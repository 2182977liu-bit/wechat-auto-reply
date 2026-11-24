"""
消息检测器（纯 UI 自动化版，不依赖 wxauto / wxautox）

安全原则（2026-11-24 账号被强制下线后整改）：
  - 不读取微信进程内存
  - 不解密微信本地数据库（contact.db / message_*.db 一律不碰）
  - 消息收发全部通过 Windows UI 自动化（系统无障碍接口）+ 模拟键鼠，
    与真人操作官方客户端的路径一致

实现：wechatauto-replica 的纯 UIA 子模块
  https://github.com/fanyuantaier/wechatauto-replica （Apache-2.0）
  - 读消息：ui.main.WeChatMainWnd + ChatBox.get_msgs()（UIA 控件树）
  - 发消息：guia 模拟键鼠逐字输入 / quick_send（verify=False，禁止数据库回读）
要求：微信已登录、主窗口存在。无需管理员权限。

对外接口保持与旧版一致：connect / init_baseline / get_new_messages /
send_reply / scan_contacts / get_connection_status / disconnect。
"""

import os
import time
import random
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

BACKEND_INFO = {
    "name": "wechatauto-replica (UIA only)",
    "repo": "https://github.com/fanyuantaier/wechatauto-replica",
    "license": "Apache-2.0",
    "verified_wechat": "4.2.0.53",
    "read": "UIA 控件树（不读内存、不解密数据库）",
    "send": "模拟键鼠逐字输入 + UIA 热激活",
}


@dataclass
class Message:
    sender: str
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    processed: bool = False


def _diff_new(prev: list, curr: list) -> list:
    """比较两轮可见消息快照，返回新增部分。

    prev 的后缀与 curr 的前缀取最长重叠，重叠之后即新消息。
    完全不重叠（例如会话被切换/清空）时返回空，宁可漏报也不把历史当新消息回复。
    """
    if not prev:
        return curr
    max_ol = min(len(prev), len(curr))
    for ol in range(max_ol, 0, -1):
        if prev[-ol:] == curr[:ol]:
            return curr[ol:]
    return []


