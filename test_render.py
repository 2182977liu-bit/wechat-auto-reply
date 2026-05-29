"""直接检查Flask渲染的模板内容"""
import sys
sys.path.insert(0, "d:\\Desktop\\新建文件夹\\wechat_auto_reply")
from pathlib import Path
from flask import Flask, render_template

# 创建一个简单的Flask应用
ROOT = Path("d:\\Desktop\\新建文件夹\\wechat_auto_reply")
app = Flask(__name__, template_folder=str(ROOT / "templates"))

# 打印模板文件夹
print(f"模板文件夹: {app.template_folder}")

# 列出模板文件
import os
template_dir = app.template_folder
print(f"\n模板文件列表:")
for f in os.listdir(template_dir):
    if f.endswith('.html'):
        filepath = os.path.join(template_dir, f)
        size = os.path.getsize(filepath)
        print(f"  - {f} ({size} 字节)")

# 渲染一个模板看看
with app.app_context():
    class FakeStatus:
        def __init__(self):
            self.running = False
            self.connected = False
            self.contacts = []
            self.ai_model = "deepseek"
            self.available_models = []
            self.last_error = "测试错误"

    html = render_template("index.html", status=FakeStatus())
    # 检查是否包含像素风格
    if "pixel" in html:
        print("\n✓ 模板包含像素风格!")
    else:
        print("\n✗ 模板不包含像素风格!")
    # 打印前500字符
    print(f"\n渲染结果前500字符:")
    print(html[:500])
