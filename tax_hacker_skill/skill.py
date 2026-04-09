import os
import base64
import json
from typing import Optional, List
from openai import OpenAI, AsyncOpenAI
import asyncio
from dotenv import load_dotenv
from .models import InvoiceData
from .prompts import TAX_HACKER_SYSTEM_PROMPT, TAX_HACKER_USER_PROMPT

_EASYOCR_AVAILABLE = False
try:
    import easyocr
    _EASYOCR_AVAILABLE = True
except ImportError:
    pass

_CNOCR_AVAILABLE = False
try:
    from cnocr import CnOcr
    _CNOCR_AVAILABLE = True
except ImportError:
    pass

_PYMUPDF_AVAILABLE = False
try:
    import fitz  # PyMuPDF
    _PYMUPDF_AVAILABLE = True
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
        
        self.default_ocr_engine = os.getenv("TAX_HACKER_OCR_ENGINE", "auto").lower()
        self._easyocr_reader = None
        self._cnocr_reader = None

    def _ensure_file_exists(self, image_path: str) -> None:
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"收据文件不存在: {image_path}")

    def _resolve_ocr_engine(self, ocr_engine: Optional[str] = None) -> str:
        engine = (ocr_engine or self.default_ocr_engine or "auto").lower()
        if engine not in {"auto", "easyocr", "cnocr"}:
            raise ValueError("ocr_engine 仅支持 auto、easyocr 或 cnocr。")
        if engine == "auto":
            if _CNOCR_AVAILABLE:
                return "cnocr"
            if _EASYOCR_AVAILABLE:
                return "easyocr"
            raise ImportError("未安装本地 OCR 依赖。请安装 cnocr 或 easyocr。")
        if engine == "cnocr" and not _CNOCR_AVAILABLE:
            raise ImportError("未安装 cnocr。请运行 `pip install cnocr` 后再使用 cnocr 本地 OCR。")
        if engine == "easyocr" and not _EASYOCR_AVAILABLE:
            raise ImportError("未安装 easyocr。请运行 `pip install easyocr torch torchvision` 后再使用 easyocr 本地 OCR。")
        return engine

    def _get_easyocr_reader(self):
        if self._easyocr_reader is None:
            self._easyocr_reader = easyocr.Reader(["ch_sim", "en"])
        return self._easyocr_reader

    def _get_cnocr_reader(self):
        if self._cnocr_reader is None:
            self._cnocr_reader = CnOcr()
        return self._cnocr_reader

    def _convert_pdf_to_images(self, file_path: str) -> List[bytes]:
        """将 PDF 文件转换为图片字节列表"""
        if not _PYMUPDF_AVAILABLE:
            raise ImportError("未安装 PyMuPDF (fitz)。请运行 `pip install PyMuPDF` 以支持 PDF 文件解析。")
        doc = fitz.open(file_path)
        images = []
        for page in doc:
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 提高分辨率
            img_bytes = pix.tobytes("jpeg")
            images.append(img_bytes)
        doc.close()
        return images

    def _get_image_bytes_list(self, file_path: str) -> List[bytes]:
        """根据文件类型，获取图片字节列表（PDF 可能有多页）"""
        self._ensure_file_exists(file_path)
        if file_path.lower().endswith(".pdf"):
            return self._convert_pdf_to_images(file_path)
        else:
            with open(file_path, "rb") as f:
                return [f.read()]

    def _perform_easyocr(self, img_bytes: bytes) -> str:
        reader = self._get_easyocr_reader()
        results = reader.readtext(img_bytes, detail=0)
        return "\n".join(results)

    def _perform_cnocr(self, img_bytes: bytes) -> str:
        reader = self._get_cnocr_reader()
        results = reader.ocr(img_bytes)
        texts = []
        for item in results:
            if isinstance(item, dict):
                if "text" in item and item["text"]:
                    texts.append(str(item["text"]))
                elif "texts" in item and item["texts"]:
                    texts.extend(str(text) for text in item["texts"] if text)
            elif item:
                texts.append(str(item))
        return "\n".join(texts)

    def _perform_local_ocr(self, file_path: str, ocr_engine: Optional[str] = None) -> str:
        engine = self._resolve_ocr_engine(ocr_engine)
        img_bytes_list = self._get_image_bytes_list(file_path)
        all_texts = []
        
        for i, img_bytes in enumerate(img_bytes_list):
            if len(img_bytes_list) > 1:
                all_texts.append(f"--- 第 {i+1} 页 ---")
            if engine == "cnocr":
                all_texts.append(self._perform_cnocr(img_bytes))
            else:
                all_texts.append(self._perform_easyocr(img_bytes))
                
        return "\n".join(all_texts)

    async def _aperform_local_ocr(self, file_path: str, ocr_engine: Optional[str] = None) -> str:
        """异步版本"""
        return await asyncio.to_thread(self._perform_local_ocr, file_path, ocr_engine)

    def _encode_images(self, file_path: str) -> List[str]:
        """将文件编码为 Base64 字符串列表"""
        img_bytes_list = self._get_image_bytes_list(file_path)
        return [base64.b64encode(img_bytes).decode("utf-8") for img_bytes in img_bytes_list]

    async def _aencode_images(self, file_path: str) -> List[str]:
        """异步版本"""
        return await asyncio.to_thread(self._encode_images, file_path)

    def _is_vision_model(self, model: str) -> bool:
        """
        判断模型是否支持 Vision（视觉）能力。
        如果明确不支持，则返回 False，否则默认返回 True 以兼容未知的多模态模型。
        """
        model_lower = model.lower()
        # 常见的不支持 Vision 的纯文本模型
        non_vision_keywords = [
            "gpt-3.5", "gpt-4-turbo-preview", "gpt-4-0125-preview", "gpt-4-1106-preview",
            "claude-1", "claude-2.0", "claude-2.1", "claude-instant",
            "llama-2", "llama-3-8b", "llama-3-70b",
            "qwen-turbo", "qwen-plus", "qwen-max"
        ]
        
        # 常见的明确支持 Vision 的模型
        vision_keywords = [
            "gpt-4o", "gpt-4-vision", "claude-3", "claude-3.5",
            "gemini-1.5-pro", "gemini-1.5-flash", "qwen-vl", "llava"
        ]

        # 1. 如果明确命中不支持的列表
        for kw in non_vision_keywords:
            if kw in model_lower:
                return False
                
        # 2. 如果明确命中支持的列表
        for kw in vision_keywords:
            if kw in model_lower:
                return True
                
        # 3. 兜底策略：假设支持，让 API 自己报错或者在此之前强制使用 OCR
        return True

    def extract_receipt_data(
        self,
        image_path: str,
        model: Optional[str] = None,
        use_local_ocr: bool = False,
        ocr_engine: Optional[str] = None,
    ) -> InvoiceData:
        """
        从收据图片或 PDF 中提取结构化数据。
        
        :param image_path: 文件本地路径。
        :param model: 使用的 LLM 模型。如果未提供，则使用默认模型。
        :param use_local_ocr: 是否强制使用本地 OCR 识别。
        :param ocr_engine: OCR 引擎，可选 auto、easyocr、cnocr。
        :return: InvoiceData 对象。
        """
        model = model or self.default_model
        
        # 自动推断：如果模型不支持 Vision，则自动开启本地 OCR
        if not use_local_ocr and not self._is_vision_model(model):
            # 增加中文注释：检测到非 Vision 模型，自动启用本地 OCR
            use_local_ocr = True
            
        content_payload = []
        if use_local_ocr:
            resolved_engine = self._resolve_ocr_engine(ocr_engine)
            ocr_text = self._perform_local_ocr(image_path, resolved_engine)
            content_payload.append({
                "type": "text", 
                "text": f"{TAX_HACKER_USER_PROMPT}\n\n以下是本地 OCR 识别出的文本内容（引擎: {resolved_engine}）：\n{ocr_text}"
            })
        else:
            base64_images = self._encode_images(image_path)
            content_payload.append({"type": "text", "text": TAX_HACKER_USER_PROMPT})
            for base64_image in base64_images:
                content_payload.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                })
        
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
        
        content = response.choices[0].message.content
        if not content:
            raise ValueError("AI 返回内容为空。")
            
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            raise ValueError(f"AI 返回的 JSON 格式错误: {content}")
        
        try:
            return InvoiceData(**data)
        except Exception as e:
            raise ValueError(f"数据模型验证失败: {str(e)}")

    async def aextract_receipt_data(
        self,
        image_path: str,
        model: Optional[str] = None,
        use_local_ocr: bool = False,
        ocr_engine: Optional[str] = None,
    ) -> InvoiceData:
        """异步版本的提取函数 (适用于 FastAPI 等异步框架)"""
        model = model or self.default_model
        
        # 自动推断：如果模型不支持 Vision，则自动开启本地 OCR
        if not use_local_ocr and not self._is_vision_model(model):
            # 增加中文注释：异步检测到非 Vision 模型，自动启用本地 OCR
            use_local_ocr = True
            
        content_payload = []
        if use_local_ocr:
            resolved_engine = self._resolve_ocr_engine(ocr_engine)
            ocr_text = await self._aperform_local_ocr(image_path, resolved_engine)
            content_payload.append({
                "type": "text", 
                "text": f"{TAX_HACKER_USER_PROMPT}\n\n以下是本地 OCR 识别出的文本内容（引擎: {resolved_engine}）：\n{ocr_text}"
            })
        else:
            base64_images = await self._aencode_images(image_path)
            content_payload.append({"type": "text", "text": TAX_HACKER_USER_PROMPT})
            for base64_image in base64_images:
                content_payload.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                })
        
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
        
        content = response.choices[0].message.content
        if not content:
            raise ValueError("AI 返回内容为空。")
            
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            raise ValueError(f"AI 返回的 JSON 格式错误: {content}")
        
        try:
            return InvoiceData(**data)
        except Exception as e:
            raise ValueError(f"数据模型验证失败: {str(e)}")

def run_tax_hacker_skill(
    file_path: str,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    model: Optional[str] = None,
    use_local_ocr: bool = False,
    ocr_engine: Optional[str] = None,
) -> str:
    """
    AI Agent 调用的工具函数。
    输入: 收据文件路径 (jpg, png)。
    可选输入: api_key, base_url, model, use_local_ocr, ocr_engine。
    输出: 格式化的 JSON 字符串。
    """
    try:
        skill = TaxHackerSkill(api_key=api_key, base_url=base_url, model=model)
        result = skill.extract_receipt_data(
            file_path,
            use_local_ocr=use_local_ocr,
            ocr_engine=ocr_engine,
        )
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
    parser.add_argument("--ocr-engine", choices=["auto", "easyocr", "cnocr"], default="auto", help="本地 OCR 引擎")
    
    args = parser.parse_args()
    
    print(
        run_tax_hacker_skill(
            args.file_path,
            api_key=args.api_key,
            base_url=args.base_url,
            model=args.model,
            use_local_ocr=args.local_ocr,
            ocr_engine=args.ocr_engine,
        )
    )
