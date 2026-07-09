"""Manim rendering and frame-evidence helpers.

This module is intentionally small and orchestration-facing. It does not replace
Manim internals; it only writes generated code to predictable output paths,
invokes the Manim CLI, and extracts frame evidence for the reviewer.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
import subprocess
import sys
from typing import Sequence

from ..bootstrap import sanitize_identifier


@dataclass(slots=True)
class ManimRenderResult:
    segment_id: str
    scene_class_name: str
    code_path: str
    command: list[str]
    success: bool
    exit_code: int | None = None
    video_path: str | None = None
    stdout_tail: str = ""
    stderr_tail: str = ""
    error: str | None = None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(slots=True)
class FrameExtractionResult:
    video_path: str
    output_dir: str
    timestamps: list[float]
    frame_paths: list[str] = field(default_factory=list)
    missing_timestamps: list[float] = field(default_factory=list)
    success: bool = False
    error: str | None = None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def write_scene_code(
    scene_code: str,
    *,
    output_dir: str | Path,
    segment_id: str,
) -> Path:
    """Persist generated Manim code under ``outputs/<project_id>/manim/code``."""
    safe_segment_id = sanitize_identifier(segment_id)
    code_dir = Path(output_dir) / "manim" / "code"
    code_dir.mkdir(parents=True, exist_ok=True)
    path = code_dir / f"{safe_segment_id}.py"
    path.write_text(scene_code, encoding="utf-8")
    return path


def build_manim_render_command(
    *,
    code_path: str | Path,
    scene_class_name: str,
    output_dir: str | Path,
    segment_id: str,
    quality: str = "l",
    python_executable: str | Path | None = None,
) -> list[str]:
    """Build the CLI command used for a single Manim render."""
    safe_segment_id = sanitize_identifier(segment_id)
    py = str(python_executable or sys.executable)
    quality_flag = quality if quality.startswith("-q") else f"-q{quality.lstrip('q')}"
    media_dir = Path(output_dir) / "manim" / "media"
    return [
        py,
        "-m",
        "manim",
        "render",
        quality_flag,
        str(Path(code_path)),
        scene_class_name,
        "-o",
        safe_segment_id,
        "--media_dir",
        str(media_dir),
    ]


def render_manim_scene(
    *,
    segment_id: str,
    scene_code: str,
    scene_class_name: str,
    output_dir: str | Path,
    quality: str = "l",
    python_executable: str | Path | None = None,
    timeout_seconds: int = 180,
) -> ManimRenderResult:
    """Write and render one generated Manim scene, returning structured evidence."""
    code_path = write_scene_code(
        scene_code,
        output_dir=output_dir,
        segment_id=segment_id,
    )
    command = build_manim_render_command(
        code_path=code_path,
        scene_class_name=scene_class_name,
        output_dir=output_dir,
        segment_id=segment_id,
        quality=quality,
        python_executable=python_executable,
    )
    result = ManimRenderResult(
        segment_id=segment_id,
        scene_class_name=scene_class_name,
        code_path=str(code_path),
        command=command,
        success=False,
    )

    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
    except FileNotFoundError as exc:
        result.error = f"renderer_not_found: {exc}"
        return result
    except subprocess.TimeoutExpired as exc:
        result.error = f"render_timeout_after_{timeout_seconds}s"
        result.stdout_tail = _tail(exc.stdout)
        result.stderr_tail = _tail(exc.stderr)
        return result

    result.exit_code = completed.returncode
    result.stdout_tail = _tail(completed.stdout)
    result.stderr_tail = _tail(completed.stderr)
    if completed.returncode != 0:
        result.error = "manim_render_failed"
        return result

    video_path = _find_latest_video(Path(output_dir) / "manim" / "media", segment_id)
    if video_path is None:
        result.error = "render_succeeded_but_video_not_found"
        return result

    result.video_path = str(video_path)
    result.success = True
    return result


def extract_keyframes(
    *,
    video_path: str | Path,
    output_dir: str | Path,
    timestamps: Sequence[float] | None = None,
    ffmpeg_executable: str | Path = "ffmpeg",
    timeout_seconds: int = 30,
) -> FrameExtractionResult:
    """Extract review frames from a rendered video using ffmpeg."""
    selected_timestamps = (
        _default_keyframe_timestamps(
            video_path,
            ffmpeg_executable=ffmpeg_executable,
            timeout_seconds=timeout_seconds,
        )
        if timestamps is None
        else list(timestamps)
    )
    frame_dir = Path(output_dir)
    frame_dir.mkdir(parents=True, exist_ok=True)
    extraction = FrameExtractionResult(
        video_path=str(video_path),
        output_dir=str(frame_dir),
        timestamps=selected_timestamps,
    )

    for timestamp in selected_timestamps:
        frame_path = frame_dir / f"frame_{_timestamp_slug(timestamp)}.jpg"
        command = [
            str(ffmpeg_executable),
            "-y",
            "-ss",
            str(timestamp),
            "-i",
            str(video_path),
            "-frames:v",
            "1",
            "-update",
            "1",
            str(frame_path),
        ]
        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                check=False,
            )
        except FileNotFoundError as exc:
            extraction.error = f"ffmpeg_not_found: {exc}"
            break
        except subprocess.TimeoutExpired:
            extraction.error = f"ffmpeg_timeout_after_{timeout_seconds}s"
            break

        if completed.returncode == 0 and frame_path.exists() and frame_path.stat().st_size > 0:
            extraction.frame_paths.append(str(frame_path))
        else:
            extraction.missing_timestamps.append(timestamp)

    extraction.success = bool(extraction.frame_paths) and extraction.error is None
    return extraction


def _default_keyframe_timestamps(
    video_path: str | Path,
    *,
    ffmpeg_executable: str | Path = "ffmpeg",
    timeout_seconds: int = 30,
) -> list[float]:
    duration = _probe_video_duration(
        video_path,
        ffmpeg_executable=ffmpeg_executable,
        timeout_seconds=timeout_seconds,
    )
    if duration is None or duration <= 0:
        return [1.0, 4.0, 8.0]
    if duration < 1.2:
        return [round(max(duration * 0.5, 0.1), 2)]
    return [
        round(min(max(duration * ratio, 0.1), max(duration - 0.15, 0.1)), 2)
        for ratio in (0.08, 0.5, 0.9)
    ]


def _probe_video_duration(
    video_path: str | Path,
    *,
    ffmpeg_executable: str | Path = "ffmpeg",
    timeout_seconds: int = 30,
) -> float | None:
    ffprobe = _ffprobe_executable(ffmpeg_executable)
    command = [
        str(ffprobe),
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=nw=1:nk=1",
        str(video_path),
    ]
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None
    if completed.returncode != 0:
        return None
    try:
        return float(completed.stdout.strip())
    except ValueError:
        return None


def _ffprobe_executable(ffmpeg_executable: str | Path) -> str:
    path = Path(ffmpeg_executable)
    if path.name.lower().startswith("ffmpeg"):
        return str(path.with_name(path.name.replace("ffmpeg", "ffprobe", 1)))
    return "ffprobe"


def _find_latest_video(media_dir: Path, segment_id: str) -> Path | None:
    safe_segment_id = sanitize_identifier(segment_id)
    if not media_dir.exists():
        return None
    candidates = [
        path
        for path in media_dir.rglob("*.mp4")
        if path.stem == safe_segment_id or safe_segment_id in path.stem
    ]
    if not candidates:
        candidates = list(media_dir.rglob("*.mp4"))
    if not candidates:
        return None
    return max(candidates, key=lambda path: path.stat().st_mtime)


def _tail(value: str | bytes | None, max_chars: int = 4000) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        value = value.decode("utf-8", errors="replace")
    return value[-max_chars:]


def _timestamp_slug(timestamp: float) -> str:
    return str(timestamp).replace(".", "_").replace("-", "neg_")
