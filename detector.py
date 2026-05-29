"""
消息检测器
检测微信新消息，发送回复
"""

import os
import time
import logging
import ctypes
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime

_user_cache = Path.home() / ".comtypes_cache"
_user_cache.mkdir(exist_ok=True)
os.environ["COMTYPES_CACHE"] = str(_user_cache)

log = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_INTERVAL = 5

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
        self._sent_contents: set[str] = set()
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
        self._sent_contents.clear()
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
            actual_new_count = 0
            for i in range(baseline, current_count):
                msg = raw_msgs[i]
                content = msg.content if hasattr(msg, 'content') else str(msg.get('content', ''))
                if content in self._sent_contents:
                    log.debug(f"[{contact}] 跳过自己发的消息: {content[:30]}...")
                    actual_new_count += 1
                    continue
                m = Message(sender=contact, content=content)
                new_msgs.append(m)
                self.history.append(m)
                actual_new_count += 1

            self._baseline[contact] = current_count

            if len(self.history) > 1000:
                self.history = self.history[-500:]

            return new_msgs

        except Exception as e:
            log.error(f"获取消息失败 [{contact}]: {e}")
            return []

    def send_reply(self, contact: str, text: str) -> bool:
        if not self.connected or not self.wx:
            return False

        try:
            self._activate_wechat_window()
            time.sleep(0.3)
            self.wx.ChatWith(contact)
            time.sleep(0.3)
            self.wx.SendMsg(text)
            time.sleep(1.5)

            self._sent_contents.add(text)
            self._baseline[contact] = self._baseline.get(contact, 0) + 1

            if len(self._sent_contents) > 500:
                self._sent_contents = set(list(self._sent_contents)[-200:])

            log.info(f"已回复 [{contact}]: {text[:50]}...")
            return True
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
