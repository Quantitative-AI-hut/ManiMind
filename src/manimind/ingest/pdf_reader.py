import os
from pypdf import PdfReader
from typing import Optional, List
from datetime import datetime
from dataclasses import dataclass

@dataclass
class PaperContent:
    path: str                               # 原始PDF路径
    exists : bool                             # 文件是否存在
    text: Optional[str] = None                        # 全文本（包括公式LaTeX）
    extracted_at : str = ""          # 提取时间
    parse_warnings: List[str] = None          # 解析警告（如编码问题、公式可能混排）

class PDFTextExtractor:
    """PDF 文本提取器（支持中文编码和 LaTeX 公式混排）
    
    功能：
        1. 检查文件是否存在
        2. 提取全文本（保留 LaTeX 公式）
        3. 记录解析警告（编码问题、公式混排等）
    """

    def __init__(self, filePath: str):
        self.path = filePath
        exists = os.path.exists(filePath)
        self.note = PaperContent(path=filePath,exists=exists)
        self.note.extracted_at = datetime.now()
        
    #return raw_text  # 返回原文本 ,相当于对文本加工
    def _fix_encoding(self, raw_text: str) -> str:
        """尝试修复编码问题（如 GBK 乱码）
        
        Args:
            raw_text: 原始提取的文本
            
        Returns:
            修复后的文本，若失败则返回原文本并记录警告
        """
        if not raw_text:
            return ""
        
        try:
            # 优先尝试 UTF-8（现代 PDF 常用）
            return raw_text.encode('latin1').decode('utf-8')
        except UnicodeDecodeError:
            try:
                # 尝试 GBK（兼容旧版中文 PDF）
                return raw_text.encode('latin1').decode('gbk')
            except UnicodeDecodeError as e:
                self.parse_warnings.append(
                    f"编码修复失败（可能非文本内容）: {str(e)[:50]}..."
                )
                return raw_text  # 返回原文本

    #主函数
    def extract_text(self) -> None:
        """提取 PDF 全文本（包括 LaTeX 公式）
        
        Raises:
            FileNotFoundError: 如果文件不存在（但已通过 self.exists 提前检查）
        """
        if not self.note.exists:
            raise FileNotFoundError(f"文件不存在: {self.note.path}")
        
        try:
            reader = PdfReader(self.note.path)
            full_text = ""
            
            for page_num, page in enumerate(reader.pages, start=1):
                raw_text = page.extract_text()  #reader内置函数，得到某一页的内容
                if not raw_text:
                    self.note.parse_warnings.append(
                        f"第 {page_num} 页: 可能包含图片/公式（无法提取为文本）"
                    )
                    continue
                
                # 修复编码并合并到全文本
                cleaned_text = self._fix_encoding(raw_text)
                full_text += cleaned_text + "\n\n"  # 页间用双换行分隔
            
            self.note.text = full_text.strip()  # 移除末尾多余换行
            
            if not self.note.text and self.note.parse_warnings:
                self.note.parse_warnings.insert(
                    0, "警告: 提取的文本为空，可能 PDF 全是图片/公式"
                )

            return self.note

        except Exception as e:
            self.note.parse_warnings.append(f"解析错误: {str(e)[:100]}...")
            self.note.text = None

            return self.note


# 使用示例
if __name__ == "__main__":
    
    extractor = PDFTextExtractor("example.pdf")
    print(extractor.extract_text())