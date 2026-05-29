"""验证主题切换功能"""
import requests

resp = requests.get("http://localhost:5000/", timeout=5)
html = resp.text

checks = [
    ("data-theme属性", 'data-theme="dark"' in html),
    ("主题切换按钮", 'theme-toggle' in html),
    ("localStorage持久化", 'localStorage' in html),
    ("toggleTheme函数", 'toggleTheme' in html),
    ("setTheme函数", 'setTheme' in html),
    ("深色主题变量", '[data-theme="dark"]' in html),
    ("浅色主题变量", '[data-theme="light"]' in html),
    ("扫描线效果", 'scanline' in html),
    ("浮动动画", 'pixel-float' in html),
    ("像素分割线", 'pixel-divider' in html),
]

print("主题切换功能检查:")
print("-" * 40)
all_pass = True
for name, result in checks:
    status = "✓" if result else "✗"
    if not result:
        all_pass = False
    print(f"{status} {name}")

print("-" * 40)
if all_pass:
    print("✓ 所有检查通过！主题切换功能正常！")
else:
    print("✗ 部分检查未通过")

# 测试所有页面
PAGES = [
    ("http://localhost:5000/", "首页"),
    ("http://localhost:5000/contacts", "联系人"),
    ("http://localhost:5000/ai-config", "AI配置"),
    ("http://localhost:5000/logs", "日志"),
]

print("\n页面响应检查:")
print("-" * 40)
for url, name in PAGES:
    resp = requests.get(url, timeout=5)
    has_theme = 'data-theme' in resp.text
    status = "✓" if resp.status_code == 200 and has_theme else "✗"
    print(f"{status} {name:10} | 状态: {resp.status_code} | 主题支持: {has_theme}")
