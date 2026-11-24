"""
消息检测器
检测微信新消息，发送回复
"""

import os
import time
import random
import logging
import ctypes
from ctypes import wintypes
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime

_user_cache = Path.home() / ".comtypes_cache"
_user_cache.mkdir(exist_ok=True)
os.environ["COMTYPES_CACHE"] = str(_user_cache)

log = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_INTERVAL = 5

# ---- SendInput 结构体：用于模拟真实键盘逐字输入（支持中文/emoji） ----
INPUT_KEYBOARD = 1
KEYEVENTF_UNICODE = 0x0004
KEYEVENTF_KEYUP = 0x0002
VK_RETURN = 0x0D
VK_CONTROL = 0x11
VK_DELETE = 0x2E


class _KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_size_t),
    ]


class _INPUT_UNION(ctypes.Union):
    _fields_ = [("ki", _KEYBDINPUT), ("padding", ctypes.c_byte * 32)]


class _INPUT(ctypes.Structure):
    _fields_ = [("type", wintypes.DWORD), ("u", _INPUT_UNION)]


def _send_vk(vk: int, key_up: bool = False) -> None:
    inp = _INPUT(type=INPUT_KEYBOARD)
    inp.u.ki = _KEYBDINPUT(vk, 0, KEYEVENTF_KEYUP if key_up else 0, 0, 0)
    ctypes.windll.user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(_INPUT))


def _send_unicode_unit(unit: int) -> None:
    for flags in (KEYEVENTF_UNICODE, KEYEVENTF_UNICODE | KEYEVENTF_KEYUP):
        inp = _INPUT(type=INPUT_KEYBOARD)
        inp.u.ki = _KEYBDINPUT(0, unit, flags, 0, 0)
        ctypes.windll.user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(_INPUT))

VERSION_INFO = {
    "free": {
        "name": "wxauto4 免费版",
        "max_wechat": "4.1.8.107",
        "download": "https://github.com/SiverKing/wechat4.0-windows-versions/releases/tag/v4.1.8.107"
    },
    "plus": {
        "name": "wxautox4 Plus版",
        "max_wechat": "4.1.9.35",
        "download": "https://github.com/SiverKing/wechat4.0-windows-versions/releases/tag/v4.1.9.35"
    }
}


@dataclass
class Message:
    sender: str
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    processed: bool = False


