import os, json
from pathlib import Path

user_cache = Path.home() / ".comtypes_cache"
user_cache.mkdir(exist_ok=True)
os.environ["COMTYPES_CACHE"] = str(user_cache)
import comtypes, comtypes.client
comtypes.client.gen_dir = str(user_cache)
comtypes.gen.__path__ = [str(user_cache)]

from wxauto4 import WeChat
wx = WeChat()

print("=== 会话列表 ===")
sessions = wx.GetSession()
for i, s in enumerate(sessions[:10]):
    print(f"  [{i}] {s}  type={type(s)}")

print()
print("=== 联系人配置 ===")
config_path = r"d:\Desktop\新建文件夹\wechat_auto_reply\config.json"
with open(config_path, "r", encoding="utf-8") as f:
    cfg = json.load(f)
contacts = cfg["contacts"]
print(f"  contacts: {contacts}")

print()
print("=== 尝试 ChatWith 第一个联系人 ===")
if contacts:
    name = contacts[0]
    print(f"  ChatWith('{name}')...")
    try:
        wx.ChatWith(name)
        print(f"  成功打开聊天: {name}")
        msgs = wx.GetAllMessage()
        print(f"  获取到 {len(msgs)} 条消息")
        for m in msgs[-3:]:
            print(f"    {m}")
    except Exception as e:
        print(f"  失败: {e}")
