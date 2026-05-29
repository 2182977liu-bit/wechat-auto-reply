"""测试小米AI模型配置"""
import requests

# 测试API状态
resp = requests.get("http://localhost:5000/api/status", timeout=5)
data = resp.json()
print("API状态:")
print(f"  可用模型: {data.get('available_models', [])}")
print(f"  当前模型: {data.get('ai_model', '未知')}")

# 测试AI配置页面
resp = requests.get("http://localhost:5000/ai-config", timeout=5)
html = resp.text
print(f"\nAI配置页面:")
print(f"  状态: {resp.status_code}")
print(f"  包含小米配置: {'xiaomi' in html}")
print(f"  包含正确URL: {'token-plan-cn.xiaomimimo.com' in html}")

# 测试小米模型
print("\n测试小米模型连接...")
resp = requests.post("http://localhost:5000/api/ai-config/test/xiaomi", timeout=30)
data = resp.json()
print(f"  结果: {data}")
