"""
AI回复生成器
支持每个联系人的独立持久化记忆
"""

import logging
from typing import Optional

from openai import OpenAI

log = logging.getLogger(__name__)

DEFAULT_SYSTEM_PROMPT = (
    "你是一个友好的微信助手。根据收到的消息生成简洁、自然、有礼貌的回复。"
    "回复控制在100字以内。你可以参考之前的对话历史来提供更连贯的回复。"
)


class AIReplier:

    def __init__(self, config: dict, memory=None) -> None:
        self.config = config
        self.default_model = config.get("default_model", "deepseek")
        self.clients: dict[str, OpenAI] = {}
        self.system_prompt = config.get("system_prompt", DEFAULT_SYSTEM_PROMPT)
        self.memory = memory
        self._init_clients()

    def _init_clients(self) -> None:
        models = self.config.get("models", {})
        for name, cfg in models.items():
            api_key = cfg.get("api_key", "")
            if not api_key:
                log.warning(f"AI模型 [{name}] 未配置api_key，跳过")
                continue
            self.clients[name] = OpenAI(
                api_key=api_key,
                base_url=cfg.get("base_url")
            )
            log.info(f"AI模型 [{name}] 初始化成功")

    def generate(self, message: str, contact: str = "default", model_name: str = None) -> Optional[str]:
        name = model_name or self.default_model
        client = self.clients.get(name)
        if not client:
            log.error(f"AI模型 [{name}] 不可用")
            return None

        model_cfg = self.config.get("models", {}).get(name, {})
        model_id = model_cfg.get("model", "")

        messages = [{"role": "system", "content": self.system_prompt}]

        if self.memory:
            self.memory.add_message(contact, "user", message)
            history = self.memory.get_recent_messages(contact, limit=20)
            for entry in history:
                messages.append({
                    "role": entry["role"],
                    "content": entry["content"]
                })
        else:
            messages.append({"role": "user", "content": message})

        try:
            resp = client.chat.completions.create(
                model=model_id,
                messages=messages,
                temperature=0.7,
                max_tokens=300
            )
            reply = resp.choices[0].message.content

            if self.memory:
                self.memory.add_message(contact, "assistant", reply)

            log.debug(f"AI [{name}] 回复: {reply}")
            return reply
        except Exception as e:
            log.error(f"AI调用失败 [{name}]: {e}")
            return None

    def clear_history(self, contact: str = None) -> None:
        if self.memory and contact:
            self.memory.clear_contact(contact)

    def test_model(self, model_name: str = None) -> bool:
        name = model_name or self.default_model
        client = self.clients.get(name)
        if not client:
            return False

        model_cfg = self.config.get("models", {}).get(name, {})
        model_id = model_cfg.get("model", "")

        try:
            resp = client.chat.completions.create(
                model=model_id,
                messages=[{"role": "user", "content": "你好"}],
                max_tokens=50
            )
            return resp is not None and len(resp.choices) > 0
        except Exception as e:
            log.error(f"AI测试失败 [{name}]: {e}")
            return False

    def switch_model(self, model_name: str) -> bool:
        if model_name in self.clients:
            self.default_model = model_name
            log.info(f"已切换到模型 [{model_name}]")
            return True
        return False

    def get_available_models(self) -> list[str]:
        return list(self.clients.keys())
