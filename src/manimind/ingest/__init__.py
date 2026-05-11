"""输入摄取层 — PDF 解析、笔记读取、资产扫描、环境检测。"""

from dataclasses import dataclass, field
from typing import List

from .markdown_reader import MarkdownNote, MarkdownReader

__all__: list[str] = ["markdown_reader", "SourceBundle", "load_source_bundle"]


@dataclass
class SourceBundle:
    """输入摄取层的统一输出，给Explorer使用。"""
    notes: List[MarkdownNote] = field(default_factory=list)


def load_source_bundle(note_paths: List[str]) -> SourceBundle:
    result = SourceBundle()
    for path in note_paths:
        result.notes.append(MarkdownReader(path).read())
    return result
