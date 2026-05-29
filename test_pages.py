"""测试所有页面是否正常响应（不需要浏览器）"""
import requests

# 测试的页面列表
PAGES = [
    ("http://localhost:5000/", "首页"),
    ("http://localhost:5000/contacts", "联系人"),
    ("http://localhost:5000/ai-config", "AI配置"),
    ("http://localhost:5000/logs", "日志"),
    ("http://localhost:5000/api/status", "API状态"),
    ("http://localhost:5000/api/logs", "API日志"),
]

print("=" * 50)
print("开始测试所有页面")
print("=" * 50)

for url, name in PAGES:
    try:
        # 发送GET请求
        resp = requests.get(url, timeout=5)
        # 检查状态码
        if resp.status_code == 200:
            # 检查内容长度
            content_len = len(resp.text)
            print(f"✓ {name:10} | {url:35} | 状态: {resp.status_code} | 大小: {content_len} 字节")
        else:
            print(f"✗ {name:10} | {url:35} | 状态: {resp.status_code}")
    except Exception as e:
        print(f"✗ {name:10} | {url:35} | 错误: {e}")

print("=" * 50)
print("测试完成!")
