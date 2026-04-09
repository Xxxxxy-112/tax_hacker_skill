<!--
 * @Author: 嘛的叭卡 xxxxxy_112@163.com
 * @Date: 2026-04-08 15:48:37
 * @LastEditors: 嘛的叭卡 xxxxxy_112@163.com
 * @LastEditTime: 2026-04-08 16:39:36
 * @FilePath: \skill\README.md
 * @Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
-->
# TaxHacker AI Agent Skill

这是一个基于 [TaxHacker](https://taxhacker.app/) 理念制作的通用 AI Agent 技能（Skill），并已深度适配 **OpenClaw** 框架。它利用大语言模型自动解析收据、发票、账单图片及 PDF 文件，提取出结构化的财务数据，方便后续的记账、报税和风险评估。

## ✨ 主要功能

- **多格式支持**：全面支持 JPG, PNG, WEBP 等图片格式，以及 **单页/多页 PDF** 发票文件的智能拆分和提取。
- **通用发票字段解析**：不仅支持提取商家、日期、总金额，还支持提取 **发票代码、发票号码、税额、校验码、购方/销方名称** 等国内/国际通用发票字段。
- **双模态提取架构**：
  - **Vision 模式**：原生支持 GPT-4o, Claude 3.5 等多模态视觉模型直接读图。
  - **Local OCR 模式**：内置支持 **CnOCR** 和 **EasyOCR**，当使用不支持视觉的纯文本模型（如 GPT-3.5, Llama 3）时，**系统会自动降级**，在本地完成图片文字识别后再交由大模型解析，省时且节约 Token。
- **错票与模糊处理**：自动评估收据规范性，发现金额不符、模糊不清、错票时，会自动提高风险等级并备注原因。
- **结构化输出**：基于 Pydantic 的严谨数据模型 (`InvoiceData`)，与下游系统无缝集成。

## 📂 项目结构

```text
tax_hacker_skill/
├── __init__.py          # 包导出接口
├── models.py            # Pydantic 数据模型定义
├── prompts.py           # 优化的 AI 提示词模板
├── skill.py             # 核心逻辑类 TaxHackerSkill
└── requirements.txt     # 项目依赖列表
example.py               # 快速入门使用示例
test_skill.py            # 单元测试
```

## 🚀 快速开始

### 1. 安装依赖

确保您的 Python 环境版本 >= 3.9。

```bash
pip install -r tax_hacker_skill/requirements.txt
```

### 2. 配置环境变量

在项目根目录下创建 `.env` 文件，或者直接在终端设置：

```bash
# 方式 A: 标准 OpenAI 变量
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxx
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL_NAME=gpt-4o-mini

# 方式 B: OpenClaw 框架自动适配 (推荐)
# 如果您在 OpenClaw 中使用，可以设置以下变量，Skill 会自动读取：
OPENCLAW_LLM_API_KEY=sk-xxxxxxxxxxxxxxxxxxxx
OPENCLAW_LLM_BASE_URL=https://api.openai.com/v1
OPENCLAW_LLM_MODEL=gpt-4o-mini
```

### 3. 基本用法

#### 🐍 Python 调用

```python
from tax_hacker_skill import TaxHackerSkill

# 初始化技能 (会自动读取环境变量)
skill = TaxHackerSkill()

# 提取发票数据 (支持 jpg, png, pdf 等格式)
try:
    data = skill.extract_receipt_data("path/to/your/invoice.pdf")
    
    print(f"发票号码: {data.invoice_number}")
    print(f"商家: {data.vendor}")
    print(f"总额: {data.amount} {data.currency}")
    print(f"摘要: {data.summary}")
except Exception as e:
    print(f"解析出错: {e}")
```

#### 💻 命令行 (CLI) 调用

```bash
# 基本用法 (默认 Vision 模式)
python -m tax_hacker_skill.skill "path/to/invoice.jpg"

# 强制使用本地 OCR 模式 (不上传图片)
python -m tax_hacker_skill.skill "path/to/invoice.jpg" --local-ocr

# 强制使用本地 OCR 并指定引擎为 CnOCR
python -m tax_hacker_skill.skill "path/to/invoice.jpg" --local-ocr --ocr-engine cnocr

# 传入纯文本大模型（自动降级为 OCR 模式）
python -m tax_hacker_skill.skill "path/to/invoice.pdf" --model "gpt-3.5-turbo"
```

## 🤖 在 OpenClaw 中集成

本 Skill 已深度适配 **OpenClaw** AI Agent 框架。

### 1. 无需手动配置 API Key
如果您的 OpenClaw 已经配置了模型（环境变量中包含 `OPENCLAW_LLM_API_KEY` 等），本 Skill 在安装后会**自动继承**这些配置，无需您再次手动填写 `.env` 或 `api_key`。

### 2. 安装方法
将 `tax_hacker_skill` 文件夹及 `manifest.yaml` 复制到 OpenClaw 的技能目录中：
- 个人全局目录：`~/.openclaw/skills/tax_hacker_skill`
- 工作区目录：`<your-workspace>/skills/tax_hacker_skill`

### 3. 依赖安装
在 OpenClaw 运行的环境中安装必要的依赖：
```bash
pip install -r tax_hacker_skill/requirements.txt
```

### 4. 一键验证与注册
项目提供了验证脚本，确保在您的环境中该 Skill 能被顺利调用：
```bash
python verify.py
```
若验证通过，OpenClaw 在启动时会自动扫描 `manifest.yaml` 并将其注册为可用技能。您可以直接在 OpenClaw 界面或对话中调用。

---
## 🛠️ 数据模型说明

系统返回的 `InvoiceData` 对象包含以下关键字段：

| 字段名 | 类型 | 说明 |
| :--- | :--- | :--- |
| `invoice_code` | string | 发票代码 |
| `invoice_number` | string | 发票号码 |
| `date` | string | 开票日期/交易日期 (YYYY-MM-DD) |
| `amount` | float | 交易总金额/价税合计金额 |
| `tax_amount` | float | 税额 |
| `check_code` | string | 校验码(通常为后6位或全位) |
| `vendor` | string | 销方/商家名称 |
| `purchaser` | string | 购方名称 |
| `currency` | string | 货币符号或代码 (如 CNY, USD) |
| `items` | list | 商品明细列表 (name, price, quantity) |
| `category` | string | 自动分类结果 |
| `summary` | string | 交易摘要/内容简述 (错票/模糊原因说明) |
| `risk_level` | string | 风险等级 (low, medium, high) |

## 💡 提示与建议

1. **模型选择**：建议使用 `gpt-4o-mini`（高性价比）或 `gpt-4o`（更高精度）。本技能支持任何具备 Vision（视觉能力）且兼容 OpenAI 格式的模型。
2. **图片质量**：虽然 AI 对模糊或倾斜的收据有很强的容错性，但清晰的光线和垂直拍摄能显著提高识别准确率。
3. **隐私说明**：本工具会将图片数据发送至配置的 AI 服务商。如果处理极敏感数据，建议使用本地部署的 LLM（如通过 Ollama 运行的 Llama-3-Vision）。

---
*Inspired by TaxHacker - Let AI handle your taxes.*
