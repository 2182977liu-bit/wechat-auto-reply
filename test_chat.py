import os
from pathlib import Path

user_cache = Path.home() / ".comtypes_cache"
user_cache.mkdir(exist_ok=True)
os.environ["COMTYPES_CACHE"] = str(user_cache)
import comtypes, comtypes.client
comtypes.client.gen_dir = str(user_cache)
comtypes.gen.__path__ = [str(user_cache)]

from wxauto4 import WeChat
wx = WeChat()

print(f"nickname: {wx.nickname}")
print(f"myinfo: {wx.GetMyInfo()}")

print("\n=== GetSession ===")
sessions = wx.GetSession()
print(f"  count: {len(sessions)}")
for i, s in enumerate(sessions[:5]):
    print(f"  [{i}] type={type(s).__name__} dir={[a for a in dir(s) if not a.startswith('_')]}")

print("\n=== ChatWith 青松 ===")
try:
    chat = wx.ChatWith("青松")
    print(f"  chat type: {type(chat)}")
    print(f"  chat dir: {[a for a in dir(chat) if not a.startswith('_')]}")
    msgs = wx.GetAllMessage()
    print(f"  messages: {len(msgs)}")
    for m in msgs[-3:]:
        print(f"    sender={m.sender} content={m.content[:50]}")
except Exception as e:
    print(f"  error: {type(e).__name__}: {e}")
