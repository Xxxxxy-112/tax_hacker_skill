import os
from dotenv import load_dotenv
from tax_hacker_skill import TaxHackerSkill

# 加载 .env 环境变量 (可选，建议手动设置或在 shell 环境中配置)
load_dotenv()

def main():
    # 1. 确保已设置 OPENAI_API_KEY (或在初始化时传入)
    if "OPENAI_API_KEY" not in os.environ:
        print("请先设置 OPENAI_API_KEY 环境变量。")
        return

    # 2. 初始化 TaxHacker 技能
    # api_key = "sk-..." 
    # base_url = "https://..."
    skill = TaxHackerSkill()

    # 3. 指定要处理的收据图片路径
    # 这里为了演示，假设当前目录下有一个 invoice_sample.jpg 或 pdf。
    # 您需要根据实际情况替换为有效的文件路径。
    receipt_image = "invoice_sample.jpg" 

    if not os.path.exists(receipt_image):
        print(f"找不到文件: {receipt_image}。请提供一个真实的图片或PDF进行测试。")
        return

    try:
        # 4. 调用核心提取逻辑 (使用 gpt-4o-mini 以平衡速度与成本)
        print(f"正在分析 {receipt_image} (Vision 模式)...")
        data = skill.extract_receipt_data(receipt_image, model="gpt-4o-mini")

        # 5. 打印结果
        print("\n=== Vision 提取成功 ===")
        print(f"商家: {data.vendor}")
        print(f"总金额: {data.amount} {data.currency}")
        print(f"分类: {data.category}")
        
        # 6. (可选) 演示自动降级到本地 OCR 模式 (使用不支持图片的模型时触发)
        print(f"\n正在尝试使用纯文本模型 (如 gpt-3.5-turbo)，它会自动触发本地 OCR...")
        # 提示：需要安装 cnocr (pip install cnocr) 或 easyocr (pip install easyocr torch torchvision)
        try:
            # 传递不支持 vision 的模型名称时，内部会自动触发 use_local_ocr=True
            data_ocr = skill.extract_receipt_data(receipt_image, model="gpt-3.5-turbo")
            print("=== 自动本地 OCR 提取成功 ===")
            print(f"商家: {data_ocr.vendor}")
            print(f"总金额: {data_ocr.amount} {data_ocr.currency}")
        except ImportError as e:
            print(f"跳过本地 OCR 演示 (未安装依赖): {e}")
        except Exception as e:
            print(f"自动本地 OCR 模式提取失败: {e}")

    except Exception as e:
        print(f"Vision 提取失败: {e}")

if __name__ == "__main__":
    main()
