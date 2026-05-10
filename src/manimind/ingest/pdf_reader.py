import re
import os
from pypdf import PdfReader
from typing import Optional, List
from datetime import datetime
from dataclasses import dataclass, field

@dataclass
class PaperContent:
    path: str                               # 原始PDF路径
    exists: bool                            # 文件是否存在
    text: Optional[str] = None              # 全文本（注意：pypdf无法直接提取LaTeX，仅为纯文本）
    extracted_at: str = ""                  # 提取时间
    parse_warnings: List[str] = field(default_factory=list)  # 解析警告

class PDFTextExtractor:
    """PDF 文本提取器
    
    注意：
    1. pypdf 仅能提取文本层内容，无法直接将图片公式转换为 LaTeX。
    2. 对于包含复杂公式的 PDF，建议后续结合 OCR 工具（如 Pix2Text, Nougat）处理。
    3. 中文乱码通常源于 PDF 字体缺少 ToUnicode 映射，单纯编码转换难以完美修复。
    """

    def __init__(self, filePath: str):
        self.path = filePath
        exists = os.path.exists(filePath)
        # 初始化数据对象
        self.note = PaperContent(
            path=filePath, 
            exists=exists, 
            extracted_at=datetime.now().isoformat()
        )

    def _fix_encoding(self,raw_text):
        try:
            # 优先尝试 UTF-8（现代 PDF 常用）
            return raw_text.encode('latin1').decode('utf-8')
        except UnicodeDecodeError:
            try:
                # 尝试 GBK（兼容旧版中文 PDF）
                return raw_text.encode('latin1').decode('gbk')
            except UnicodeDecodeError as e:
                self.note.parse_warnings.append(
                    f"编码修复失败（可能非文本内容）: {str(e)[:50]}..."
                )
                return raw_text  # 返回原文本

    def _clean_text(self, raw_text: Optional[str]) -> str:
        """清理提取的文本
        
        Args:
            raw_text: pypdf 提取的原始文本
            
        Returns:
            清理后的文本
        """

        if not raw_text.strip():
            return ""
        
        # 1. 修复编码问题
        text = self._fix_encoding(raw_text)
        
        # 2. 处理异常换行符（PDF 中常见的行中断）
        # 示例：将 "Hello\nWorld" 合并为 "Hello World"
        text = re.sub(r"(?<=[^\s])\n(?=[^\s])", " ", text)
        
        # 3. 合并多个连续空格/换行符
        text = re.sub(r"\s+", " ", text).strip()
        
        return text

    def extract_text(self) -> PaperContent:
        """提取 PDF 全文本
        
        Returns:
            PaperContent 对象，包含提取结果和警告信息
        """
        if not self.note.exists:
            self.note.parse_warnings.append(f"文件不存在: {self.note.path}")
            return self.note
        
        try:
            reader = PdfReader(self.note.path)
            full_text_parts = []
            
            for page_num, page in enumerate(reader.pages, start=1):
                try:
                    raw_text = page.extract_text()
                except Exception as e:
                    self.note.parse_warnings.append(f"第 {page_num} 页提取出错: {str(e)[:50]}")
                    continue

                if not raw_text or raw_text.strip() == "":
                    # 注意：空文本不一定意味着全是图片，也可能是排版问题
                    # 这里仅做轻微提示，避免过多噪音
                    pass 
                
                cleaned_text = self._clean_text(raw_text)
                if cleaned_text:
                    full_text_parts.append(cleaned_text)
            
            self.note.text = "\n\n".join(full_text_parts)
            
            if not self.note.text:
                self.note.parse_warnings.append("警告: 最终提取文本为空。该 PDF 可能是扫描版或字体未嵌入，建议使用 OCR 工具。")

        except Exception as e:
            self.note.parse_warnings.append(f"全局解析错误: {str(e)[:100]}")
            self.note.text = None

        return self.note

# 使用示例
if __name__ == "__main__":
    # 创建一个测试文件以便演示（实际使用时请替换为真实路径）
    extractor = PDFTextExtractor("example.pdf")
    result = extractor.extract_text()
    print(result)