class WeChatDetector:

    def __init__(self, config: dict) -> None:
        self.config = config
        self.ui = None               # WeChatMainWnd，纯 UIA
        self.connected = False
        self.last_error: str = ""
        self.nickname: str = ""
        self.backend: str = BACKEND_INFO["name"]
        # 每个联系人的可见消息快照 {contact: [(attr, type, content), ...]}
        self._snap: dict[str, list] = {}

    # ---- 窗口 / 进程 ----

    def _check_wechat_window(self) -> bool:
        try:
            hwnd = ctypes.windll.user32.FindWindowW(None, "微信")
            if hwnd:
                return True
            hwnd = ctypes.windll.user32.FindWindowW(None, "WeChat")
            return bool(hwnd)
        except Exception:
            return False

    # ---- 连接 ----

    def connect(self) -> bool:
        try:
            from wechatauto.ui.main import WeChatMainWnd
        except ImportError:
            self.last_error = "未安装后端，请运行: pip install wechatauto-replica==1.3.0.1"
            log.error(self.last_error)
            return False

        # wechatauto 导入时会清空 root handlers，恢复文件日志
        from config import ensure_logging
        ensure_logging()

        for attempt in range(1, MAX_RETRIES + 1):
            log.info(f"尝试连接微信 ({attempt}/{MAX_RETRIES})...")
            if not self._check_wechat_window():
                self.last_error = "未找到微信窗口，请先打开微信客户端并登录"
                log.error(self.last_error)
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_INTERVAL)
                continue
            try:
                # 仅 attach 主窗口 UIA 控件树，不实例化任何 DB/内存读取组件
                self.ui = WeChatMainWnd()
                self.nickname = self.ui.nickname or ""
                self.connected = True
                self.last_error = ""
                log.info(
                    f"微信连接成功（窗口: {self.nickname}），"
                    "模式: 纯UI自动化（不读进程内存、不解密数据库）"
                )
                return True
            except Exception as e:
                self.last_error = f"连接失败: {e}"
                log.error(self.last_error)
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_INTERVAL)

        log.error(f"连接失败，已重试 {MAX_RETRIES} 次")
        return False

    def disconnect(self) -> None:
        self.ui = None
        self.connected = False
        self._snap.clear()
        log.info("微信已断开")

    # ---- 会话读取 ----

    def _chatbox(self, contact: str):
        """切换到指定会话并返回 ChatBox（UIA）。失败返回 None。"""
        try:
            cb = self.ui._get_chatbox(nickname=contact, exact=False)
            if cb is None:
                log.warning(f"未找到会话 [{contact}]，请确认名称与微信会话列表一致")
            return cb
        except Exception as e:
            log.warning(f"打开会话失败 [{contact}]: {e}")
            return None

    def init_baseline(self, contacts: list[str]) -> None:
        log.info("正在初始化消息基线...")
        for contact in contacts:
            self._snap.pop(contact, None)
            self.get_new_messages(contact)   # 首轮只建快照，不回复
        log.info("基线初始化完成")

    def get_new_messages(self, contact: str) -> list[Message]:
        if not self.connected or self.ui is None:
            return []
        cb = self._chatbox(contact)
        if cb is None:
            return []
        time.sleep(0.3)   # 等右侧消息区渲染稳定
        try:
            raw = cb.get_msgs() or []
        except Exception as e:
            log.error(f"读取消息失败 [{contact}]: {e}")
            return []

        curr = []
        for m in raw:
            key = (getattr(m, "attr", ""), getattr(m, "type", ""), m.content or "")
            curr.append((key, m))
        keys = [k for k, _ in curr]

        prev = self._snap.get(contact)
        self._snap[contact] = keys
        if prev is None:
            # 首次见到该联系人（含运行中新增）：只记基线，不回复历史消息
            log.info(f"基线 [{contact}]: 记录 {len(keys)} 条可见消息")
            return []

        new_keys = _diff_new(prev, keys)
        if not new_keys:
            return []
        fresh = curr[len(curr) - len(new_keys):]

        new_msgs: list[Message] = []
        for (attr, mtype, _), m in fresh:
            # 自己发的(Self)、系统消息(system)、非文本：不回复
            if attr != "Friend":
                continue
            if mtype != "text":
                log.debug(f"[{contact}] 跳过非文本消息 type={mtype!r}")
                continue
            content = (m.content or "").strip()
            if not content:
                continue
            new_msgs.append(Message(sender=contact, content=content, timestamp=datetime.now()))
        return new_msgs

    # ---- 发送（模拟键鼠，无数据库回读） ----

    @staticmethod
    def _type_text(inp, text: str) -> None:
        """逐字键入；非 BMP 字符（如 emoji）拆成 UTF-16 代理对，避免 wScan 截断"""
        for ch in text:
            code = ord(ch)
            if code > 0xFFFF:
                code -= 0x10000
                inp.type_unicode(chr(0xD800 + (code >> 10)))
                inp.type_unicode(chr(0xDC00 + (code & 0x3FF)))
            else:
                inp.type_unicode(ch)

    def _type_like_human(self, contact: str, text: str) -> bool:
        """真人输入效果：打开会话 -> 聚焦输入框 -> 逐字键入（后端自带拟人节奏）-> 回车。
        任一步失败返回 False，由调用方回退到 quick_send。"""
        try:
            from wechatauto.guia import (
                WeChatGUI, WinInput, VK_A, VK_DELETE, VK_RETURN,
            )
            gui = WeChatGUI()
            if not gui.ensure_visible():
                return False
            if not gui.open_chat(contact):
                return False
            time.sleep(0.6)
            box = gui.get_input_box()
            if not box or not gui.focus_input(box):
                return False
            inp = WinInput()
            inp.key(VK_A, ctrl=True)   # 清空输入框残留
            inp.key(VK_DELETE)
            time.sleep(0.15)
            # 换行替换为空格，避免提前触发发送
            text = text.replace("\r", " ").replace("\n", " ").strip()
            # SendInput 逐字键入，key_hold/type_gap 拟人节奏；
            # 文本中的微信表情短代码（[呲牙] 等）原样键入，客户端自动渲染
            self._type_text(inp, text)
            time.sleep(random.uniform(0.3, 0.8))
            inp.key(VK_RETURN)
            time.sleep(0.8)
            return True
        except Exception as e:
            log.warning(f"逐字输入失败: {e}")
            return False

    def send_reply(self, contact: str, text: str, input_mode: str = "typing") -> bool:
        if not self.connected:
            return False
        try:
            from wechatauto.guia import quick_send
            sent = False
            if input_mode == "typing":
                sent = self._type_like_human(contact, text)
                if not sent:
                    log.warning("逐字输入不可用，回退到 quick_send")
            if not sent:
                # verify=False：禁止数据库回读确认（会触发进程内存读取）
                result = quick_send(text, contact, verify=False)
                # WxResponse 以 is_success 判真假，不能只认 is False
                if not result:
                    log.error(f"发送失败 [{contact}]: 后端返回失败 {result}")
                    return False
            log.info(f"已回复 [{contact}]: {text[:50]}...")
            return True
        except Exception as e:
            log.error(f"发送失败 [{contact}]: {e}")
            return False

    def _send_media(self, contact: str, path, kind: str) -> bool:
        """发送图片/文件（表情包走 image 通道，GIF 同理）"""
        if not self.connected:
            return False
        try:
            from wechatauto.guia import quick_send_file, quick_send_image
            p = Path(path)
            if not p.is_file():
                log.error(f"媒体文件不存在: {p}")
                return False
            fn = quick_send_image if kind == "image" else quick_send_file
            result = fn(str(p), contact, verify=False)
            if not result:
                log.error(f"媒体发送失败 [{contact}]: {result}")
                return False
            label = "图片/表情" if kind == "image" else "文件"
            log.info(f"已发送{label} [{contact}]: {p.name}")
            return True
        except Exception as e:
            log.error(f"媒体发送异常 [{contact}]: {e}")
            return False

    def send_image(self, contact: str, path) -> bool:
        return self._send_media(contact, path, "image")

    def send_file(self, contact: str, path) -> bool:
        return self._send_media(contact, path, "file")

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
            "backend": self.backend,
            "backend_info": BACKEND_INFO,
            "nickname": self.nickname,
        }
