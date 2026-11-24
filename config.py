"""
配置管理
负责加载、保存和验证配置
"""

import json
import logging
from pathlib import Path

# 项目根目录
ROOT = Path(__file__).parent

# 默认配置文件路径
CONFIG_PATH = ROOT / "config.json"

# 默认日志路径
LOG_PATH = ROOT / "logs" / "wechat.log"


def ensure_logging() -> None:
    """恢复我们的文件日志。

    wechatauto 在导入时会清空 root logger 的全部 handlers（logger.py），
    导致 logs/wechat.log 和 Web 日志页断流。每次导入 wechatauto 后调用本函数，
    把文件处理器补回来（幂等，不会重复添加）。
    """
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    target = str(LOG_PATH.resolve())
    for h in root.handlers:
        if isinstance(h, logging.FileHandler) and getattr(h, "baseFilename", "") == target:
            return
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    fh = logging.FileHandler(LOG_PATH, encoding="utf-8")
    fh.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    ))
    root.addHandler(fh)

# 默认配置
DEFAULT_CONFIG = {
    "wechat": {
        "backend": "wechatauto-replica",  # 开源逆向后端（读库解密+UIA/OCR发送）
        "window_title": "微信",
        "scan_interval": 5,  # 扫描间隔（秒）
        "contacts": [],  # 要监控的联系人列表
        "reply_all": False,  # 是否回复所有消息
        "reply_cooldown_seconds": 10,  # 同一联系人两次回复的最小间隔（秒），冷却期内消息合并回复
        "max_replies_per_hour": 60,  # 每小时回复总数上限（滚动窗口）
        "max_consecutive_failures": 3,  # 连续发送失败达到该次数自动停机
        "input_mode": "typing"  # 发送方式：typing=模拟真人逐字输入，paste=quick_send 默认发送
    },
    "ai": {
        "default_model": "deepseek",  # 默认AI模型
        "reply_mode": "direct",  # 回复模式：direct=直接调用大模型，agent=外接智能体
        "system_prompt": "你是一个友好的微信助手。根据收到的消息生成简洁、自然、有礼貌的回复。回复控制在100字以内。",  # 系统提示词
        "models": {
            "deepseek": {
                "api_key": "",
                "base_url": "https://api.deepseek.com",
                "model": "deepseek-chat"
            },
            "qianwen": {
                "api_key": "",
                "base_url": "https://dashscope.aliyuncs.com",
                "model": "qwen-turbo"
            },
            "xiaomi": {
                "api_key": "",
                "base_url": "https://api.xiaomi.com",
                "model": "MiLM"
            }
        },
        "agents": {}  # 智能体配置
    },
    "knowledge": {
        "enabled": True,   # 是否启用知识库 RAG
        "dir": "knowledge",  # 知识库目录（.md / .txt）
        "top_k": 3,        # 每次注入的最相关片段数
        "chunk_size": 400  # 切块长度（字符）
    },
    "server": {
        "host": "0.0.0.0",
        "port": 5000
    }
}


def load_config(path: Path = CONFIG_PATH) -> dict:
    """加载配置文件，不存在则创建默认配置"""
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    save_config(DEFAULT_CONFIG, path)
    return DEFAULT_CONFIG.copy()


def save_config(config: dict, path: Path = CONFIG_PATH) -> None:
    """保存配置到文件"""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def add_contact(config: dict, name: str) -> bool:
    """添加联系人到监控列表"""
    contacts = config.setdefault("wechat", {}).setdefault("contacts", [])
    if name not in contacts:
        contacts.append(name)
        save_config(config)
    return True


def remove_contact(config: dict, name: str) -> bool:
    """从监控列表移除联系人"""
    contacts = config.get("wechat", {}).get("contacts", [])
    if name in contacts:
        contacts.remove(name)
        save_config(config)
    return True
