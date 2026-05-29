"""检查页面HTML内容是否包含像素风格样式"""
import requests

# 检查首页是否包含像素风格CSS
resp = requests.get("http://localhost:5000/", timeout=5)
html = resp.text

# 检查关键像素风格元素
checks = [
    ("Press Start 2P 字体", "Press+Start+2P" in html),
    ("像素风格变量", "--pixel-black" in html),
    ("像素风格卡片", "pixel-card" in html),
    ("像素风格按钮", "pixel-btn" in html),
    ("像素风格导航", "pixel-navbar" in html),
    ("Bootstrap Icons", "bootstrap-icons" in html),
]

print("像素风格样式检查:")
print("-" * 40)
for name, result in checks:
    status = "✓" if result else "✗"
    print(f"{status} {name}")

# 检查API状态接口
resp = requests.get("http://localhost:5000/api/status", timeout=5)
data = resp.json()
print("\nAPI状态检查:")
print("-" * 40)
print(f"✓ 运行状态: {data.get('running', False)}")
print(f"✓ 微信连接: {data.get('connected', False)}")
print(f"✓ AI模型: {data.get('ai_model', '未知')}")
print(f"✓ 监控联系人: {len(data.get('contacts', []))} 个")
