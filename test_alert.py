"""测试AI配置页面的测试按钮功能"""
import requests

# 测试小米模型
print("测试小米模型连接...")
resp = requests.post("http://localhost:5000/api/ai-config/test/xiaomi", timeout=30)
data = resp.json()
print(f"  状态码: {resp.status_code}")
print(f"  响应: {data}")

# 测试AI配置页面
print("\n测试AI配置页面...")
resp = requests.get("http://localhost:5000/ai-config", timeout=5)
html = resp.text
print(f"  状态码: {resp.status_code}")
print(f"  包含testModel函数: {'async function testModel' in html}")
print(f"  包含错误处理: {'d._ok' in html}")
print(f"  包含动画: {'alert-in' in html}")
print(f"  z-index修复: {'z-index: 100' in html}")
