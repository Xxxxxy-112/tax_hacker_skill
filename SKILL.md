# TaxHacker Receipt Analysis Skill

Extract structured financial data from receipt/invoice images using AI.

## Description
This skill analyzes images of receipts, invoices, or bills to extract key accounting information including vendor name, date, total amount, currency, tax, and itemized lists. It also provides an AI-based risk assessment and categorization.

## Configuration (OpenClaw)
This skill is optimized for OpenClaw. If you have configured a model in OpenClaw, the skill can automatically use its settings.
- If `OPENCLAW_LLM_API_KEY` is set in the environment, the skill will use it.
- If `OPENCLAW_LLM_BASE_URL` is set, the skill will use it.
- If `OPENCLAW_LLM_MODEL` is set, the skill will use it (e.g., `gpt-4o`, `gpt-4o-mini`).

Otherwise, you can provide parameters directly via CLI:
```bash
# Vision Mode (Default)
python -m tax_hacker_skill.skill "<file_path>" --api-key "YOUR_KEY" --model "gpt-4o-mini"

# Local OCR Mode (Saves tokens, no image upload)
python -m tax_hacker_skill.skill "<file_path>" --local-ocr

# Local OCR Mode with CnOCR
python -m tax_hacker_skill.skill "<file_path>" --local-ocr --ocr-engine cnocr
```

## Parameters
- `file_path`: (Required) Absolute path to the receipt image file (jpg, png, webp).
- `--api-key`: (Optional) Override API Key.
- `--base-url`: (Optional) Override API Base URL.
- `--model`: (Optional) Override LLM Model.
- `--local-ocr`: (Optional) Use local OCR instead of vision.
- `--ocr-engine`: (Optional) OCR engine: `auto`, `easyocr`, `cnocr`.

## Instructions
1. Ensure the user has provided an image file path.
2. Execute the following command to process the receipt:
   ```bash
   python -m tax_hacker_skill.skill "<file_path>"
   ```
3. The command will output a JSON object containing the extracted data.
4. Use the output to update accounting records, generate reports, or answer user queries about their expenses.

## Example Usage
"Analyze the receipt at C:/Users/Docs/receipt_123.jpg and tell me the total amount."
-> Run: `python -m tax_hacker_skill.skill "C:/Users/Docs/receipt_123.jpg"`
