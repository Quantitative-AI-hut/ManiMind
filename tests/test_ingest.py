"""
输入摄取组单元测试。

覆盖 A1/A2 全部模块：
  - AssetScanner (A2-1)
  - EnvReporter (A2-2)
  - load_source_bundle (A1-3)
  - MarkdownReader (A1-2，只验证可导入)
"""

import pytest
from unittest.mock import patch
from datetime import datetime


# ─── AssetScanner 测试 ───

class TestAssetScanner:

    def test_scan_returns_assetlist(self):
        """扫描正常目录应该返回 AssetList 类型。"""
        from manimind.ingest.asset_scanner import AssetScanner, AssetList
        scanner = AssetScanner()
        result = scanner.scan()
        assert isinstance(result, AssetList)

    def test_scan_has_components(self):
        """resources/ 目录下有文件，components 列表应该非空。"""
        from manimind.ingest.asset_scanner import AssetScanner
        scanner = AssetScanner()
        result = scanner.scan()
        assert len(result.components) > 0

    def test_scan_has_required_fields(self):
        """返回的 AssetList 必须有 scanned_at、components、manim_assets、references 四个字段。"""
        from manimind.ingest.asset_scanner import AssetScanner
        scanner = AssetScanner()
        result = scanner.scan()
        assert hasattr(result, "scanned_at")
        assert hasattr(result, "components")
        assert hasattr(result, "manim_assets")
        assert hasattr(result, "references")
        assert isinstance(result.scanned_at, datetime)

    def test_scan_componentinfo_fields(self):
        """components 中每个元素必须包含 path、name、category、description。"""
        from manimind.ingest.asset_scanner import AssetScanner, ComponentInfo
        scanner = AssetScanner()
        result = scanner.scan()
        for comp in result.components:
            assert isinstance(comp, ComponentInfo)
            assert hasattr(comp, "path")
            assert hasattr(comp, "name")
            assert hasattr(comp, "category")
            assert hasattr(comp, "description")

    def test_scan_path_is_relative(self):
        """ComponentInfo.path 必须以 resources/ 开头，不能是绝对路径。"""
        from manimind.ingest.asset_scanner import AssetScanner
        scanner = AssetScanner()
        result = scanner.scan()
        for comp in result.components:
            assert comp.path.startswith("resources/"), f"路径应以 resources/ 开头: {comp.path}"
            assert not comp.path.startswith("D:"), f"不应为绝对路径: {comp.path}"
            assert not comp.path.startswith("/"), f"不应以 / 开头: {comp.path}"

    def test_scan_category_valid(self):
        """ComponentInfo.category 必须是四种有效值之一。"""
        from manimind.ingest.asset_scanner import AssetScanner
        valid = {"html_template", "manim_script", "svg_asset", "other"}
        scanner = AssetScanner()
        result = scanner.scan()
        for comp in result.components:
            assert comp.category in valid, f"无效的 category: {comp.category} for {comp.name}"

    def test_scan_manim_assets_match(self):
        """manim_assets 列表中的 path 对应的 component.category 应为 manim_script。"""
        from manimind.ingest.asset_scanner import AssetScanner
        scanner = AssetScanner()
        result = scanner.scan()
        component_paths = {c.path: c.category for c in result.components}
        for path in result.manim_assets:
            assert path in component_paths
            assert component_paths[path] == "manim_script"

    def test_scan_references_match(self):
        """references 列表中的 path 对应的 component.category 应为 other。"""
        from manimind.ingest.asset_scanner import AssetScanner
        scanner = AssetScanner()
        result = scanner.scan()
        component_paths = {c.path: c.category for c in result.components}
        for path in result.references:
            assert path in component_paths
            assert component_paths[path] == "other"

    def test_graceful_degradation_missing_dir(self):
        """【优雅降级】扫描不存在的目录应返回空 AssetList，不报错。"""
        from manimind.ingest.asset_scanner import AssetScanner
        scanner = AssetScanner()
        result = scanner.scan("/nonexistent/path/xyz123")
        assert len(result.components) == 0
        assert len(result.manim_assets) == 0
        assert len(result.references) == 0
        assert isinstance(result.scanned_at, datetime)


# ─── EnvReporter 测试 ───

