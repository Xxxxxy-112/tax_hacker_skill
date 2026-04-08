import os
import base64
import json
from typing import Optional, Union
from openai import OpenAI
from dotenv import load_dotenv
from .models import ReceiptData
from .prompts import TAX_HACKER_SYSTEM_PROMPT, TAX_HACKER_USER_PROMPT

class TaxHackerSkill:
    """
    基于 TaxHacker 理念的 AI Agent 技能 (Skill)
    用于从收据/发票中自动提取结构化数据。
    """

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """
        初始化技能。
        :param api_key: OpenAI 或兼容 API 的密钥。如果未提供，则从环境变量 OPENAI_API_KEY 读取。
        :param base_url: API 的基础 URL。
        """
        # 自动加载当前目录或上层目录的 .env 文件
        load_dotenv()
        
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.base_url = base_url or os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        
        if not self.api_key:
            raise ValueError("未提供 API Key。请设置环境变量 OPENAI_API_KEY 或在初始化时传入。")
            
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    def _encode_image(self, image_path: str) -> str:
        """将图片文件编码为 Base64 字符串"""
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"收据文件不存在: {image_path}")
            
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")

    def extract_receipt_data(self, image_path: str, model: str = "gpt-4o-mini") -> ReceiptData:
        """
        从收据图片中提取结构化数据。
        
        :param image_path: 图片文件的本地路径。
        :param model: 使用的 LLM 模型 (建议使用具备多模态能力的模型，如 gpt-4o, gpt-4o-mini)。
        :return: ReceiptData 对象 (包含商家、日期、金额、明细等)。
        """
        # 1. 编码图片 (内部会检查文件是否存在)
        base64_image = self._encode_image(image_path)
        
        # 2. 调用 LLM
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": TAX_HACKER_SYSTEM_PROMPT
                    },
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": TAX_HACKER_USER_PROMPT},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                response_format={"type": "json_object"}
            )
        except Exception as e:
            raise RuntimeError(f"调用 AI 服务失败: {str(e)}")
        
        # 3. 解析结果
        content = response.choices[0].message.content
        if not content:
            raise ValueError("AI 返回内容为空。")
            
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            raise ValueError(f"AI 返回的 JSON 格式错误: {content}")
        
        # 4. 验证并返回 Pydantic 模型
        try:
            return ReceiptData(**data)
        except Exception as e:
            raise ValueError(f"数据模型验证失败: {str(e)}")

    async def aextract_receipt_data(self, image_path: str, model: str = "gpt-4o-mini") -> ReceiptData:
        """异步版本的提取函数 (适用于 FastAPI 等异步框架)"""
        # 这里为了演示，简单复用同步调用，实际生产中可使用 AsyncOpenAI
        return self.extract_receipt_data(image_path, model)

# 简易调用接口 (供 Agent 框架使用)
def run_tax_hacker_skill(file_path: str) -> str:
    """
    AI Agent 调用的工具函数。
    输入: 收据文件路径 (jpg, png)。
    输出: 格式化的 JSON 字符串。
    """
    try:
        skill = TaxHackerSkill()
        result = skill.extract_receipt_data(file_path)
        return result.model_dump_json(indent=2, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print(json.dumps({"error": "请输入文件路径。用法: python -m tax_hacker_skill.skill <path_to_receipt>"}, ensure_ascii=False))
        sys.exit(1)
    
    # 确保可以从包外部调用
    file_path = sys.argv[1]
    print(run_tax_hacker_skill(file_path))
