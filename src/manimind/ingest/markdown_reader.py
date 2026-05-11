import os
import re
import yaml
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class MarkdownNote:
    """Markdown 笔记数据结构"""
    path: str                                          # 原始笔记路径
    title: str = ""                                    # 标题（优先来自 YAML，其次文件名）
    front_matter: Dict[str, Any] = field(default_factory=dict)  # YAML front matter 内容
    body_text: str = ""                                # 正文文本
    images: List[str] = field(default_factory=list)    # 笔记中引用的图片路径


class MarkdownReader:
    """Markdown 笔记读取器（支持 YAML front matter 和图片提取）"""
    
    YAML_DELIMITER = "---"  # YAML front matter 分隔符
    IMAGE_PATTERN = re.compile(r"!\[.*?\]\((.*?)\)")  # 匹配 Markdown 图片语法

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.note = MarkdownNote(path=file_path)

    # return body_text, front_matter
    def _parse_yaml_front_matter(self, content: str) -> Tuple[str, Dict[str, Any]]:
        """解析 YAML front matter 和剩余正文
        
        Args:
            content: 原始文件内容
            
        Returns:
            (正文文本, YAML 数据字典)
        """
        if self.YAML_DELIMITER not in content:
            return content, {}
        
        parts = content.split(self.YAML_DELIMITER, 2)
        if len(parts) != 3:
            return content, {}  # 格式错误，返回全文和空 YAML
        
        yaml_str = parts[1].strip()
        body_text = parts[2].strip()
        
        try:
            front_matter = yaml.safe_load(yaml_str) or {}
        except yaml.YAMLError as e:
            print(f"YAML 解析错误: {e}")
            front_matter = {}
        
        return body_text, front_matter

    #return [imagePath1,...]
    def _extract_images(self, body_text: str) -> List[str]:
        """从正文中提取所有图片路径"""
        return [
            os.path.abspath(os.path.join(os.path.dirname(self.file_path), match.group(1)))
            for match in self.IMAGE_PATTERN.finditer(body_text)
        ]
    
    #这个倒是直接加上去了self.note.title
    def _infer_title(self) -> None:
        """推断标题（优先 YAML，其次文件名）"""
        fm_title = self.note.front_matter.get("title")
        if fm_title:
            self.note.title = str(fm_title)
            return

        self.note.title = os.path.splitext(os.path.basename(self.file_path))[0]

    #主函数
    def read(self) -> MarkdownNote:
        """读取并解析 Markdown 文件"""
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # 解析 YAML 和正文
            body_text, front_matter = self._parse_yaml_front_matter(content)
            self.note.front_matter = front_matter
            self.note.body_text = body_text
            
            # 提取图片路径
            self.note.images = self._extract_images(body_text)
            
            # 推断标题
            self._infer_title()
            
            return self.note
            
        except FileNotFoundError:
            print(f"错误: 文件不存在 - {self.file_path}")
            return self.note
        except Exception as e:
            print(f"解析错误: {e}")
            return self.note


# 使用示例
if __name__ == "__main__":

    # 读取笔记
    reader = MarkdownReader("test.md")
    note = reader.read()
    print(note)
