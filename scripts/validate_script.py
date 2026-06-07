#!/usr/bin/env python3
"""Validate graduation-video script.json files before rendering."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

ALLOWED = {
    "mode": {"voice", "subtitle-only"},
    "visual_profile": {"warm_cinematic", "bright_documentary", "lively_school", "ceremony_gold", "soft_pastel", "natural"},
    "story_role": {"hook", "setup", "peak", "turn", "echo"},
    "rhythm": {"warm_slow", "lively_fast", "cinematic_peak", "emotional_pause", "documentary"},
    "layout": {"full_bleed", "photo_stack", "split_two", "scrapbook", "film_frame", "detail_focus", "letterbox_video", "video_wall", "grid_2x2", "mosaic"},
    "motion": {"auto", "slow_push_in", "slow_pull_back", "pan_right", "pan_left", "parallax_soft", "handheld_soft", "none"},
    "effect": {"auto", "zoom-in", "pan-right", "pan-left", "fade-in", "blur-in", "pop-in", "none"},
    "style": {"vibrant", "vintage", "sepia", "film", "bw", "none"},
    "frame": {"polaroid", "film_strip", "thin_white", "shadow_card", "none"},
    "transition": {"auto", "dissolve", "slide_left", "slide_right", "zoom_cut", "whip_pan", "flash_white", "match_cut", "fade", "hold"},
    "template": {"cinematic_blur", "paper_memory", "ceremony_gold", "clean_documentary", "chalkboard"},
    "chapter_style": {"lower_third_line", "date_stamp", "small_badge", "none"},
    "sound_cue": {"soft_hit", "soft_whoosh", "beat_hit", "camera_click", "none"},
}
IMAGE_MEDIA = {".jpg", ".jpeg", ".png", ".heic"}
SUPPORTED_MEDIA = IMAGE_MEDIA | {".mp4", ".mov", ".m4v"}
VIDEO_MEDIA = {".mp4", ".mov", ".m4v"}


class Reporter:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, msg: str) -> None:
        self.errors.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)

    def show(self) -> None:
        for msg in self.errors:
            print(f"ERROR: {msg}")
        for msg in self.warnings:
            print(f"WARNING: {msg}")
        if not self.errors and not self.warnings:
            print("OK: script.json passed validation.")
        elif not self.errors:
            print(f"OK: script.json has {len(self.warnings)} warning(s), no errors.")


def allowed(r: Reporter, path: str, value: Any, key: str, default_ok: bool = True) -> None:
    if value is None and default_ok:
        return
    if value not in ALLOWED[key]:
        r.error(f"{path} must be one of {sorted(ALLOWED[key])}, got {value!r}.")


def number(r: Reporter, path: str, value: Any, minimum: float | None = None, maximum: float | None = None) -> None:
    if value is None:
        return
    if not isinstance(value, (int, float)):
        r.error(f"{path} must be a number.")
        return
    if minimum is not None and value < minimum:
        r.error(f"{path} must be >= {minimum}.")
    if maximum is not None and value > maximum:
        r.error(f"{path} must be <= {maximum}.")


def media_file(
    r: Reporter,
    where: str,
    value: Any,
    media_root: Path,
    field: str = "file",
    allowed_extensions: set[str] | None = None,
) -> None:
    if not isinstance(value, str) or not value.strip():
        r.error(f"{where}.{field} must be a non-empty string.")
        return
    p = Path(value)
    if p.is_absolute():
        r.warn(f"{where}.{field} should be relative, got absolute path {value!r}.")
        full = p
    else:
        full = media_root / p
    allowed = allowed_extensions or SUPPORTED_MEDIA
    if p.suffix.lower() not in allowed:
        r.error(f"{where}.{field} has unsupported extension {p.suffix!r}; allowed: {sorted(allowed)}.")
    if not full.exists():
        r.error(f"{where}.{field} does not exist: {full}")
    elif not full.is_file():
        r.error(f"{where}.{field} is not a file: {full}")


def resolve_media_path(value: Any, media_root: Path) -> Path | None:
    if not isinstance(value, str) or not value.strip():
        return None
    p = Path(value)
    return p if p.is_absolute() else media_root / p


def ffprobe_duration(path: Path) -> float | None:
    if shutil.which("ffprobe") is None:
        return None
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                str(path),
            ],
            capture_output=True,
            text=True,
            check=True,
            timeout=15,
        )
        return float(result.stdout.strip())
    except Exception:
        return None


def validate(
    data: dict[str, Any],
    media_root: Path,
    target_duration: float | None = None,
    probe_video_durations: bool = False,
) -> Reporter:
    r = Reporter()
    for key in ("title", "mode", "output", "width", "height", "scenes"):
        if key not in data:
            r.error(f"Missing top-level field: {key}")

    if not isinstance(data.get("title"), str) or not data.get("title", "").strip():
        r.error("title must be a non-empty string.")
    allowed(r, "mode", data.get("mode"), "mode", False)
    allowed(r, "visual_profile", data.get("visual_profile"), "visual_profile")

    output = data.get("output")
    if not isinstance(output, str) or not output.strip():
        r.error("output must be a non-empty string.")
    elif Path(output).suffix.lower() != ".mp4":
        r.warn("output should usually end with .mp4.")

    for key in ("width", "height"):
        if not isinstance(data.get(key), int) or data.get(key, 0) <= 0:
            r.error(f"{key} must be a positive integer.")
    number(r, "fps", data.get("fps"), 1, 120)
    number(r, "duration_per_image", data.get("duration_per_image"), 0.1)

    audio = data.get("audio")
    if isinstance(audio, dict):
        number(r, "audio.bgm_volume", audio.get("bgm_volume"), 0, 1)
        number(r, "audio.tts_volume", audio.get("tts_volume"), 0, 2)
        number(r, "audio.bgm_fadeout", audio.get("bgm_fadeout"), 0, 30)
    elif audio is not None:
        r.error("audio must be an object when present.")

    scenes = data.get("scenes")
    if not isinstance(scenes, list) or not scenes:
        r.error("scenes must be a non-empty array.")
        return r

    seen_ids: set[Any] = set()
    used_media: dict[str, str] = {}
    estimated = 0.0
    media_count = 0
    title_count = 0
    cue_count = 0

    for si, scene in enumerate(scenes):
        sp = f"scenes[{si}]"
        if not isinstance(scene, dict):
            r.error(f"{sp} must be an object.")
            continue
        sid = scene.get("id")
        if sid in seen_ids:
            r.error(f"{sp}.id is duplicated: {sid!r}.")
        seen_ids.add(sid)
        if not isinstance(scene.get("name"), str) or not scene.get("name", "").strip():
            r.error(f"{sp}.name must be a non-empty string.")
        allowed(r, f"{sp}.story_role", scene.get("story_role"), "story_role")
        allowed(r, f"{sp}.rhythm", scene.get("rhythm"), "rhythm")
        allowed(r, f"{sp}.color_look", scene.get("color_look"), "visual_profile")

        marker = scene.get("chapter_marker")
        if isinstance(marker, dict):
            if not isinstance(marker.get("text"), str) or not marker.get("text", "").strip():
                r.error(f"{sp}.chapter_marker.text must be non-empty.")
            elif len(marker["text"]) > 24:
                r.warn(f"{sp}.chapter_marker.text is long: {marker['text']!r}.")
            allowed(r, f"{sp}.chapter_marker.style", marker.get("style"), "chapter_style")
        elif marker is not None:
            r.error(f"{sp}.chapter_marker must be an object.")

        media = scene.get("media")
        if not isinstance(media, list) or not media:
            r.error(f"{sp}.media must be a non-empty array.")
            continue

        for mi, item in enumerate(media):
            ip = f"{sp}.media[{mi}]"
            if not isinstance(item, dict):
                r.error(f"{ip} must be an object.")
                continue
            if item.get("type") == "titlecard":
                title_count += 1
                text = item.get("title") or item.get("text")
                if not isinstance(text, str) or not text.strip():
                    r.error(f"{ip} must include non-empty title or text.")
                elif len(text) > 16:
                    r.warn(f"{ip} title/text may be too long: {text!r}.")
                allowed(r, f"{ip}.template", item.get("template"), "template")
                allowed(r, f"{ip}.motion", item.get("motion"), "motion")
                allowed(r, f"{ip}.color_look", item.get("color_look"), "visual_profile")
                allowed(r, f"{ip}.sound_cue", item.get("sound_cue"), "sound_cue")
                if item.get("sound_cue") not in (None, "none"):
                    cue_count += 1
                if item.get("background_file") is not None:
                    media_file(r, ip, item["background_file"], media_root, "background_file", IMAGE_MEDIA)
                dur = item.get("duration", 3)
            else:
                media_count += 1
                files = item.get("files")
                if files is not None:
                    if not isinstance(files, list) or not files:
                        r.error(f"{ip}.files must be a non-empty array when present.")
                    else:
                        if len(files) > 6:
                            r.warn(f"{ip}.files has many images; video_wall/mosaic works best with 2-6 files.")
                        for fi, file_value in enumerate(files):
                            media_file(r, f"{ip}.files[{fi}]", file_value, media_root, "file", IMAGE_MEDIA)
                            if isinstance(file_value, str):
                                previous = used_media.get(file_value)
                                if previous and not item.get("allow_repeat"):
                                    r.warn(f"{ip}.files[{fi}] repeats {file_value!r} already used at {previous}; replace duplicates before final render unless intentional.")
                                used_media.setdefault(file_value, f"{ip}.files[{fi}]")
                else:
                    file_value = item.get("file")
                    media_file(r, ip, file_value, media_root)
                    if isinstance(file_value, str):
                        previous = used_media.get(file_value)
                        if previous and not item.get("allow_repeat"):
                            r.warn(f"{ip}.file repeats {file_value!r} already used at {previous}; replace duplicates before final render unless intentional.")
                        used_media.setdefault(file_value, f"{ip}.file")
                if data.get("mode") == "voice" and not str(item.get("narration") or "").strip():
                    r.warn(f"{ip}.narration is empty in voice mode.")
                allowed(r, f"{ip}.effect", item.get("effect"), "effect")
                allowed(r, f"{ip}.style", item.get("style"), "style")
                allowed(r, f"{ip}.frame", item.get("frame"), "frame")
                allowed(r, f"{ip}.layout", item.get("layout"), "layout")
                allowed(r, f"{ip}.motion", item.get("motion"), "motion")
                allowed(r, f"{ip}.color_look", item.get("color_look"), "visual_profile")
                allowed(r, f"{ip}.transition", item.get("transition"), "transition")
                allowed(r, f"{ip}.sound_cue", item.get("sound_cue"), "sound_cue")
                if item.get("sound_cue") not in (None, "none"):
                    cue_count += 1
                dur = item.get("duration", data.get("duration_per_image", 5))
                if probe_video_durations and files is None:
                    media_path = resolve_media_path(item.get("file"), media_root)
                    if media_path and media_path.suffix.lower() in VIDEO_MEDIA and media_path.exists():
                        real_duration = ffprobe_duration(media_path)
                        if real_duration is not None and isinstance(dur, (int, float)):
                            adjusted = min(float(dur), real_duration)
                            if adjusted != float(dur):
                                r.warn(
                                    f"{ip} estimated duration adjusted from {float(dur):.1f}s to "
                                    f"{adjusted:.1f}s because actual video is {real_duration:.1f}s."
                                )
                            dur = adjusted
                        elif real_duration is None:
                            r.warn(f"{ip} video duration could not be probed; using script duration metadata.")

            if not isinstance(dur, (int, float)) or dur <= 0:
                r.error(f"{ip}.duration must be a positive number when present.")
            else:
                estimated += float(dur)
            number(r, f"{ip}.transition_duration", item.get("transition_duration"), 0, 3)
            pause_after = item.get("pause_after")
            number(r, f"{ip}.pause_after", pause_after, 0, 5)
            if isinstance(pause_after, (int, float)):
                estimated += float(pause_after)

    if media_count == 0:
        r.warn("No photo/video media items found; only title cards are present.")
    if title_count == 0:
        r.warn("No title cards found. Consider adding opening and closing title cards.")
    if cue_count > max(8, estimated / 15):
        r.warn("Many sound cues requested; consider using cues more sparingly.")
    if estimated:
        label = "metadata + probed video durations" if probe_video_durations else "metadata"
        r.warn(f"Estimated duration from {label}: {estimated:.1f} seconds.")
    if target_duration and estimated:
        low, high = target_duration * 0.85, target_duration * 1.15
        if not (low <= estimated <= high):
            r.warn(f"Estimated duration {estimated:.1f}s is outside ±15% of target {target_duration:.1f}s.")
    return r


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("script", type=Path)
    parser.add_argument("--media-root", type=Path)
    parser.add_argument("--target-duration", type=float)
    parser.add_argument(
        "--probe-video-durations",
        action="store_true",
        help="Use ffprobe when available to estimate rendered video clips as min(script duration, real clip duration).",
    )
    args = parser.parse_args()

    script_path = args.script.resolve()
    media_root = (args.media_root or script_path.parent).resolve()
    try:
        data = json.loads(script_path.read_text(encoding="utf-8-sig"))
    except FileNotFoundError:
        print(f"ERROR: script not found: {script_path}")
        return 2
    except json.JSONDecodeError as exc:
        print(f"ERROR: invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}")
        return 2
    if not isinstance(data, dict):
        print("ERROR: top-level JSON value must be an object.")
        return 2
    reporter = validate(data, media_root, args.target_duration, args.probe_video_durations)
    reporter.show()
    return 1 if reporter.errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
