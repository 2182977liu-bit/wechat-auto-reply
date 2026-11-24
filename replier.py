"""
AI回复生成器
支持每个联系人的独立持久化记忆
"""

import logging
from typing import Optional

from openai import OpenAI

import dispatcher

log = logging.getLogger(__name__)

DEFAULT_SYSTEM_PROMPT = (
    "你是一个友好的微信助手。根据收到的消息生成简洁、自然、有礼貌的回复。"
    "回复控制在100字以内。你可以参考之前的对话历史来提供更连贯的回复。"
)


class AIReplier:

    def __init__(self, config: dict, memory=None, knowledge=None) -> None:
        self.config = config
        self.default_model = config.get("default_model", "deepseek")
        self.clients: dict[str, OpenAI] = {}
        self.system_prompt = config.get("system_prompt", DEFAULT_SYSTEM_PROMPT)
        self.memory = memory
        self.knowledge = knowledge
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

    def _media_prompt(self) -> str:
        """注入媒体发送能力与当前素材清单，让 AI 知道能发什么、怎么发"""
        try:
            assets = dispatcher.list_assets()
        except Exception as e:
            log.warning(f"读取素材清单失败: {e}")
            return ""
        lines = [
            "",
            "【媒体回复能力】",
            "除纯文字外，你可以在回复中嵌入以下标记发送素材，标记由系统自动执行：",
            "- 发图片：[IMAGE:文件名]",
            "- 发文件：[FILE:文件名]",
            "- 发表情包：[STICKER:文件名]",
            "文字中可以直接混用微信内置表情短代码，如 [呲牙][微笑][强]。",
        ]
        labels = {"image": "图片", "file": "文件", "sticker": "表情包"}
        for kind, names in assets.items():
            if names:
                lines.append(f"当前可用{labels[kind]}素材：" + "、".join(names))
            else:
                lines.append(f"当前没有可用{labels[kind]}素材，禁止输出对应标记。")
        lines.append("仅在确有需要时使用标记，名称必须从上方清单中选取，不要编造。")
        return "\n".join(lines)

    def generate(self, message: str, contact: str = "default", model_name: str = None) -> Optional[str]:
        name = model_name or self.default_model
        client = self.clients.get(name)
        if not client:
            log.error(f"AI模型 [{name}] 不可用")
            return None

        model_cfg = self.config.get("models", {}).get(name, {})
        model_id = model_cfg.get("model", "")

        messages = [{"role": "system", "content": self.system_prompt + self._media_prompt()}]

        # 知识库 RAG：检索相关片段注入提示词
        if self.knowledge:
            try:
                hits = self.knowledge.search(message)
            except Exception as e:
                log.warning(f"知识库检索失败: {e}")
                hits = []
            if hits:
                ref = "\n\n".join(
                    f"[{h['source']}] {h['text']}" for h in hits
                )
                messages.append({
                    "role": "system",
                    "content": (
                        "以下是知识库参考资料。若资料与问题相关，请优先依据资料回答；"
                        "资料未覆盖时再按常识回答，不要编造资料中没有的事实。\n\n"
                        + ref
                    ),
                })

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
                max_tokens=500
            )
            reply = resp.choices[0].message.content

            if self.memory:
                self.memory.add_message(contact, "assistant", reply)

            log.debug(f"AI [{name}] 回复: {reply}")
            return reply
        except Exception as e:
            log.error(f"AI调用失败 [{name}]: {e}")
            return None

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
