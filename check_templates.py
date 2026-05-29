"""检查Flask模板路径"""
import sys
sys.path.insert(0, "d:\\Desktop\\新建文件夹\\wechat_auto_reply")
from app import create_app

# 创建一个假的bot对象用于测试
class FakeBot:
    def __init__(self):
        self.config = {"ai": {"models": {}, "default_model": "deepseek"}, "wechat": {"contacts": []}}
        self.running = False
        self.replier = type('obj', (object,), {'switch_model': lambda s,m: False, 'test_model': lambda s,m: False})()

    def get_status(self):
        return {"running": False, "connected": False, "contacts": [], "ai_model": "deepseek", "available_models": [], "last_error": ""}

bot = FakeBot()
app = create_app(bot)

# 打印模板文件夹路径
print(f"模板文件夹: {app.template_folder}")

# 列出模板文件
import os
template_dir = app.template_folder
if os.path.exists(template_dir):
    print(f"\n模板文件列表:")
    for f in os.listdir(template_dir):
        if f.endswith('.html'):
            filepath = os.path.join(template_dir, f)
            size = os.path.getsize(filepath)
            print(f"  - {f} ({size} 字节)")
