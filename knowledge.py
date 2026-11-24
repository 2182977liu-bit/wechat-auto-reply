"""
本地知识库（RAG 检索层）

把 knowledge/ 目录下的 .md / .txt 文档切块，用纯 Python BM25 做关键词检索，
在生成回复前把最相关的片段注入提示词。不依赖向量模型 / 外部服务，离线可用。

用法:
    kb = KnowledgeBase("knowledge", top_k=3)
    hits = kb.search("退货政策")
    # hits: [{"text":..., "source":..., "score":...}, ...]
"""

import re
import math
import logging
from pathlib import Path

log = logging.getLogger(__name__)

_ASCII_WORD = re.compile(r"[a-z0-9]+")
_CJK = re.compile(r"[一-鿿]")


def tokenize(text: str) -> list[str]:
    """英文/数字按词，中文按单字+二元组，兼顾召回与精度"""
    text = text.lower()
    tokens = _ASCII_WORD.findall(text)
    cjk_chars = _CJK.findall(text)
    tokens.extend(cjk_chars)
    tokens.extend(a + b for a, b in zip(cjk_chars, cjk_chars[1:]))
    return tokens


def _split_chunks(text: str, chunk_size: int) -> list[str]:
    """按空行/标题切段，再按长度合并/截断"""
    raw_parts = re.split(r"\n\s*\n|(?=^#{1,6}\s)", text, flags=re.M)
    chunks: list[str] = []
    buf = ""
    for part in raw_parts:
        part = part.strip()
        if not part:
            continue
        if len(buf) + len(part) + 1 <= chunk_size:
            buf = f"{buf}\n{part}".strip()
        else:
            if buf:
                chunks.append(buf)
            while len(part) > chunk_size:
                chunks.append(part[:chunk_size])
                part = part[chunk_size:]
            buf = part
    if buf:
        chunks.append(buf)
    return chunks


class KnowledgeBase:

    def __init__(self, directory: str = "knowledge", top_k: int = 3,
                 enabled: bool = True, chunk_size: int = 400) -> None:
        self.dir = Path(directory)
        if not self.dir.is_absolute():
            self.dir = Path(__file__).parent / self.dir
        self.top_k = top_k
        self.enabled = enabled
        self.chunk_size = chunk_size
        self.chunks: list[dict] = []
        self._df: dict[str, int] = {}
        self._doc_tokens: list[list[str]] = []
        self._avgdl = 0.0
        self.reload()

    def reload(self) -> None:
        self.chunks = []
        self._df = {}
        self._doc_tokens = []
        if not self.enabled:
            return
        if not self.dir.exists():
            log.info(f"知识库目录不存在，跳过: {self.dir}")
            return
        for path in sorted(self.dir.rglob("*")):
            if path.suffix.lower() not in (".md", ".txt"):
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except Exception as e:
                log.warning(f"读取知识库文件失败 {path}: {e}")
                continue
            for chunk in _split_chunks(text, self.chunk_size):
                tokens = tokenize(chunk)
                if not tokens:
                    continue
                self.chunks.append({"text": chunk, "source": path.name})
                self._doc_tokens.append(tokens)
                for t in set(tokens):
                    self._df[t] = self._df.get(t, 0) + 1
        n = len(self._doc_tokens)
        self._avgdl = (sum(len(t) for t in self._doc_tokens) / n) if n else 0.0
        log.info(f"知识库加载完成: {n} 个片段，来自 {self.dir}")

    def search(self, query: str, top_k: int = None) -> list[dict]:
        if not self.enabled or not self.chunks:
            return []
        k = top_k or self.top_k
        q_tokens = tokenize(query)
        if not q_tokens:
            return []
        n = len(self._doc_tokens)
        k1, b = 1.5, 0.75
        scores = []
        for i, tokens in enumerate(self._doc_tokens):
            dl = len(tokens)
            tf: dict[str, int] = {}
            for t in tokens:
                tf[t] = tf.get(t, 0) + 1
            score = 0.0
            for t in q_tokens:
                if t not in tf:
                    continue
                df = self._df.get(t, 0)
                idf = math.log(1 + (n - df + 0.5) / (df + 0.5))
                denom = tf[t] + k1 * (1 - b + b * dl / (self._avgdl or 1))
                score += idf * tf[t] * (k1 + 1) / denom
            if score > 0:
                scores.append((score, i))
        scores.sort(reverse=True)
        return [
            {"text": self.chunks[i]["text"],
             "source": self.chunks[i]["source"],
             "score": round(s, 3)}
            for s, i in scores[:k]
        ]

    def stats(self) -> dict:
        return {
            "enabled": self.enabled,
            "dir": str(self.dir),
            "chunks": len(self.chunks),
        }
