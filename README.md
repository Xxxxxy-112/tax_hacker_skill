<!--
 * @Author: 嘛的叭卡 xxxxxy_112@163.com
 * @Date: 2026-04-08 15:48:37
 * @LastEditors: 嘛的叭卡 xxxxxy_112@163.com
 * @LastEditTime: 2026-04-08 15:59:26
 * @FilePath: \skill\README.md
 * @Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
-->
# TaxHacker AI Agent Skill

这是一个基于 [TaxHacker](https://taxhacker.app/) 理念制作的 AI Agent 技能（Skill）。它利用多模态大语言模型（如 GPT-4o-mini）自动解析收据、发票、账单图片，并提取结构化的财务数据，方便后续的记账、报税和风险评估。

## ✨ 主要功能

- **自动化 OCR 提取**：无需手动输入，AI 自动识别商家、金额、日期、货币等关键信息。
- **智能分类**：根据消费内容自动推断交易类别（如餐饮、办公用品、交通等）。
- **商品明细解析**：支持提取收据中的每一项商品及其单价、数量。
- **风险评估**：AI 自动对收据的规范性和金额异常进行初步审计，标记风险等级。
- **结构化输出**：基于 Pydantic 的严谨数据模型，确保与下游系统无缝集成。

## 📂 项目结构

```text
.
├── __init__.py          # 包导出接口
├── models.py            # Pydantic 数据模型定义
├── prompts.py           # 优化的 AI 提示词模板
├── skill.py             # 核心逻辑类 TaxHackerSkill
├── requirements.txt     # 项目依赖列表
└── example.py           # 快速入门使用示例
```

## 🚀 快速开始

### 1. 安装依赖

确保您的 Python 环境版本 >= 3.9。

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

在项目根目录下创建 `.env` 文件，或者直接在终端设置：

```bash
# 必填：您的 OpenAI 或兼容平台的 API Key
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxx

# 可选：如果您使用的是代理或第三方平台（如 DeepSeek, 智谱 AI）
# OPENAI_BASE_URL=https://api.openai.com/v1
```

### 3. 基本用法

```python
from skill import TaxHackerSkill
```,old_str:python
from tax_hacker_skill import TaxHackerSkill

# 初始化技能
skill = TaxHackerSkill()

# 提取收据数据 (支持 jpg, png, webp 等图片格式)
try:
    data = skill.extract_receipt_data("path/to/your/receipt.jpg")
    
    print(f"商家: {data.vendor}")
    print(f"总额: {data.total_amount} {data.currency}")
    print(f"分类: {data.category}")
    print(f"摘要: {data.summary}")
except Exception as e:
    print(f"解析出错: {e}")
```

## 🤖 在 OpenClaw 中使用

本 Skill 已适配 **OpenClaw** AI Agent 框架。

### 1. 安装方法
将项目文件夹复制到 OpenClaw 的技能目录中：
- 个人全局目录：`~/.openclaw/skills/tax_hacker_skill`
- 工作区目录：`<your-workspace>/skills/tax_hacker_skill`

### 2. 依赖安装
在 OpenClaw 运行的环境中安装必要的依赖：
```bash
pip install -r requirements.txt
```

### 3. 配置
确保已设置环境变量 `OPENAI_API_KEY`。OpenClaw 在启动时会自动扫描 `SKILL.md` 并将其注册为可用技能。

---
## 🛠️ 数据模型说明

系统返回的 `ReceiptData` 对象包含以下关键字段：

| 字段名 | 类型 | 说明 |
| :--- | :--- | :--- |
| `vendor` | string | 商家或收款人名称 |
| `date` | string | 交易日期 (YYYY-MM-DD) |
| `total_amount` | float | 交易总金额 |
| `currency` | string | 货币符号 (如 CNY, USD) |
| `items` | list | 商品明细列表 (name, price, quantity) |
| `category` | string | 自动分类结果 |
| `risk_level` | string | 风险等级 (low, medium, high) |

## 💡 提示与建议

1. **模型选择**：建议使用 `gpt-4o-mini`（高性价比）或 `gpt-4o`（更高精度）。本技能支持任何具备 Vision（视觉能力）且兼容 OpenAI 格式的模型。
2. **图片质量**：虽然 AI 对模糊或倾斜的收据有很强的容错性，但清晰的光线和垂直拍摄能显著提高识别准确率。
3. **隐私说明**：本工具会将图片数据发送至配置的 AI 服务商。如果处理极敏感数据，建议使用本地部署的 LLM（如通过 Ollama 运行的 Llama-3-Vision）。

---
*Inspired by TaxHacker - Let AI handle your taxes.*
