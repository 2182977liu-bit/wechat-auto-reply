"""
微信自动回复主程序
将消息检测(Part1)和AI回复(Part2)串联起来
"""

import sys
import time
import random
import signal
import logging
import threading
from collections import deque

from config import load_config, LOG_PATH
from detector import WeChatDetector
from replier import AIReplier
from memory import ContactMemory
from knowledge import KnowledgeBase

# 日志配置
LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
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
        kb_cfg = self.config.get("knowledge", {})
        self.knowledge = KnowledgeBase(
            directory=kb_cfg.get("dir", "knowledge"),
            top_k=kb_cfg.get("top_k", 3),
            enabled=kb_cfg.get("enabled", True),
            chunk_size=kb_cfg.get("chunk_size", 400),
        )
        self.detector = WeChatDetector(self.config.get("wechat", {}))
        self.replier = AIReplier(
            self.config.get("ai", {}),
            memory=self.memory,
            knowledge=self.knowledge,
        )
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
        """主循环：检测消息 -> 合并缓冲 -> 限速回复。

        风控保护：
        - 同一联系人冷却期内多条消息合并为一次回复
        - 每小时回复总数上限（滚动窗口）
        - 连续发送失败达到上限自动停机
        """
        wc = self.config.get("wechat", {})
        interval = wc.get("scan_interval", 5)
        contacts = wc.get("contacts", [])
        cooldown = wc.get("reply_cooldown_seconds", 10)
        hourly_cap = wc.get("max_replies_per_hour", 60)
        max_failures = wc.get("max_consecutive_failures", 3)
        input_mode = wc.get("input_mode", "typing")

        pending: dict[str, list[str]] = {}
        last_reply_at: dict[str, float] = {}
        send_times: deque = deque()
        failures = 0

        log.info(f"开始监控 {len(contacts)} 个联系人（冷却{cooldown}s，每小时上限{hourly_cap}条）")
        self.detector.init_baseline(contacts)

        while self.running:
            try:
                new_msgs = self.detector.scan_contacts(contacts)
                for contact, msgs in new_msgs.items():
                    for msg in msgs:
                        if not msg.processed:
                            pending.setdefault(contact, []).append(msg.content)
                            msg.processed = True

                now = time.time()
                while send_times and now - send_times[0] > 3600:
                    send_times.popleft()

                for contact in list(pending.keys()):
                    if not self.running:
                        break
                    contents = pending.get(contact) or []
                    if not contents:
                        continue
                    if now - last_reply_at.get(contact, 0) < cooldown:
                        continue
                    if len(send_times) >= hourly_cap:
                        log.warning("已达每小时回复上限，暂缓回复")
                        break

                    merged = "\n".join(contents[-20:])
                    pending[contact] = []
                    log.info(f"收到 [{contact}] 的 {len(contents)} 条消息，合并处理")

                    reply = self.replier.generate(merged, contact=contact)
                    if not reply:
                        log.warning("AI未能生成回复")
                        continue
                    if not self.running:
                        break

                    # 模拟真人阅读思考后再回复
                    time.sleep(random.uniform(1.5, 4.0))
                    if not self.running:
                        break

                    success = self.detector.send_reply(contact, reply, input_mode=input_mode)
                    if success:
                        failures = 0
                        last_reply_at[contact] = time.time()
                        send_times.append(time.time())
                    else:
                        failures += 1
                        log.error(f"回复发送失败（连续 {failures} 次）")
                        if failures >= max_failures:
                            log.error("连续失败达到上限，自动停机保护")
                            self.stop()
                            break

                # 防止缓冲无限增长
                for c in pending:
                    if len(pending[c]) > 20:
                        pending[c] = pending[c][-20:]

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
            "available_models": self.replier.get_available_models(),
            "knowledge": self.knowledge.stats()
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
