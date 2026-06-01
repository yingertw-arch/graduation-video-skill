#!/usr/bin/env python3
"""Validate graduation-video script.json files before rendering."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ALLOWED_MODES = {"voice", "subtitle-only"}
ALLOWED_VISUAL_PROFILES = {
    "warm_cinematic",
    "bright_documentary",
    "lively_school",
    "ceremony_gold",
    "soft_pastel",
    "natural",
}
ALLOWED_STORY_ROLES = {"hook", "setup", "peak", "turn", "echo"}
ALLOWED_RHYTHMS = {
    "warm_slow",
    "lively_fast",
    "cinematic_peak",
    "emotional_pause",
    "documentary",
}
ALLOWED_LAYOUTS = {
    "full_bleed",
    "photo_stack",
    "split_two",
    "scrapbook",
    "film_frame",
    "detail_focus",
    "letterbox_video",
}
ALLOWED_MOTIONS = {
    "slow_push_in",
    "slow_pull_back",
    "pan_right",
    "pan_left",
    "parallax_soft",
    "handheld_soft",
    "none",
}
ALLOWED_EFFECTS = {"zoom-in", "pan-right", "pan-left", "none"}
ALLOWED_STYLES = {"vibrant", "vintage", "sepia", "film", "bw", "none"}
ALLOWED_FRAMES = {"polaroid", "film_strip", "thin_white", "shadow_card", "none"}
ALLOWED_TRANSITIONS = {
    "dissolve",
    "slide_left",
    "slide_right",
    "zoom_cut",
    "whip_pan",
    "flash_white",
    "match_cut",
    "fade",
}
ALLOWED_TITLE_TEMPLATES = {
    "cinematic_blur",
    "paper_memory",
    "ceremony_gold",
    "clean_documentary",
    "chalkboard",
}
ALLOWED_CHAPTER_STYLES = {"lower_third_line", "date_stamp", "small_badge", "none"}
ALLOWED_SOUND_CUES = {"soft_hit", "soft_whoosh", "beat_hit", "camera_click", "none"}
SUPPORTED_MEDIA = {".jpg", ".jpeg", ".png", ".heic", ".mp4", ".mov", ".m4v"}


class Reporter:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)

    def print(self) -> None:
        for message in self.errors:
            print(f"ERROR: {message}")
        for message in self.warnings:
            print(f"WARNING: {message}")
        if not self.errors and not self.warnings:
            print("OK: script.json passed validation.")
        elif not self.errors:
            print(f"OK: script.json has {len(self.warnings)} warning(s), no errors.")


def validate_allowed(
    reporter: Reporter,
    path: str,
    value: Any,
    allowed: set[str],
    default: str | None = None,
) -> None:
    if value is None and default is not None:
        return
    if value not in allowed:
        reporter.error(f"{path} must be one of {sorted(allowed)}, got {value!r}.")


def validate_optional_number(
    reporter: Reporter,
    path: str,
    value: Any,
    minimum: float | None = None,
    maximum: float | None = None,
) -> None:
    if value is None:
        return
    if not isinstance(value, (int, float)):
        reporter.error(f"{path} must be a number when present.")
        return
    if minimum is not None and value < minimum:
        reporter.error(f"{path} must be >= {minimum}.")
    if maximum is not None and value > maximum:
        reporter.error(f"{path} must be <= {maximum}.")


def validate_media_file(
    reporter: Reporter,
    path: str,
    file_value: Any,
    media_root: Path,
    field_name: str = "file",
) -> None:
    if not isinstance(file_value, str) or not file_value.strip():
        reporter.error(f"{path}.{field_name} must be a non-empty string.")
        return

    candidate = Path(file_value)
    if candidate.is_absolute():
        reporter.warn(f"{path}.{field_name} should be relative, got absolute path {file_value!r}.")
        full_path = candidate
    else:
        full_path = media_root / candidate

    if candidate.suffix.lower() not in SUPPORTED_MEDIA:
        reporter.error(f"{path}.{field_name} has unsupported extension {candidate.suffix!r}.")
    if not full_path.exists():
        reporter.error(f"{path}.{field_name} does not exist: {full_path}")
    elif not full_path.is_file():
        reporter.error(f"{path}.{field_name} is not a file: {full_path}")


def validate_script(data: dict[str, Any], media_root: Path) -> Reporter:
    reporter = Reporter()

    for key in ("title", "mode", "output", "width", "height", "scenes"):
        if key not in data:
            reporter.error(f"Missing top-level field: {key}")

    if not isinstance(data.get("title"), str) or not data.get("title", "").strip():
        reporter.error("title must be a non-empty string.")

    validate_allowed(reporter, "mode", data.get("mode"), ALLOWED_MODES)
    validate_allowed(
        reporter,
        "visual_profile",
        data.get("visual_profile"),
        ALLOWED_VISUAL_PROFILES,
        "natural",
    )

    audio = data.get("audio")
    if audio is not None:
        if not isinstance(audio, dict):
            reporter.error("audio must be an object when present.")
        else:
            validate_optional_number(reporter, "audio.bgm_volume", audio.get("bgm_volume"), 0, 1)
            validate_optional_number(reporter, "audio.tts_volume", audio.get("tts_volume"), 0, 2)
            if "sound_cues" in audio and not isinstance(audio.get("sound_cues"), bool):
                reporter.error("audio.sound_cues must be a boolean when present.")

    safe_area = data.get("safe_area")
    if safe_area is not None:
        if not isinstance(safe_area, dict):
            reporter.error("safe_area must be an object when present.")
        else:
            validate_optional_number(reporter, "safe_area.subtitle_bottom", safe_area.get("subtitle_bottom"), 0)
            validate_optional_number(reporter, "safe_area.title_margin", safe_area.get("title_margin"), 0)

    output = data.get("output")
    if not isinstance(output, str) or not output.strip():
        reporter.error("output must be a non-empty string.")
    elif Path(output).suffix.lower() != ".mp4":
        reporter.warn("output should usually end with .mp4.")

    for key in ("width", "height"):
        if not isinstance(data.get(key), int) or data.get(key, 0) <= 0:
            reporter.error(f"{key} must be a positive integer.")

    duration_per_image = data.get("duration_per_image")
    if duration_per_image is not None and (
        not isinstance(duration_per_image, (int, float)) or duration_per_image <= 0
    ):
        reporter.error("duration_per_image must be a positive number when present.")

    scenes = data.get("scenes")
    if not isinstance(scenes, list) or not scenes:
        reporter.error("scenes must be a non-empty array.")
        return reporter

    seen_scene_ids: set[Any] = set()
    media_count = 0
    titlecard_count = 0
    estimated_seconds = 0.0

    for scene_index, scene in enumerate(scenes):
        scene_path = f"scenes[{scene_index}]"
        if not isinstance(scene, dict):
            reporter.error(f"{scene_path} must be an object.")
            continue

        scene_id = scene.get("id")
        if scene_id in seen_scene_ids:
            reporter.error(f"{scene_path}.id is duplicated: {scene_id!r}.")
        seen_scene_ids.add(scene_id)

        if not isinstance(scene.get("name"), str) or not scene.get("name", "").strip():
            reporter.error(f"{scene_path}.name must be a non-empty string.")

        validate_allowed(
            reporter,
            f"{scene_path}.story_role",
            scene.get("story_role"),
            ALLOWED_STORY_ROLES,
            "setup",
        )
        validate_allowed(
            reporter,
            f"{scene_path}.rhythm",
            scene.get("rhythm"),
            ALLOWED_RHYTHMS,
            "warm_slow",
        )
        validate_allowed(
            reporter,
            f"{scene_path}.color_look",
            scene.get("color_look"),
            ALLOWED_VISUAL_PROFILES,
            "natural",
        )

        chapter_marker = scene.get("chapter_marker")
        if chapter_marker is not None:
            if not isinstance(chapter_marker, dict):
                reporter.error(f"{scene_path}.chapter_marker must be an object when present.")
            else:
                marker_text = chapter_marker.get("text")
                if not isinstance(marker_text, str) or not marker_text.strip():
                    reporter.error(f"{scene_path}.chapter_marker.text must be a non-empty string.")
                elif len(marker_text) > 24:
                    reporter.warn(f"{scene_path}.chapter_marker.text is long: {marker_text!r}.")
                validate_allowed(
                    reporter,
                    f"{scene_path}.chapter_marker.style",
                    chapter_marker.get("style"),
                    ALLOWED_CHAPTER_STYLES,
                    "lower_third_line",
                )

        media_items = scene.get("media")
        if not isinstance(media_items, list) or not media_items:
            reporter.error(f"{scene_path}.media must be a non-empty array.")
            continue

        for media_index, item in enumerate(media_items):
            item_path = f"{scene_path}.media[{media_index}]"
            if not isinstance(item, dict):
                reporter.error(f"{item_path} must be an object.")
                continue

            if item.get("type") == "titlecard":
                titlecard_count += 1
                title = item.get("title")
                text = item.get("text")
                if title is not None and not isinstance(title, str):
                    reporter.error(f"{item_path}.title must be a string when present.")
                if text is not None and not isinstance(text, str):
                    reporter.error(f"{item_path}.text must be a string when present.")
                if not (isinstance(title, str) and title.strip()) and not (
                    isinstance(text, str) and text.strip()
                ):
                    reporter.error(f"{item_path} must include non-empty title or text.")
                display_text = title if isinstance(title, str) and title.strip() else text
                if isinstance(display_text, str) and len(display_text) > 12:
                    reporter.warn(f"{item_path} title/text is longer than 12 characters: {display_text!r}.")
                validate_allowed(
                    reporter,
                    f"{item_path}.template",
                    item.get("template"),
                    ALLOWED_TITLE_TEMPLATES,
                    "cinematic_blur",
                )
                background_file = item.get("background_file")
                if background_file is not None:
                    validate_media_file(
                        reporter,
                        item_path,
                        background_file,
                        media_root,
                        "background_file",
                    )
                validate_allowed(
                    reporter,
                    f"{item_path}.motion",
                    item.get("motion"),
                    ALLOWED_MOTIONS,
                    "slow_push_in",
                )
                validate_allowed(
                    reporter,
                    f"{item_path}.color_look",
                    item.get("color_look"),
                    ALLOWED_VISUAL_PROFILES,
                    "natural",
                )
                validate_allowed(
                    reporter,
                    f"{item_path}.sound_cue",
                    item.get("sound_cue"),
                    ALLOWED_SOUND_CUES,
                    "none",
                )
                duration = item.get("duration", 3)
                if not isinstance(duration, (int, float)) or duration <= 0:
                    reporter.error(f"{item_path}.duration must be a positive number.")
                else:
                    if duration < 4 and item.get("template") is not None:
                        reporter.warn(f"{item_path}.duration is short for a motion title card.")
                    estimated_seconds += float(duration)
                continue

            media_count += 1
            validate_media_file(reporter, item_path, item.get("file"), media_root)

            narration = item.get("narration")
            if narration is not None and not isinstance(narration, str):
                reporter.error(f"{item_path}.narration must be a string when present.")
            elif data.get("mode") == "voice" and not (narration or "").strip():
                reporter.warn(f"{item_path}.narration is empty in voice mode.")

            validate_allowed(reporter, f"{item_path}.effect", item.get("effect"), ALLOWED_EFFECTS, "zoom-in")
            validate_allowed(reporter, f"{item_path}.style", item.get("style"), ALLOWED_STYLES, "none")
            validate_allowed(reporter, f"{item_path}.frame", item.get("frame"), ALLOWED_FRAMES, "none")
            validate_allowed(reporter, f"{item_path}.layout", item.get("layout"), ALLOWED_LAYOUTS, "full_bleed")
            validate_allowed(reporter, f"{item_path}.motion", item.get("motion"), ALLOWED_MOTIONS, "slow_push_in")
            validate_allowed(
                reporter,
                f"{item_path}.color_look",
                item.get("color_look"),
                ALLOWED_VISUAL_PROFILES,
                "natural",
            )
            validate_allowed(
                reporter,
                f"{item_path}.sound_cue",
                item.get("sound_cue"),
                ALLOWED_SOUND_CUES,
                "none",
            )
            validate_allowed(
                reporter,
                f"{item_path}.transition",
                item.get("transition"),
                ALLOWED_TRANSITIONS,
                "fade",
            )

            duration = item.get("duration", duration_per_image or 5)
            if not isinstance(duration, (int, float)) or duration <= 0:
                reporter.error(f"{item_path}.duration must be a positive number when present.")
            else:
                estimated_seconds += float(duration)

    if media_count == 0:
        reporter.warn("No photo/video media items were found; only title cards are present.")
    if titlecard_count == 0:
        reporter.warn("No title cards found. Consider adding opening and closing title cards.")
    if estimated_seconds:
        reporter.warn(f"Estimated duration from script metadata: {estimated_seconds:.1f} seconds.")

    return reporter


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a graduation-video script.json file.")
    parser.add_argument("script", type=Path, help="Path to script.json")
    parser.add_argument(
        "--media-root",
        type=Path,
        default=None,
        help="Folder containing referenced media files. Defaults to the script folder.",
    )
    args = parser.parse_args()

    script_path = args.script.resolve()
    media_root = (args.media_root or script_path.parent).resolve()

    try:
        with script_path.open("r", encoding="utf-8-sig") as handle:
            data = json.load(handle)
    except FileNotFoundError:
        print(f"ERROR: script not found: {script_path}")
        return 2
    except json.JSONDecodeError as exc:
        print(f"ERROR: invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}")
        return 2

    if not isinstance(data, dict):
        print("ERROR: top-level JSON value must be an object.")
        return 2

    reporter = validate_script(data, media_root)
    reporter.print()
    return 1 if reporter.errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
