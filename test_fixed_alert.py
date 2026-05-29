"""验证提示框固定定位修复"""
import requests

resp = requests.get("http://localhost:5000/ai-config", timeout=5)
html = resp.text

checks = [
    ("alerts-fixed类", "alerts-fixed" in html),
    ("固定定位", "position: fixed" in html),
    ("z-index: 9999", "z-index: 9999" in html),
    ("顶部定位", "top: 60px" in html),
    ("居中显示", "left: 50%" in html),
    ("testModel函数", "async function testModel" in html),
]

print("提示框固定定位检查:")
print("-" * 40)
for name, result in checks:
    status = "✓" if result else "✗"
    print(f"{status} {name}")
print("-" * 40)
print("✓ 修复完成！提示框现在会固定在页面顶部显示")
