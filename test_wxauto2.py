"""直接测试wxauto4连接"""
import os
import sys
from pathlib import Path

# 设置comtypes缓存到用户目录
user_cache = Path.home() / ".comtypes_cache"
user_cache.mkdir(exist_ok=True)
os.environ["COMTYPES_CACHE"] = str(user_cache)

# 在导入comtypes之前，monkey-patch gen_dir
import comtypes
import comtypes.client
comtypes.client.gen_dir = str(user_cache)
comtypes.gen.__path__ = [str(user_cache)]

print(f"comtypes缓存目录: {user_cache}")
print(f"comtypes.client.gen_dir: {comtypes.client.gen_dir}")
print("正在导入wxauto4...")

try:
    from wxauto4 import WeChat
    print("wxauto4导入成功")
    
    print("正在连接微信...")
    wx = WeChat()
    print(f"微信实例创建成功: {wx}")
    
    print("获取会话列表...")
    sessions = wx.GetSessionList()
    print(f"会话列表: {sessions}")
    
    print("连接成功！")
except Exception as e:
    print(f"错误: {type(e).__name__}: {e}")