class WeChatDetector:

    def __init__(self, config: dict) -> None:
        self.config = config
        self.wx = None
        self.connected = False
        self.history: list[Message] = []
        self._baseline: dict[str, int] = {}
        self.last_error: str = ""
        self.wechat_version: str = ""
        self.wxauto_type: str = "free"
        self._window_activated_at: float = 0
        self._window_cache_ttl: float = 5.0

    def _check_wechat_window(self) -> bool:
        try:
            hwnd = ctypes.windll.user32.FindWindowW(None, "微信")
            if hwnd:
                return True
            hwnd = ctypes.windll.user32.FindWindowW(None, "WeChat")
            return bool(hwnd)
        except Exception:
            return False

    def _activate_wechat_window(self) -> bool:
        now = time.time()
        if now - self._window_activated_at < self._window_cache_ttl:
            return True

        try:
            hwnd = ctypes.windll.user32.FindWindowW(None, "微信")
            if not hwnd:
                hwnd = ctypes.windll.user32.FindWindowW(None, "WeChat")
            if not hwnd:
                return False
            if ctypes.windll.user32.IsIconic(hwnd):
                ctypes.windll.user32.ShowWindow(hwnd, 9)
                time.sleep(0.5)
            ctypes.windll.user32.SetForegroundWindow(hwnd)
            time.sleep(0.5)
            ctypes.windll.user32.BringWindowToTop(hwnd)
            time.sleep(0.2)
            self._window_activated_at = time.time()
            return True
        except Exception as e:
            log.warning(f"激活微信窗口失败: {e}")
            return False

    def _try_import_wxauto(self) -> tuple[bool, object]:
        self._setup_comtypes_cache()
        try:
            from wxautox4 import WeChat
            self.wxauto_type = "plus"
            log.info("使用 wxautox4 Plus版")
            return True, WeChat
        except ImportError:
            pass
        try:
            from wxauto4 import WeChat
            self.wxauto_type = "free"
            log.info("使用 wxauto4 免费版")
            return True, WeChat
        except ImportError:
            pass
        return False, None

    def _setup_comtypes_cache(self) -> None:
        try:
            import comtypes.gen
            user_cache = Path.home() / ".comtypes_cache"
            user_cache.mkdir(exist_ok=True)
            comtypes.gen.__path__ = [str(user_cache)]
        except Exception:
            pass

    def _get_version_error_message(self) -> str:
        info = VERSION_INFO[self.wxauto_type]
        return (
            f"微信版本不兼容！\n"
            f"当前使用的库：{info['name']}\n"
            f"支持的最高微信版本：{info['max_wechat']}\n"
            f"解决方案：降级微信到 {info['max_wechat']}\n"
            f"下载地址：{info['download']}"
        )

    def connect(self) -> bool:
        wxauto_available, WeChatClass = self._try_import_wxauto()
        if not wxauto_available:
            self.last_error = "未安装wxauto4，请运行: pip install wxauto4"
            log.error(self.last_error)
            return False

        self._fix_comtypes_permissions()

        for attempt in range(1, MAX_RETRIES + 1):
            log.info(f"尝试连接微信 ({attempt}/{MAX_RETRIES})...")

            if not self._check_wechat_window():
                self.last_error = "未找到微信窗口，请先打开微信客户端并登录"
                log.error(self.last_error)
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_INTERVAL)
                continue

            self._activate_wechat_window()

            try:
                self.wx = WeChatClass()
                sessions = self.wx.GetSession()
                if sessions:
                    self.connected = True
                    self.last_error = ""
                    log.info(f"微信连接成功，获取到 {len(sessions)} 个会话")
                    return True
                elif hasattr(self.wx, 'nickname') and self.wx.nickname:
                    self.connected = True
                    self.last_error = ""
                    log.info(f"微信连接成功（用户: {self.wx.nickname}）")
                    return True
                else:
                    self.last_error = "无法获取会话列表，请确保微信已登录"
                    log.warning(self.last_error)
            except Exception as e:
                error_msg = str(e)
                if "FindControl" in error_msg:
                    self.last_error = self._get_version_error_message()
                elif "Permission denied" in error_msg:
                    self.last_error = "权限不足，请以管理员权限运行"
                else:
                    self.last_error = f"连接失败: {error_msg}"
                log.error(self.last_error)

            if attempt < MAX_RETRIES:
                time.sleep(RETRY_INTERVAL)

        log.error(f"连接失败，已重试 {MAX_RETRIES} 次")
        return False

    def _fix_comtypes_permissions(self) -> None:
        try:
            import comtypes
            gen_dir = Path(comtypes.__file__).parent / "gen"
            if gen_dir.exists():
                import stat
                for item in gen_dir.rglob("*"):
                    try:
                        item.chmod(stat.S_IWRITE | stat.S_IREAD)
                    except Exception:
                        pass
        except Exception:
            pass

    def disconnect(self) -> None:
        if not self.connected and self.wx is None:
            return
        self.wx = None
        self.connected = False
        self._baseline.clear()
        self._window_activated_at = 0
        log.info("微信已断开")

    def init_baseline(self, contacts: list[str]) -> None:
        log.info("正在初始化消息基线...")
        for contact in contacts:
            try:
                self._activate_wechat_window()
                time.sleep(0.3)
                self.wx.ChatWith(contact)
                time.sleep(0.8)
                raw_msgs = self.wx.GetAllMessage()
                count = len(raw_msgs)
                self._baseline[contact] = count
                log.info(f"基线 [{contact}]: {count} 条消息")
            except Exception as e:
                log.warning(f"基线初始化失败 [{contact}]: {e}")
                self._baseline[contact] = 0
        log.info("基线初始化完成")

    def get_new_messages(self, contact: str) -> list[Message]:
        if not self.connected or not self.wx:
            return []

        if contact not in self._baseline:
            self._baseline[contact] = 0

        try:
            self._activate_wechat_window()
            time.sleep(0.3)
            self.wx.ChatWith(contact)
            time.sleep(0.8)

            raw_msgs = self.wx.GetAllMessage()
            current_count = len(raw_msgs)
            baseline = self._baseline[contact]

            if current_count < baseline:
                log.info(f"[{contact}] 消息数量减少 ({baseline}->{current_count})，重置基线")
                self._baseline[contact] = current_count
                return []

            if current_count <= baseline:
                return []

            new_msgs = []
            for i in range(baseline, current_count):
                msg = raw_msgs[i]
                # 按消息归属过滤：只处理对方消息（friend），
                # 自己(self)/系统(sys)/时间(time)等一律跳过，杜绝自回复循环
                attr = getattr(msg, "attr", "")
                if attr != "friend":
                    continue
                content = getattr(msg, "content", "") or ""
                if not content:
                    continue
                sender = getattr(msg, "sender", "") or contact
                m = Message(sender=sender, content=content)
                new_msgs.append(m)
                self.history.append(m)

            self._baseline[contact] = current_count

            if len(self.history) > 1000:
                self.history = self.history[-500:]

            return new_msgs

        except Exception as e:
            log.error(f"获取消息失败 [{contact}]: {e}")
            return []

    def _find_input_control(self):
        """定位聊天输入框：优先当前焦点控件，否则取窗口下半部最靠下的编辑框。
        找不到或位置可疑时返回 None，交由粘贴方式兜底，避免误输入到搜索框。"""
        try:
            from wxauto4 import uia
        except ImportError:
            try:
                from wxautox4 import uia
            except ImportError:
                return None
        try:
            hwnd = ctypes.windll.user32.FindWindowW(None, "微信")
            if not hwnd:
                hwnd = ctypes.windll.user32.FindWindowW(None, "WeChat")
            if not hwnd:
                return None
            root = uia.ControlFromHandle(hwnd)
            if root is None:
                return None
            wr = root.BoundingRectangle
            min_top = wr.top + wr.height() * 0.4

            fg = uia.GetFocusedControl()
            if fg is not None and fg.ControlTypeName in ("EditControl", "DocumentControl"):
                r = fg.BoundingRectangle
                if r.top >= min_top and r.height() >= 30:
                    return fg

            # 按类型枚举编辑框（限制深度与数量，避免全树遍历过慢）
            edits = []
            stack = [(root, 0)]
            while stack and len(edits) < 10:
                ctrl, depth = stack.pop()
                if depth > 12:
                    continue
                try:
                    children = ctrl.GetChildren()
                except Exception:
                    continue
                for child in children:
                    if child.ControlTypeName == "EditControl":
                        edits.append(child)
                    else:
                        stack.append((child, depth + 1))
            candidates = []
            for e in edits:
                r = e.BoundingRectangle
                if r.top >= min_top and r.height() >= 30:
                    candidates.append((r.top, e))
            if not candidates:
                return None
            candidates.sort(key=lambda x: x[0])
            return candidates[-1][1]
        except Exception as e:
            log.debug(f"定位输入框失败: {e}")
            return None

    def _type_like_human(self, text: str) -> bool:
        """聚焦输入框后逐字键入（随机间隔模拟真人），回车发送。
        任一前置条件不满足即返回 False，由调用方回退到粘贴发送。"""
        ctrl = self._find_input_control()
        if ctrl is None:
            return False
        try:
            wx_hwnd = ctypes.windll.user32.FindWindowW(None, "微信") or \
                ctypes.windll.user32.FindWindowW(None, "WeChat")
            ctrl.SetFocus()
            time.sleep(0.2)
            if ctypes.windll.user32.GetForegroundWindow() != wx_hwnd:
                return False

            # 清空输入框残留：Ctrl+A -> Delete
            _send_vk(VK_CONTROL)
            _send_vk(ord("A"))
            _send_vk(ord("A"), key_up=True)
            _send_vk(VK_CONTROL, key_up=True)
            time.sleep(0.1)
            _send_vk(VK_DELETE)
            _send_vk(VK_DELETE, key_up=True)
            time.sleep(0.15)

            # 换行替换为空格，避免提前触发发送
            text = text.replace("\r", " ").replace("\n", " ").strip()
            data = text.encode("utf-16-le")
            for i in range(0, len(data), 2):
                unit = data[i] | (data[i + 1] << 8)
                _send_unicode_unit(unit)
                delay = random.uniform(0.04, 0.16)
                if random.random() < 0.06:
                    delay += random.uniform(0.2, 0.5)
                time.sleep(delay)

            time.sleep(random.uniform(0.3, 0.8))
            _send_vk(VK_RETURN)
            _send_vk(VK_RETURN, key_up=True)
            return True
        except Exception as e:
            log.warning(f"逐字输入失败: {e}")
            return False

    def send_reply(self, contact: str, text: str, input_mode: str = "typing") -> bool:
        if not self.connected or not self.wx:
            return False

        try:
            self._activate_wechat_window()
            time.sleep(0.3)
            self.wx.ChatWith(contact)
            time.sleep(0.3)

            sent = False
            if input_mode == "typing":
                sent = self._type_like_human(text)
                if not sent:
                    log.warning("逐字输入不可用，回退到粘贴发送")
            if not sent:
                resp = self.wx.SendMsg(text)
                sent = bool(resp)
                if not sent:
                    log.error(f"SendMsg 返回失败: {resp}")

            if sent:
                time.sleep(1.0)
                self._baseline[contact] = self._baseline.get(contact, 0) + 1
                log.info(f"已回复 [{contact}]: {text[:50]}...")
            return sent
        except Exception as e:
            log.error(f"发送失败 [{contact}]: {e}")
            return False

    def scan_contacts(self, contacts: list[str]) -> dict[str, list[Message]]:
        if not self.connected:
            return {}

        result = {}
        for contact in contacts:
            if not self.connected:
                break
            msgs = self.get_new_messages(contact)
            if msgs:
                result[contact] = msgs
        return result

    def get_connection_status(self) -> dict:
        return {
            "connected": self.connected,
            "last_error": self.last_error,
            "wechat_window_exists": self._check_wechat_window(),
            "wxauto_type": self.wxauto_type,
            "version_info": VERSION_INFO.get(self.wxauto_type, {})
        }
