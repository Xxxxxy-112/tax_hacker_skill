import unittest
from unittest.mock import MagicMock, patch
import json
import os
from skill import TaxHackerSkill, run_tax_hacker_skill
from models import ReceiptData

class TestTaxHackerSkill(unittest.TestCase):

    def setUp(self):
        os.environ["OPENAI_API_KEY"] = "test-key"

    @patch('skill.OpenAI')
    @patch('skill.load_dotenv')
    def test_init_no_api_key(self, mock_dotenv, mock_openai):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError):
                TaxHackerSkill()

    @patch('skill.OpenAI')
    @patch('skill.load_dotenv')
    @patch('skill.os.path.exists')
    @patch('builtins.open', unittest.mock.mock_open(read_data=b"fake-image-data"))
    def test_extract_receipt_data_success(self, mock_exists, mock_dotenv, mock_openai):
        mock_exists.return_value = True
        skill = TaxHackerSkill()
        
        # 模拟 OpenAI 的响应
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content=json.dumps({
                "vendor": "Test Store",
                "date": "2024-01-01",
                "total_amount": 100.0,
                "currency": "CNY",
                "items": [{"name": "Item 1", "price": 100.0, "quantity": 1}],
                "category": "Office",
                "summary": "Office supplies",
                "risk_level": "low"
            })))
        ]
        skill.client.chat.completions.create.return_value = mock_response
        
        result = skill.extract_receipt_data("fake_path.jpg")
        
        self.assertIsInstance(result, ReceiptData)
        self.assertEqual(result.vendor, "Test Store")

    @patch('skill.os.path.exists')
    @patch('skill.load_dotenv')
    @patch('skill.OpenAI')
    def test_extract_receipt_data_file_not_found(self, mock_openai, mock_dotenv, mock_exists):
        mock_exists.return_value = False
        skill = TaxHackerSkill()
        with self.assertRaises(FileNotFoundError):
            skill.extract_receipt_data("non_existent.jpg")

    @patch('skill.OpenAI')
    @patch('skill.load_dotenv')
    @patch('skill.os.path.exists')
    @patch('builtins.open', unittest.mock.mock_open(read_data=b"fake-image-data"))
    def test_run_tax_hacker_skill_success(self, mock_exists, mock_dotenv, mock_openai):
        mock_exists.return_value = True
        
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content=json.dumps({
                "vendor": "Test Store",
                "total_amount": 100.0,
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

    @patch('skill.os.path.exists')
    @patch('skill.load_dotenv')
    def test_run_tax_hacker_skill_error(self, mock_dotenv, mock_exists):
        mock_exists.return_value = False
        output = run_tax_hacker_skill("non_existent.jpg")
        data = json.loads(output)
        self.assertIn("error", data)
        self.assertIn("收据文件不存在", data["error"])

if __name__ == '__main__':
    unittest.main()
