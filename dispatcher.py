"""
媒体回复调度：把 AI 输出拆成文本/图片/文件/表情包片段。

AI 回复中可嵌入标记（由 replier 注入的提示词约定）：
  [IMAGE:名称]   发送图片，素材目录 assets/images/
  [FILE:名称]    发送文件，素材目录 assets/files/
  [STICKER:名称] 发送表情包（GIF/图片），素材目录 stickers/

文本片段中的微信内置表情短代码（如 [呲牙][微笑]）不是标记，
保持原文随文字发送，微信客户端会渲染成对应表情。

名称支持：绝对路径 / 带扩展名的文件名 / 不带扩展名的名称（自动匹配常见扩展）。
"""

import logging
import re
from dataclasses import dataclass
from pathlib import Path

log = logging.getLogger(__name__)

ROOT = Path(__file__).parent

MEDIA_DIRS = {
    "image": ROOT / "assets" / "images",
    "file": ROOT / "assets" / "files",
    "sticker": ROOT / "stickers",
}

MEDIA_EXTS = {
    "image": [".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"],
    "sticker": [".gif", ".png", ".jpg", ".jpeg", ".webp"],
    "file": [],  # 文件不限扩展名
}

# [IMAGE:xxx] / [FILE:xxx] / [STICKER:xxx]，微信表情短代码首字母非大写英文单词不受影响
MARKER_RE = re.compile(r"\[(IMAGE|FILE|STICKER):([^\]\n]+)\]")


@dataclass
class Segment:
    kind: str      # text / image / file / sticker
    value: str     # text=文本内容；其余=素材引用


def parse_reply(reply: str) -> list[Segment]:
    """把 AI 回复按标记拆成有序片段；无标记时就是单个文本片段"""
    segments: list[Segment] = []
    pos = 0
    for m in MARKER_RE.finditer(reply):
        text = reply[pos:m.start()].strip()
        if text:
            segments.append(Segment("text", text))
        kind = m.group(1).lower()
        ref = m.group(2).strip()
        if ref:
            segments.append(Segment(kind, ref))
        pos = m.end()
    tail = reply[pos:].strip()
    if tail:
        segments.append(Segment("text", tail))
    return segments


def resolve_media(kind: str, ref: str) -> Path | None:
    """把素材引用解析成真实文件路径，找不到返回 None"""
    p = Path(ref)
    if p.is_absolute():
        return p if p.is_file() else None

    directory = MEDIA_DIRS.get(kind)
    if directory is None or not directory.is_dir():
        return None

    # 1. 精确文件名
    exact = directory / ref
    if exact.is_file():
        return exact

    # 2. 无扩展名：按常见扩展匹配
    candidates = []
    for item in directory.iterdir():
        if not item.is_file() or item.name.startswith("."):
            continue
        if item.stem == ref or item.name == ref:
            if kind == "file" or item.suffix.lower() in MEDIA_EXTS.get(kind, []):
                candidates.append(item)
    if len(candidates) == 1:
        return candidates[0]
    if candidates:
        # 多个候选时取文件名最短者（最接近精确匹配）
        return sorted(candidates, key=lambda x: len(x.name))[0]

    # 3. 唯一模糊包含匹配
    fuzzy = [
        item for item in directory.iterdir()
        if item.is_file() and ref in item.stem
        and (kind == "file" or item.suffix.lower() in MEDIA_EXTS.get(kind, []))
    ]
    if len(fuzzy) == 1:
        return fuzzy[0]
    if len(fuzzy) > 1:
        log.warning(f"素材引用 [{ref}] 匹配到 {len(fuzzy)} 个文件，无法唯一确定")
    return None


def list_assets() -> dict[str, list[str]]:
    """列出各素材目录的可用文件名（供注入 AI 提示词）"""
    result = {}
    for kind, directory in MEDIA_DIRS.items():
        if not directory.is_dir():
            result[kind] = []
            continue
        names = [
            item.name for item in sorted(directory.iterdir())
            if item.is_file() and not item.name.startswith(".")
            and item.suffix.lower() != ".md"
        ]
        result[kind] = names[:50]
    return result
