import ctypes
import ctypes.wintypes

def get_class_name(hwnd):
    buf = ctypes.create_unicode_buffer(256)
    ctypes.windll.user32.GetClassNameW(hwnd, buf, 256)
    return buf.value

def get_window_text(hwnd):
    buf = ctypes.create_unicode_buffer(256)
    ctypes.windll.user32.GetWindowTextW(hwnd, buf, 256)
    return buf.value

EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)

results = []
def enum_callback(hwnd, lparam):
    title = get_window_text(hwnd)
    if "微信" in title or "WeChat" in title:
        cls = get_class_name(hwnd)
        visible = ctypes.windll.user32.IsWindowVisible(hwnd)
        results.append((hwnd, cls, title, visible))
    return True

ctypes.windll.user32.EnumWindows(EnumWindowsProc(enum_callback), 0)

print("微信相关窗口:")
for hwnd, cls, title, visible in results:
    print(f"  句柄: {hwnd} | 类名: '{cls}' | 标题: '{title}' | 可见: {bool(visible)}")

print(f"\nwxauto4 版本:")
import wxauto4
print(f"  {wxauto4.__version__}")

print(f"\n微信安装路径:")
import os, glob
wechat_paths = [
    "C:\\Program Files (x86)\\Tencent\\WeChat",
    "C:\\Program Files\\Tencent\\WeChat",
    os.path.expandvars("%LOCALAPPDATA%\\Programs\\Tencent\\WeChat"),
]
for p in wechat_paths:
    if os.path.exists(p):
        print(f"  找到: {p}")
        for f in glob.glob(os.path.join(p, "WeChat*.exe")):
            print(f"    {f}")