class TestEnvReporter:

    def test_generate_returns_envreport(self):
        """应该返回 EnvReport 类型。"""
        from manimind.ingest.env_reporter import EnvReporter, EnvReport
        reporter = EnvReporter()
        report = reporter.generate()
        assert isinstance(report, EnvReport)

    def test_generate_has_required_fields(self):
        """EnvReport 必须有 generated_at、python、node、manim、ffmpeg、overall_status、warnings。"""
        from manimind.ingest.env_reporter import EnvReporter
        reporter = EnvReporter()
        report = reporter.generate()
        assert hasattr(report, "generated_at")
        assert hasattr(report, "python")
        assert hasattr(report, "node")
        assert hasattr(report, "manim")
        assert hasattr(report, "ffmpeg")
        assert hasattr(report, "overall_status")
        assert hasattr(report, "warnings")
        assert isinstance(report.generated_at, datetime)

    def test_toolcheckresult_fields(self):
        """每个工具结果必须包含 name、available、version、path、details。"""
        from manimind.ingest.env_reporter import EnvReporter, ToolCheckResult
        reporter = EnvReporter()
        report = reporter.generate()
        for tool in [report.python, report.node, report.manim, report.ffmpeg]:
            assert isinstance(tool, ToolCheckResult)
            assert hasattr(tool, "name")
            assert hasattr(tool, "available")
            assert hasattr(tool, "version")
            assert hasattr(tool, "path")
            assert hasattr(tool, "details")
            assert isinstance(tool.available, bool)

    def test_overall_status_valid(self):
        """overall_status 必须是 'ok' 或 'warning' 或 'error'。"""
        from manimind.ingest.env_reporter import EnvReporter
        reporter = EnvReporter()
        report = reporter.generate()
        assert report.overall_status in ("ok", "warning", "error")

    @patch("manimind.bootstrap.check_tools")
    def test_all_available_gives_ok(self, mock_check_tools):
        """所有工具都可用时，overall_status 应为 ok。"""
        mock_check_tools.return_value = {
            "python": True,
            "node": True,
            "manim": True,
            "ffmpeg": True,
        }
        from manimind.ingest.env_reporter import EnvReporter
        reporter = EnvReporter()
        report = reporter.generate()
        assert report.overall_status == "ok"
        assert report.warnings == []

    @patch("manimind.bootstrap.check_tools")
    def test_anything_missing_gives_warning(self, mock_check_tools):
        """有工具不可用时，overall_status 应为 warning 且 warnings 非空。"""
        mock_check_tools.return_value = {
            "python": True,
            "node": False,
            "manim": False,
            "ffmpeg": True,
        }
        from manimind.ingest.env_reporter import EnvReporter
        reporter = EnvReporter()
        report = reporter.generate()
        assert report.overall_status == "warning"
        assert len(report.warnings) > 0


# ─── 集成测试 ───

class TestIngestIntegration:

    def test_load_source_bundle_importable(self):
        """load_source_bundle 可以正常导入。"""
        from manimind.ingest import load_source_bundle
        assert callable(load_source_bundle)

    def test_load_source_bundle_returns_sourcebundle(self):
        """load_source_bundle() 应该返回 SourceBundle 对象。"""
        from manimind.ingest import load_source_bundle, SourceBundle
        bundle = load_source_bundle()
        assert isinstance(bundle, SourceBundle)

    def test_sourcebundle_has_all_fields(self):
        """SourceBundle 必须包含 paper、notes、assets、env_report。"""
        from manimind.ingest import load_source_bundle
        bundle = load_source_bundle()
        assert hasattr(bundle, "paper")
        assert hasattr(bundle, "notes")
        assert hasattr(bundle, "assets")
        assert hasattr(bundle, "env_report")

    def test_sourcebundle_assets_is_not_none(self):
        """load 后 assets 字段应为 AssetList 对象，不能为 None。"""
        from manimind.ingest import load_source_bundle, AssetList
        bundle = load_source_bundle()
        assert bundle.assets is not None
        assert isinstance(bundle.assets, AssetList)

    def test_sourcebundle_env_report_is_not_none(self):
        """load 后 env_report 字段应为 EnvReport 对象，不能为 None。"""
        from manimind.ingest import load_source_bundle, EnvReport
        bundle = load_source_bundle()
        assert bundle.env_report is not None
        assert isinstance(bundle.env_report, EnvReport)