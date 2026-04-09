import unittest
from unittest.mock import MagicMock, patch, AsyncMock
import json
import os
from tax_hacker_skill.skill import TaxHackerSkill, run_tax_hacker_skill
from tax_hacker_skill.models import InvoiceData

class TestTaxHackerSkill(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        os.environ["OPENAI_API_KEY"] = "test-key"

    @patch('tax_hacker_skill.skill.OpenAI')
    @patch('tax_hacker_skill.skill.load_dotenv')
    def test_init_no_api_key(self, mock_dotenv, mock_openai):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError):
                TaxHackerSkill()

    @patch('tax_hacker_skill.skill.OpenAI')
    @patch('tax_hacker_skill.skill.load_dotenv')
    @patch('tax_hacker_skill.skill.os.path.exists')
    @patch('builtins.open', unittest.mock.mock_open(read_data=b"fake-image-data"))
    def test_extract_receipt_data_success(self, mock_exists, mock_dotenv, mock_openai):
        mock_exists.return_value = True
        skill = TaxHackerSkill()
        
        # 模拟 OpenAI 的响应
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content=json.dumps({
                "invoice_code": "011002200111",
                "invoice_number": "12345678",
                "date": "2024-01-01",
                "amount": 100.0,
                "tax_amount": 13.0,
                "check_code": "123456",
                "vendor": "Test Store",
                "purchaser": "Buy Corp",
                "currency": "CNY",
                "items": [{"name": "Item 1", "price": 100.0, "quantity": 1}],
                "category": "Office",
                "summary": "Office supplies",
                "risk_level": "low"
            })))
        ]
        skill.client.chat.completions.create.return_value = mock_response
        
        result = skill.extract_receipt_data("fake_path.jpg")
        
        self.assertIsInstance(result, InvoiceData)
        self.assertEqual(result.vendor, "Test Store")
        self.assertEqual(result.invoice_code, "011002200111")
        self.assertEqual(result.amount, 100.0)

    @patch('tax_hacker_skill.skill.os.path.exists')
    @patch('tax_hacker_skill.skill.load_dotenv')
    @patch('tax_hacker_skill.skill.OpenAI')
    def test_extract_receipt_data_file_not_found(self, mock_openai, mock_dotenv, mock_exists):
        mock_exists.return_value = False
        skill = TaxHackerSkill()
        with self.assertRaises(FileNotFoundError):
            skill.extract_receipt_data("non_existent.jpg")

    @patch('tax_hacker_skill.skill.OpenAI')
    @patch('tax_hacker_skill.skill.load_dotenv')
    @patch('tax_hacker_skill.skill.os.path.exists')
    @patch('builtins.open', unittest.mock.mock_open(read_data=b"fake-image-data"))
    def test_run_tax_hacker_skill_success(self, mock_exists, mock_dotenv, mock_openai):
        mock_exists.return_value = True
        
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content=json.dumps({
                "vendor": "Test Store",
                "amount": 100.0,
                "currency": "CNY",
                "items": [],
                "summary": "Test"
            })))
        ]
        # 创建一个模拟客户端实例，并让 OpenAI 类返回它
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        output = run_tax_hacker_skill("fake_path.jpg")
        data = json.loads(output)
        self.assertEqual(data["vendor"], "Test Store")

    @patch('tax_hacker_skill.skill.os.path.exists')
    @patch('tax_hacker_skill.skill.load_dotenv')
    def test_run_tax_hacker_skill_error(self, mock_dotenv, mock_exists):
        mock_exists.return_value = False
        output = run_tax_hacker_skill("non_existent.jpg")
        data = json.loads(output)
        self.assertIn("error", data)
        self.assertIn("收据文件不存在", data["error"])

    @patch('tax_hacker_skill.skill._EASYOCR_AVAILABLE', True)
    @patch('tax_hacker_skill.skill.os.path.exists')
    @patch('tax_hacker_skill.skill.load_dotenv')
    @patch('tax_hacker_skill.skill.OpenAI')
    @patch('tax_hacker_skill.skill.TaxHackerSkill._perform_local_ocr')
    def test_extract_receipt_data_local_ocr(self, mock_ocr, mock_openai, mock_dotenv, mock_exists):
        mock_exists.return_value = True
        mock_ocr.return_value = "Test Store\n2024-01-01\n100.0\nCNY"
        
        skill = TaxHackerSkill()
        
        # 模拟 OpenAI 响应
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content=json.dumps({
                "vendor": "Test Store",
                "amount": 100.0,
                "currency": "CNY",
                "items": [],
                "summary": "OCR Result"
            })))
        ]
        skill.client.chat.completions.create.return_value = mock_response
        
        result = skill.extract_receipt_data("fake_path.jpg", use_local_ocr=True, ocr_engine="easyocr")
        
        self.assertEqual(result.vendor, "Test Store")
        mock_ocr.assert_called_once_with("fake_path.jpg", "easyocr")
        args, kwargs = skill.client.chat.completions.create.call_args
        messages = kwargs['messages']
        user_content = messages[1]['content']
        self.assertEqual(user_content[0]['type'], 'text')
        self.assertIn("OCR 识别出的文本内容", user_content[0]['text'])
        self.assertIn("引擎: easyocr", user_content[0]['text'])

    @patch('tax_hacker_skill.skill._CNOCR_AVAILABLE', True)
    @patch('tax_hacker_skill.skill.os.path.exists')
    @patch('tax_hacker_skill.skill.load_dotenv')
    @patch('tax_hacker_skill.skill.OpenAI')
    @patch('tax_hacker_skill.skill.TaxHackerSkill._perform_local_ocr')
    def test_extract_receipt_data_cnocr(self, mock_ocr, mock_openai, mock_dotenv, mock_exists):
        mock_exists.return_value = True
        mock_ocr.return_value = "测试商户\n100.0\nCNY"

        skill = TaxHackerSkill()

        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content=json.dumps({
                "vendor": "测试商户",
                "amount": 100.0,
                "currency": "CNY",
                "items": [],
                "summary": "CnOCR Result"
            })))
        ]
        skill.client.chat.completions.create.return_value = mock_response

        result = skill.extract_receipt_data("fake_path.jpg", use_local_ocr=True, ocr_engine="cnocr")

        self.assertEqual(result.vendor, "测试商户")
        mock_ocr.assert_called_once_with("fake_path.jpg", "cnocr")
        _, kwargs = skill.client.chat.completions.create.call_args
        user_content = kwargs['messages'][1]['content']
        self.assertIn("引擎: cnocr", user_content[0]['text'])

    @patch('tax_hacker_skill.skill._EASYOCR_AVAILABLE', True)
    @patch('tax_hacker_skill.skill.os.path.exists')
    @patch('tax_hacker_skill.skill.load_dotenv')
    @patch('tax_hacker_skill.skill.AsyncOpenAI')
    @patch('tax_hacker_skill.skill.TaxHackerSkill._aperform_local_ocr')
    async def test_aextract_receipt_data_local_ocr(self, mock_aocr, mock_aopenai, mock_dotenv, mock_exists):
        mock_exists.return_value = True
        mock_aocr.return_value = "Test Store\n2024-01-01\n100.0\nCNY"
        
        skill = TaxHackerSkill()
        
        # 模拟 AsyncOpenAI 响应
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content=json.dumps({
                "vendor": "Test Store",
                "amount": 100.0,
                "currency": "CNY",
                "items": [],
                "summary": "OCR Result"
            })))
        ]
        # 注意: AsyncOpenAI 的 create 方法是异步的
        skill.aclient.chat.completions.create = AsyncMock(return_value=mock_response)
        
        result = await skill.aextract_receipt_data("fake_path.jpg", use_local_ocr=True, ocr_engine="easyocr")
        
        self.assertEqual(result.vendor, "Test Store")
        mock_aocr.assert_called_once_with("fake_path.jpg", "easyocr")

    @patch('tax_hacker_skill.skill._CNOCR_AVAILABLE', True)
    @patch('tax_hacker_skill.skill.os.path.exists')
    @patch('tax_hacker_skill.skill.load_dotenv')
    @patch('tax_hacker_skill.skill.OpenAI')
    @patch('tax_hacker_skill.skill.TaxHackerSkill._perform_local_ocr')
    def test_extract_receipt_data_auto_fallback(self, mock_ocr, mock_openai, mock_dotenv, mock_exists):
        """测试使用不支持 vision 的模型时，自动启用本地 OCR（默认 cnocr）"""
        mock_exists.return_value = True
        mock_ocr.return_value = "Fallback Store\n2024-01-01\n100.0\nCNY"

        skill = TaxHackerSkill()

        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content=json.dumps({
                "vendor": "Fallback Store",
                "amount": 100.0,
                "currency": "CNY",
                "items": [],
                "summary": "CnOCR Result"
            })))
        ]
        skill.client.chat.completions.create.return_value = mock_response

        # use_local_ocr=False, model="gpt-3.5-turbo" -> 应该自动触发本地 OCR
        result = skill.extract_receipt_data("fake_path.jpg", model="gpt-3.5-turbo", use_local_ocr=False)

        self.assertEqual(result.vendor, "Fallback Store")
        mock_ocr.assert_called_once_with("fake_path.jpg", "cnocr")
        _, kwargs = skill.client.chat.completions.create.call_args
        user_content = kwargs['messages'][1]['content']
        self.assertIn("引擎: cnocr", user_content[0]['text'])

    @patch('tax_hacker_skill.skill.os.path.exists')
    @patch('tax_hacker_skill.skill.load_dotenv')
    @patch('tax_hacker_skill.skill.OpenAI')
    @patch('tax_hacker_skill.skill.TaxHackerSkill._convert_pdf_to_images')
    def test_extract_receipt_data_pdf(self, mock_convert_pdf, mock_openai, mock_dotenv, mock_exists):
        mock_exists.return_value = True
        mock_convert_pdf.return_value = [b"fake-pdf-image-bytes-1", b"fake-pdf-image-bytes-2"]

        skill = TaxHackerSkill()

        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content=json.dumps({
                "invoice_code": "PDF001",
                "invoice_number": "123456",
                "date": "2024-01-01",
                "amount": 200.0,
                "vendor": "PDF Store",
                "currency": "CNY",
                "items": [],
                "summary": "PDF Result"
            })))
        ]
        skill.client.chat.completions.create.return_value = mock_response

        result = skill.extract_receipt_data("fake_path.pdf", use_local_ocr=False)

        self.assertEqual(result.vendor, "PDF Store")
        self.assertEqual(result.amount, 200.0)
        
        args, kwargs = skill.client.chat.completions.create.call_args
        messages = kwargs['messages']
        user_content = messages[1]['content']
        # 1 text + 2 images
        self.assertEqual(len(user_content), 3)
        self.assertEqual(user_content[1]['type'], 'image_url')
        self.assertEqual(user_content[2]['type'], 'image_url')

    @patch('tax_hacker_skill.skill.os.path.exists')
    @patch('tax_hacker_skill.skill.load_dotenv')
    @patch('tax_hacker_skill.skill.OpenAI')
    @patch('builtins.open', unittest.mock.mock_open(read_data=b"fake-image-data"))
    def test_extract_invoice_blurry_or_error(self, mock_openai, mock_dotenv, mock_exists):
        """集成测试用例：覆盖错票或模糊图片场景"""
        mock_exists.return_value = True
        skill = TaxHackerSkill()
        
        # 模拟 OpenAI 返回错票/模糊发票
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content=json.dumps({
                "invoice_code": None,
                "invoice_number": None,
                "date": None,
                "amount": 0.0,
                "tax_amount": None,
                "check_code": None,
                "vendor": None,
                "purchaser": None,
                "currency": "CNY",
                "items": [],
                "category": None,
                "summary": "图片模糊不清，无法识别发票代码和金额。",
                "risk_level": "high"
            })))
        ]
        skill.client.chat.completions.create.return_value = mock_response
        
        result = skill.extract_receipt_data("blurry_invoice.jpg")
        
        self.assertEqual(result.risk_level, "high")
        self.assertIn("模糊不清", result.summary)
        self.assertEqual(result.amount, 0.0)

if __name__ == '__main__':
    unittest.main()
