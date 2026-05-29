"""
配置管理
负责加载、保存和验证配置
"""

import json
import os
from pathlib import Path

# 项目根目录
ROOT = Path(__file__).parent

# 默认配置文件路径
CONFIG_PATH = ROOT / "config.json"

# 默认日志路径
LOG_PATH = ROOT / "logs" / "wechat.log"

# 默认配置
DEFAULT_CONFIG = {
    "wechat": {
        "window_title": "微信",
        "scan_interval": 5,  # 扫描间隔（秒）
        "contacts": [],  # 要监控的联系人列表
        "reply_all": False  # 是否回复所有消息
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


def get_ai_config(config: dict, model_name: str = None) -> dict:
    """获取指定AI模型的配置"""
    ai = config.get("ai", {})
    name = model_name or ai.get("default_model", "deepseek")
    return ai.get("models", {}).get(name, {})


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
