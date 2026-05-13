"""
资产扫描器 - 遍历 resources/ 目录，生成结构化资产清单。

严格按照 docs/agent-data-protocol.md 第 0.4 节的数据格式定义。
"""

import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class ComponentInfo:
    """单个参考资产的描述，对应协议中的 ComponentInfo。"""
    path: str
    name: str
    category: str
    description: Optional[str] = None


@dataclass
class AssetList:
    """资产扫描的完整输出，对应协议中的 AssetList。"""
    scanned_at: datetime
    components: list[ComponentInfo] = field(default_factory=list)
    manim_assets: list[str] = field(default_factory=list)
    references: list[str] = field(default_factory=list)


class AssetScanner:
    """扫描 resources/ 目录，生成资产清单。"""

    def scan(self, resources_dir: str = "resources") -> AssetList:
        resources_path = Path(resources_dir)
        components: list[ComponentInfo] = []

        # 优雅降级：目录不存在时返回空清单
        if not resources_path.exists():
            print(f"[警告] 资源目录不存在: {resources_dir}，返回空清单。")
            return AssetList(scanned_at=datetime.now())

        # 递归遍历所有文件
        for root, _, files in os.walk(resources_path):
            for file_name in files:
                full_path = Path(root) / file_name

                # 生成相对于项目根目录的路径
                try:
                    rel_path = str(full_path.relative_to(Path.cwd())).replace("\\", "/")
                except ValueError:
                    rel_path = str(full_path).replace("\\", "/")

                # 确保以 resources/ 开头
                if not rel_path.startswith("resources/"):
                    rel_path = "resources/" + rel_path.partition("resources/")[2]

                # 分类
                category = self._classify(rel_path, file_name)

                # 构建 ComponentInfo
                components.append(ComponentInfo(
                    path=rel_path,
                    name=file_name,
                    category=category,
                    description=None
                ))

        # 按类别拆分到对应字段
        manim_assets = [c.path for c in components if c.category == "manim_script"]
        references = [c.path for c in components if c.category == "other"]

        return AssetList(
            scanned_at=datetime.now(),
            components=components,
            manim_assets=manim_assets,
            references=references
        )

    @staticmethod
    def _classify(rel_path: str, file_name: str) -> str:
        """根据路径和文件名判断资产类别。"""
        lower_path = rel_path.lower()
        lower_name = file_name.lower()

        # html_template: 路径在 html-animation 目录下
        if "resources/skills/html-animation/" in lower_path:
            return "html_template"

        # manim_script: 路径在 skills/manim/ 下，且后缀为 .py 或 .md
        if "resources/skills/manim/" in lower_path:
            if lower_name.endswith(".py") or lower_name.endswith(".md"):
                return "manim_script"

        # svg_asset: 后缀为 .svg
        if lower_name.endswith(".svg"):
            return "svg_asset"

        # 其余情况归为 other
        return "other"