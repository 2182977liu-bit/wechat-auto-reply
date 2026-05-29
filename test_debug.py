import os
from pathlib import Path

user_cache = Path.home() / ".comtypes_cache"
user_cache.mkdir(exist_ok=True)
os.environ["COMTYPES_CACHE"] = str(user_cache)

import comtypes
import comtypes.client
comtypes.client.gen_dir = str(user_cache)
comtypes.gen.__path__ = [str(user_cache)]

import logging
logging.basicConfig(level=logging.DEBUG)

from wxauto4 import WeChat

print("正在以debug模式连接微信...")
try:
    wx = WeChat(debug=True)
    print("连接成功！")
except Exception as e:
    print(f"错误: {e}")
