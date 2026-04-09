import os
import sys
import subprocess
import json

def run_command(cmd):
    print(f"执行命令: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ 失败: {result.stderr}")
        sys.exit(1)
    return result.stdout

def main():
    print("======================================")
    print("开始验证 TaxHackerSkill (OpenClaw 版)")
    print("======================================")

    # 1. 安装依赖
    print("\n[1/4] 安装相关依赖...")
    run_command("pip install -r tax_hacker_skill/requirements.txt")
    print("✔️  依赖安装完成")

    # 2. 准备测试文件
    print("\n[2/4] 准备测试数据...")
    test_image = "test_invoice.jpg"
    if not os.path.exists(test_image):
        try:
            from PIL import Image
            img = Image.new('RGB', (800, 600), color = (255, 255, 255))
            img.save(test_image)
            print(f"✔️  创建了空白测试图片: {test_image}")
        except ImportError:
            print("❌ 未安装 Pillow 库，请先安装 Pillow 以生成测试图片")
            sys.exit(1)
    else:
        print(f"✔️  使用已有测试图片: {test_image}")

    # 3. 模拟 OpenClaw skill invoke 命令调用
    print("\n[3/4] 模拟 OpenClaw 'skill invoke' 调用测试...")
    if not os.getenv("OPENAI_API_KEY") and not os.getenv("OPENCLAW_LLM_API_KEY"):
        print("⚠️ 未检测到 API Key，跳过实际的 LLM 调用验证。")
        print("请设置 OPENAI_API_KEY 环境变量后重新运行以测试端到端流程。")
        sys.exit(0)

    # 使用不支持 vision 的模型测试自动降级 OCR，并设定较短超时
    cmd = f"python -m tax_hacker_skill.skill {test_image} --local-ocr --ocr-engine cnocr"
    stdout = run_command(cmd)
    
    with open("invoke_result.json", "w", encoding="utf-8") as f:
        f.write(stdout)

    print("✔️  调用成功！")

    # 4. 验证返回的 JSON 结果是否符合通用发票结构
    print("\n[4/4] 检查 JSON 返回结果结构...")
    try:
        data = json.loads(stdout)
        if "error" in data:
            print(f"❌ 技能返回了错误: {data['error']}")
            sys.exit(1)
        
        expected_fields = ["invoice_code", "invoice_number", "date", "amount", "tax_amount", "check_code"]
        missing = [f for f in expected_fields if f not in data]
        if missing:
            print(f"❌ 缺失期望字段: {missing}")
            sys.exit(1)
        
        print("✔️  JSON 结构验证通过，包含核心发票字段。")
        print("提取结果:")
        print(json.dumps(data, indent=2, ensure_ascii=False))

    except json.JSONDecodeError:
        print("❌ 返回结果不是有效的 JSON 格式")
        print("输出:", stdout)
        sys.exit(1)

    print("\n======================================")
    print("🎉 验证通过！Skill 已准备好在 OpenClaw 部署。")
    print("请参考 manifest.yaml 或 SKILL.md 进行配置。")
    print("======================================")

if __name__ == "__main__":
    main()
