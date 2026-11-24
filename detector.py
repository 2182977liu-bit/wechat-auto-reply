"""
消息检测器（自研控制层，不依赖 wxauto / wxautox）

后端采用 GitHub 开源逆向项目 wechatauto-replica（Apache-2.0）:
  https://github.com/fanyuantaier/wechatauto-replica
  - 读消息：本地 SQLCipher4 数据库解密（contact.db / message_*.db），增量水位去重
  - 发消息：UIA 热激活 + 坐标/OCR 回退（wechatauto.guia.quick_send）
已在微信 4.2.0.53 真机验证。要求：微信已登录、以管理员权限运行本程序。

对外接口保持与旧版一致：connect / init_baseline / get_new_messages /
send_reply / scan_contacts / get_connection_status / disconnect。
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
FETCH_LIMIT = 100          # 每次轮询读取的最近消息条数
SEEN_CAP = 5000            # 每个联系人水位表上限

BACKEND_INFO = {
    "name": "wechatauto-replica",
    "repo": "https://github.com/fanyuantaier/wechatauto-replica",
    "license": "Apache-2.0",
    "verified_wechat": "4.2.0.53",
    "read": "本地 SQLCipher 数据库解密",
    "send": "UIA 热激活 + 坐标/OCR 回退",
}


@dataclass
class Message:
    sender: str
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    processed: bool = False


def _msg_key(m: dict):
    """跨分片唯一键：(shard, local_id, create_time)"""
    return (m.get("shard"), m.get("local_id"), m.get("create_time"))


class WeChatDetector:

    def __init__(self, config: dict) -> None:
        self.config = config
        self.db = None
        self.connected = False
        self.last_error: str = ""
        self.nickname: str = ""
        self.wxid: str = ""
        self.backend: str = BACKEND_INFO["name"]
        # 每个联系人的已读水位 {key: create_time}
        self._seen: dict[str, dict] = {}
        # 显示名 -> username 缓存
        self._username_cache: dict[str, str] = {}

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
            from wechatauto import WeChatDB
        except ImportError:
            self.last_error = "未安装后端，请运行: pip install wechatauto-replica==1.3.0.1"
            log.error(self.last_error)
            return False

        for attempt in range(1, MAX_RETRIES + 1):
            log.info(f"尝试连接微信 ({attempt}/{MAX_RETRIES})...")
            if not self._check_wechat_window():
                self.last_error = "未找到微信窗口，请先打开微信客户端并登录"
                log.error(self.last_error)
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_INTERVAL)
                continue
            try:
                self.db = WeChatDB()
                info = self.db.get_self_info() or {}
                self.wxid = info.get("wxid") or info.get("username") or ""
                self.nickname = info.get("nickname") or ""
                if not self.nickname and self.wxid:
                    try:
                        self.nickname = self.db.get_nickname(self.wxid) or ""
                    except Exception:
                        pass
                sessions = self.db.get_sessions(limit=5)
                self.connected = True
                self.last_error = ""
                log.info(
                    f"微信连接成功（用户: {self.nickname or self.wxid}），"
                    f"后端: {self.backend}，会话示例 {len(sessions)} 个"
                )
                return True
            except Exception as e:
                msg = str(e)
                if "权限" in msg or "Access" in msg or "denied" in msg.lower():
                    self.last_error = "权限不足：读取微信进程内存需要管理员权限，请以管理员身份运行"
                elif "目录" in msg or "db_dir" in msg or "登录" in msg:
                    self.last_error = "未找到微信数据库目录：请确认微信已登录，且本程序以管理员权限运行"
                else:
                    self.last_error = f"连接失败: {msg}"
                log.error(self.last_error)
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_INTERVAL)

        log.error(f"连接失败，已重试 {MAX_RETRIES} 次")
        return False

    def disconnect(self) -> None:
        self.db = None
        self.connected = False
        self._seen.clear()
        self._username_cache.clear()
        log.info("微信已断开")

    # ---- 联系人解析 ----

    def _resolve(self, contact: str) -> str:
        """把昵称/备注解析成读库所需的 username"""
        if contact in self._username_cache:
            return self._username_cache[contact]
        username = contact
        try:
            hits = self.db.search_contact(contact) or []
            exact = [
                h for h in hits
                if h.get("nickname") == contact or h.get("remark") == contact
            ]
            pick = (exact or hits)
            if pick:
                username = pick[0].get("username") or contact
        except Exception as e:
            log.debug(f"解析联系人 [{contact}] 失败，按原名使用: {e}")
        self._username_cache[contact] = username
        return username

    def _is_self(self, m: dict) -> bool:
        sender = m.get("sender_username") or ""
        return bool(self.wxid) and sender == self.wxid

    # ---- 基线 / 增量 ----

    def init_baseline(self, contacts: list[str]) -> None:
        log.info("正在初始化消息基线...")
        for contact in contacts:
            try:
                username = self._resolve(contact)
                msgs = self.db.get_messages(username, limit=FETCH_LIMIT) or []
                seen = {_msg_key(m): m.get("create_time", 0) for m in msgs}
                self._seen[contact] = seen
                log.info(f"基线 [{contact}]: 记录 {len(seen)} 条历史消息")
            except Exception as e:
                log.warning(f"基线初始化失败 [{contact}]: {e}")
                self._seen[contact] = {}
        log.info("基线初始化完成")

    def _trim_seen(self, contact: str) -> None:
        seen = self._seen.get(contact, {})
        if len(seen) > SEEN_CAP:
            items = sorted(seen.items(), key=lambda kv: kv[1] or 0)
            self._seen[contact] = dict(items[-SEEN_CAP:])

    def get_new_messages(self, contact: str) -> list[Message]:
        if not self.connected or self.db is None:
            return []
        seen = self._seen.setdefault(contact, {})
        try:
            username = self._resolve(contact)
            msgs = self.db.get_messages(username, limit=FETCH_LIMIT) or []
        except Exception as e:
            log.error(f"获取消息失败 [{contact}]: {e}")
            return []

        new_msgs: list[Message] = []
        for m in msgs:
            key = _msg_key(m)
            if key in seen:
                continue
            seen[key] = m.get("create_time", 0)
            # 自己发的、非文本消息只记水位不回复
            if self._is_self(m):
                continue
            if m.get("type") != 1:
                continue
            content = (m.get("content") or "").strip()
            if not content:
                continue
            ts = m.get("create_time")
            try:
                stamp = datetime.fromtimestamp(ts) if ts else datetime.now()
            except Exception:
                stamp = datetime.now()
            msg = Message(sender=contact, content=content, timestamp=stamp)
            new_msgs.append(msg)

        self._trim_seen(contact)
        return new_msgs

    # ---- 发送 ----

    def send_reply(self, contact: str, text: str) -> bool:
        if not self.connected or self.db is None:
            return False
        try:
            from wechatauto.guia import quick_send
            username = self._resolve(contact)
            result = quick_send(text, username, verify=True)
            if result is False:
                log.error(f"发送失败 [{contact}]: 后端返回失败")
                return False
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
            "backend": self.backend,
            "backend_info": BACKEND_INFO,
            "nickname": self.nickname,
        }
