# TaxHacker Receipt Analysis Skill

Extract structured financial data from receipt/invoice images using AI.

## Description
This skill analyzes images of receipts, invoices, or bills to extract key accounting information including vendor name, date, total amount, currency, tax, and itemized lists. It also provides an AI-based risk assessment and categorization.

## Parameters
- `file_path`: (Required) Absolute path to the receipt image file (jpg, png, webp).

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
