"""输入摄取层 — PDF 解析、笔记读取、资产扫描、环境检测。"""

from dataclasses import dataclass,field
from markdown_reader import MarkdownNote, MarkdownReader

from typing import  List
__all__: list[str] = ["markdown_reader"]

@dataclass
class SourceBundle:
    """输入摄取层的统一输出，给Explorer使用。"""
    #  paper: PaperContent | None      # 论文内容，若无则None      =>难得要死
    notes: List[MarkdownNote] =field(default_factory=list)        # 笔记列表

def load_source_bundle(pdPaths):
    result = SourceBundle()

    for pdPath in pdPaths:
        result.notes.append(MarkdownReader(pdPath).read())

    return result
