import os
import base64
import json
from typing import Optional, Union
from openai import OpenAI, AsyncOpenAI
import asyncio
from dotenv import load_dotenv
from .models import ReceiptData
from .prompts import TAX_HACKER_SYSTEM_PROMPT, TAX_HACKER_USER_PROMPT

# 延迟导入 easyocr
_EASYOCR_AVAILABLE = False
try:
    import easyocr
    _EASYOCR_AVAILABLE = True
except ImportError:
    pass

class TaxHackerSkill:
    """
    基于 TaxHacker 理念的 AI Agent 技能 (Skill)
    用于从收据/发票中自动提取结构化数据。
    支持 Vision (多模态) 和 Local OCR (本地识别) 两种模式。
    """

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None, model: Optional[str] = None):
        """
        初始化技能。
        :param api_key: OpenAI 或兼容 API 的密钥。如果未提供，则尝试从环境变量读取。
        :param base_url: API 的基础 URL。
        :param model: 默认使用的 LLM 模型。
        """
        # 自动加载当前目录或上层目录的 .env 文件
        load_dotenv()
        
        # 优先顺序: 传入参数 > OPENAI_API_KEY > OPENCLAW_LLM_API_KEY (OpenClaw 专用)
        self.api_key = api_key or os.getenv("OPENAI_API_KEY") or os.getenv("OPENCLAW_LLM_API_KEY")
        self.base_url = base_url or os.getenv("OPENAI_BASE_URL") or os.getenv("OPENCLAW_LLM_BASE_URL") or "https://api.openai.com/v1"
        self.default_model = model or os.getenv("OPENCLAW_LLM_MODEL") or "gpt-4o-mini"
        
        if not self.api_key:
            raise ValueError("未提供 API Key。请设置环境变量 (OPENAI_API_KEY 或 OPENCLAW_LLM_API_KEY) 或在初始化时传入。")
            
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        self.aclient = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)
        
        # OCR 阅读器缓存 (按需初始化)
        self._ocr_reader = None

    def _get_ocr_reader(self):
        """获取或初始化 EasyOCR Reader (支持中英文)"""
        if not _EASYOCR_AVAILABLE:
            raise ImportError("未安装 easyocr。请运行 `pip install easyocr torch torchvision` 以使用本地 OCR 功能。")
        
        if self._ocr_reader is None:
            # 增加中文注释：初始化 EasyOCR，支持简体中文和英文
            self._ocr_reader = easyocr.Reader(['ch_sim', 'en'])
        return self._ocr_reader

    def _perform_local_ocr(self, image_path: str) -> str:
        """执行本地 OCR 识别并返回合并后的文本"""
        reader = self._get_ocr_reader()
        # detail=0 表示只返回识别出的文本列表
        results = reader.readtext(image_path, detail=0)
        return "\n".join(results)

    async def _aperform_local_ocr(self, image_path: str) -> str:
        """异步执行本地 OCR 识别"""
        return await asyncio.to_thread(self._perform_local_ocr, image_path)

    def _encode_image(self, image_path: str) -> str:
        """将图片文件编码为 Base64 字符串"""
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"收据文件不存在: {image_path}")
            
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")

    async def _aencode_image(self, image_path: str) -> str:
        """异步版本的图片编码 (使用 asyncio.to_thread 避免阻塞事件循环)"""
        return await asyncio.to_thread(self._encode_image, image_path)

    def extract_receipt_data(self, image_path: str, model: Optional[str] = None, use_local_ocr: bool = False) -> ReceiptData:
        """
        从收据图片中提取结构化数据。
        
        :param image_path: 图片文件的本地路径。
        :param model: 使用的 LLM 模型。如果未提供，则使用默认模型。
        :param use_local_ocr: 是否使用本地 OCR 识别。如果为 True，则优先使用本地识别的文本。
        :return: ReceiptData 对象。
        """
        # 1. 获取内容 (图片或 OCR 文本)
        content_payload = []
        if use_local_ocr:
            # 增加中文注释：使用本地 OCR 提取文本，避免上传大图或用于非 Vision 模型
            ocr_text = self._perform_local_ocr(image_path)
            content_payload.append({
                "type": "text", 
                "text": f"{TAX_HACKER_USER_PROMPT}\n\n以下是本地 OCR 识别出的文本内容：\n{ocr_text}"
            })
        else:
            # 默认 Vision 模式：编码图片 (内部会检查文件是否存在)
            base64_image = self._encode_image(image_path)
            content_payload.append({"type": "text", "text": TAX_HACKER_USER_PROMPT})
            content_payload.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
            })
        
        # 2. 调用 LLM
        model = model or self.default_model
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
                        "content": content_payload
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

    async def aextract_receipt_data(self, image_path: str, model: Optional[str] = None, use_local_ocr: bool = False) -> ReceiptData:
        """异步版本的提取函数 (适用于 FastAPI 等异步框架)"""
        # 1. 获取内容 (使用异步方式)
        content_payload = []
        if use_local_ocr:
            # 增加中文注释：异步执行本地 OCR
            ocr_text = await self._aperform_local_ocr(image_path)
            content_payload.append({
                "type": "text", 
                "text": f"{TAX_HACKER_USER_PROMPT}\n\n以下是本地 OCR 识别出的文本内容：\n{ocr_text}"
            })
        else:
            # 异步 Vision 模式
            base64_image = await self._aencode_image(image_path)
            content_payload.append({"type": "text", "text": TAX_HACKER_USER_PROMPT})
            content_payload.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
            })
        
        # 2. 调用 LLM (使用 AsyncOpenAI)
        model = model or self.default_model
        try:
            response = await self.aclient.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": TAX_HACKER_SYSTEM_PROMPT
                    },
                    {
                        "role": "user",
                        "content": content_payload
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

# 简易调用接口 (供 Agent 框架使用)
def run_tax_hacker_skill(file_path: str, api_key: Optional[str] = None, base_url: Optional[str] = None, model: Optional[str] = None, use_local_ocr: bool = False) -> str:
    """
    AI Agent 调用的工具函数。
    输入: 收据文件路径 (jpg, png)。
    可选输入: api_key, base_url, model, use_local_ocr。
    输出: 格式化的 JSON 字符串。
    """
    try:
        skill = TaxHackerSkill(api_key=api_key, base_url=base_url, model=model)
        result = skill.extract_receipt_data(file_path, use_local_ocr=use_local_ocr)
        return result.model_dump_json(indent=2, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Tax Hacker Receipt Extraction Skill")
    parser.add_argument("file_path", help="收据文件路径 (jpg, png)")
    parser.add_argument("--api-key", help="API Key (可选，默认使用环境变量)")
    parser.add_argument("--base-url", help="API Base URL (可选，默认使用环境变量)")
    parser.add_argument("--model", help="LLM 模型 (可选，默认使用 gpt-4o-mini)")
    parser.add_argument("--local-ocr", action="store_true", help="使用本地 OCR 识别文本（不上传图片，更节省 Token）")
    
    args = parser.parse_args()
    
    # 确保可以从包外部调用
    print(run_tax_hacker_skill(args.file_path, api_key=args.api_key, base_url=args.base_url, model=args.model, use_local_ocr=args.local_ocr))
