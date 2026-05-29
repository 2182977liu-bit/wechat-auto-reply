"""测试新字体系统"""
import requests

PAGES = [
    ("http://localhost:5000/", "首页"),
    ("http://localhost:5000/contacts", "联系人"),
    ("http://localhost:5000/ai-config", "AI配置"),
    ("http://localhost:5000/logs", "日志"),
]

checks = [
    ("VT323正文字体", "VT323"),
    ("Press Start 2P标题字体", "Press+Start+2P"),
    ("Silkscreen UI字体", "Silkscreen"),
    ("font-display类", "font-display"),
    ("font-body类", "font-body"),
    ("font-ui类", "font-ui"),
    ("info-box组件", "info-box"),
    ("pixel-btn-sm小按钮", "pixel-btn-sm"),
    ("主题切换功能", "data-theme"),
]

print("字体系统检查:")
print("=" * 50)
for url, name in PAGES:
    try:
        resp = requests.get(url, timeout=5)
        html = resp.text
        passed = 0
        total = len(checks)
        for check_name, keyword in checks:
            if keyword in html:
                passed += 1
        status = "✓" if resp.status_code == 200 and passed == total else "✗"
        print(f"{status} {name:10} | 状态: {resp.status_code} | 字体检查: {passed}/{total}")
    except Exception as e:
        print(f"✗ {name:10} | 错误: {e}")

print("=" * 50)

# 检查是否有内联的小字体（8px/9px/10px）
resp = requests.get("http://localhost:5000/", timeout=5)
html = resp.text
small_fonts = []
for size in ["8px", "9px", "10px"]:
    if f"font-size: {size}" in html:
        small_fonts.append(size)

if small_fonts:
    print(f"⚠ 发现内联小字体: {', '.join(small_fonts)}")
else:
    print("✓ 未发现内联小字体（8px/9px/10px）")
