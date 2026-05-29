"""
微信自动回复主程序
将消息检测(Part1)和AI回复(Part2)串联起来
"""

import sys
import time
import signal
import logging
import threading
from pathlib import Path

from config import load_config
from detector import WeChatDetector
from replier import AIReplier
from memory import ContactMemory

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_PATH, encoding="utf-8")
    ]
)
log = logging.getLogger(__name__)


class WeChatBot:
    """微信自动回复机器人"""

    def __init__(self) -> None:
        self.config = load_config()
        self.memory = ContactMemory()
        self.detector = WeChatDetector(self.config.get("wechat", {}))
        self.replier = AIReplier(self.config.get("ai", {}), memory=self.memory)
        self.running = False
        self._lock = threading.Lock()

    def start(self) -> None:
        """启动机器人"""
        log.info("正在启动微信自动回复...")

        if not self.detector.connect():
            log.error("无法连接微信，请确保微信已登录")
            return

        with self._lock:
            self.running = True

        log.info("启动成功，开始监控消息...")
        self._run_loop()

    def stop(self) -> None:
        """停止机器人"""
        with self._lock:
            if not self.running:
                return
            self.running = False
        try:
            self.detector.disconnect()
        except Exception:
            pass
        log.info("已停止")

    def _run_loop(self) -> None:
        """主循环：检测消息 -> AI回复 -> 发送"""
        interval = self.config.get("wechat", {}).get("scan_interval", 5)
        contacts = self.config.get("wechat", {}).get("contacts", [])

        log.info(f"开始监控 {len(contacts)} 个联系人")

        self.detector.init_baseline(contacts)

        while self.running:
            try:
                new_msgs = self.detector.scan_contacts(contacts)

                for contact, msgs in new_msgs.items():
                    if not self.running:
                        break
                    for msg in msgs:
                        if not self.running:
                            break
                        if msg.processed:
                            continue
                        self._handle_message(contact, msg)
                        msg.processed = True

                for _ in range(int(interval * 2)):
                    if not self.running:
                        break
                    time.sleep(0.5)
            except KeyboardInterrupt:
                self.stop()
                break
            except Exception as e:
                log.error(f"主循环异常: {e}")
                time.sleep(1)

    def _handle_message(self, contact: str, msg) -> None:
        """处理单条消息：AI生成回复 -> 发送"""
        if not self.running:
            return
        log.info(f"收到 [{contact}] 的消息: {msg.content}")

        reply = self.replier.generate(msg.content, contact=contact)
        if not reply:
            log.warning("AI未能生成回复")
            return

        if not self.running:
            return
        success = self.detector.send_reply(contact, reply)
        if success:
            log.info(f"已回复 [{contact}]: {reply[:50]}...")
        else:
            log.error("回复发送失败")

    def get_status(self) -> dict:
        """获取系统状态"""
        conn_status = self.detector.get_connection_status()
        return {
            "running": self.running,
            "connected": self.detector.connected,
            "last_error": conn_status.get("last_error", ""),
            "wechat_window_exists": conn_status.get("wechat_window_exists", False),
            "contacts": self.config.get("wechat", {}).get("contacts", []),
            "ai_model": self.replier.default_model,
            "available_models": self.replier.get_available_models()
        }


def main() -> None:
    """程序入口"""
    bot = WeChatBot()

    def on_signal(signum, frame):
        bot.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, on_signal)
    signal.signal(signal.SIGTERM, on_signal)

    # 检查是否需要启动Web界面
    if "--web" in sys.argv:
        from app import create_app
        app = create_app(bot)
        server_cfg = bot.config.get("server", {})
        host = server_cfg.get("host", "0.0.0.0")
        port = server_cfg.get("port", 5000)
        log.info(f"Web界面: http://localhost:{port}")

        # 在后台线程启动机器人
        t = threading.Thread(target=bot.start, daemon=True)
        t.start()

        app.run(host=host, port=port, debug=False)
    else:
        bot.start()


if __name__ == "__main__":
    main()
