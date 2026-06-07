#!/usr/bin/env python3
"""Baseline renderer for graduation-video script.json.

This implements a practical baseline subset of the schema:
- title cards
- photos with subtitle text
- video clips with subtitle text
- automatic photo motion selection from image aspect ratio and scene rhythm
- slow push in / pull back / pan left / pan right photo motion
- multi-photo layouts: video_wall, grid_2x2, mosaic, split_two, photo_stack
- basic transitions: fade, dissolve, slide_left/right, zoom_cut, hold
- optional BGM
- optional single TTS narration track through edge-tts

Unsupported decorative fields are ignored rather than failing.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import tempfile
from pathlib import Path
from typing import Any

np = None
Image = ImageDraw = ImageFilter = ImageFont = None
AudioFileClip = ColorClip = CompositeAudioClip = CompositeVideoClip = ImageClip = VideoClip = VideoFileClip = concatenate_videoclips = None

# Overlap (seconds) between consecutive clips during concatenation. Shared by the
# renderer and the voice-mode timeline math so per-clip narration stays aligned.
CONCAT_PADDING = -0.6


def ensure_render_dependencies() -> None:
    """Import heavy optional packages only when rendering, not for --help."""
    global np, Image, ImageDraw, ImageFilter, ImageFont
    global AudioFileClip, ColorClip, CompositeAudioClip, CompositeVideoClip, ImageClip, VideoClip, VideoFileClip, concatenate_videoclips
    try:
        import numpy as _np
        from PIL import Image as _Image, ImageDraw as _ImageDraw, ImageFilter as _ImageFilter, ImageFont as _ImageFont
        from moviepy.editor import (
            AudioFileClip as _AudioFileClip,
            ColorClip as _ColorClip,
            CompositeAudioClip as _CompositeAudioClip,
            CompositeVideoClip as _CompositeVideoClip,
            ImageClip as _ImageClip,
            VideoClip as _VideoClip,
            VideoFileClip as _VideoFileClip,
            concatenate_videoclips as _concatenate_videoclips,
        )
    except ImportError as exc:  # pragma: no cover - user environment dependent
        raise SystemExit(
            "Missing dependencies. Install in a local venv with: "
            "python -m pip install moviepy==1.0.3 pillow numpy"
        ) from exc

    np = _np
    Image, ImageDraw, ImageFilter, ImageFont = _Image, _ImageDraw, _ImageFilter, _ImageFont
    AudioFileClip, ColorClip, CompositeAudioClip, CompositeVideoClip = _AudioFileClip, _ColorClip, _CompositeAudioClip, _CompositeVideoClip
    ImageClip, VideoClip, VideoFileClip, concatenate_videoclips = _ImageClip, _VideoClip, _VideoFileClip, _concatenate_videoclips

    try:  # Optional HEIC support.
        from pillow_heif import register_heif_opener

        register_heif_opener()
    except Exception:
        pass


def load_font(font_path: str | None, size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        font_path,
        # Windows CJK fonts
        "C:/Windows/Fonts/msjh.ttc",
        "C:/Windows/Fonts/msjhbd.ttc",
        "C:/Windows/Fonts/mingliu.ttc",
        "C:/Windows/Fonts/simhei.ttf",
        # macOS CJK fonts
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Light.ttc",
        "/System/Library/Fonts/Hiragino Sans GB.ttc",
        # Linux / Noto CJK fonts
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJKtc-Regular.otf",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/arphic/uming.ttc",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


def wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_width: int) -> list[str]:
    if not text:
        return []
    lines: list[str] = []
    current = ""
    for ch in text:
        trial = current + ch
        if draw.textbbox((0, 0), trial, font=font)[2] <= max_width or not current:
            current = trial
        else:
            lines.append(current)
            current = ch
    if current:
        lines.append(current)
    return lines


def draw_centered_text(
    image: Image.Image,
    lines: list[str],
    font: ImageFont.ImageFont,
    center_y: int,
    fill: tuple[int, int, int] = (255, 255, 255),
    stroke: int = 2,
) -> None:
    draw = ImageDraw.Draw(image)
    line_heights = [draw.textbbox((0, 0), line, font=font)[3] for line in lines]
    total_h = sum(line_heights) + max(0, len(lines) - 1) * 18
    y = center_y - total_h // 2
    for line, h in zip(lines, line_heights):
        box = draw.textbbox((0, 0), line, font=font)
        x = (image.width - (box[2] - box[0])) // 2
        draw.text((x, y), line, font=font, fill=fill, stroke_width=stroke, stroke_fill=(0, 0, 0))
        y += h + 18


def make_background(path: Path | None, width: int, height: int) -> Image.Image:
    if path and path.exists():
        img = Image.open(path).convert("RGB")
        scale = max(width / img.width, height / img.height)
        resized = img.resize((int(img.width * scale), int(img.height * scale)), Image.LANCZOS)
        x = (resized.width - width) // 2
        y = (resized.height - height) // 2
        return resized.crop((x, y, x + width, y + height)).filter(ImageFilter.GaussianBlur(12))
    return Image.new("RGB", (width, height), (28, 33, 42))


def make_titlecard(item: dict[str, Any], media_root: Path, width: int, height: int, font_path: str | None, font_size: int) -> ImageClip:
    bg_file = item.get("background_file")
    bg_path = media_root / bg_file if bg_file else None
    image = make_background(bg_path, width, height)
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 70))
    image = Image.alpha_composite(image.convert("RGBA"), overlay).convert("RGB")

    title_font = load_font(font_path, int(font_size * 1.45))
    sub_font = load_font(font_path, int(font_size * 0.8))
    small_font = load_font(font_path, int(font_size * 0.55))
    draw = ImageDraw.Draw(image)

    title = str(item.get("title") or item.get("text") or "")
    subtitle = str(item.get("subtitle") or "")
    kicker = str(item.get("kicker") or "")
    y = height // 2
    draw_centered_text(image, wrap_text(draw, title, title_font, width - 300), title_font, y)
    if subtitle:
        draw_centered_text(image, wrap_text(draw, subtitle, sub_font, width - 360), sub_font, y + 120, stroke=1)
    if kicker:
        draw_centered_text(image, [kicker], small_font, y - 150, fill=(240, 220, 170), stroke=1)
    return ImageClip(np.array(image)).set_duration(float(item.get("duration", 4)))


def fit_image(path: Path, width: int, height: int) -> Image.Image:
    img = Image.open(path).convert("RGB")
    scale = min(width / img.width, height / img.height)
    resized = img.resize((int(img.width * scale), int(img.height * scale)), Image.LANCZOS)
    canvas = Image.new("RGB", (width, height), (18, 20, 24))
    canvas.paste(resized, ((width - resized.width) // 2, (height - resized.height) // 2))
    return canvas


def cover_image(img: Image.Image, width: int, height: int, scale_extra: float = 0.0) -> Image.Image:
    scale = max(width / img.width, height / img.height) * (1 + scale_extra)
    resized = img.resize((max(1, int(img.width * scale)), max(1, int(img.height * scale))), Image.LANCZOS)
    return resized


def crop_frame(resized: Image.Image, width: int, height: int, x_ratio: float, y_ratio: float) -> Image.Image:
    max_x = max(0, resized.width - width)
    max_y = max(0, resized.height - height)
    x = int(max_x * min(1, max(0, x_ratio)))
    y = int(max_y * min(1, max(0, y_ratio)))
    return resized.crop((x, y, x + width, y + height))


def infer_motion(path: Path, item: dict[str, Any], scene: dict[str, Any] | None = None) -> str:
    requested = item.get("motion") or item.get("effect")
    if requested and requested not in {"none", "auto"}:
        return {"zoom-in": "slow_push_in", "pan-right": "pan_right", "pan-left": "pan_left"}.get(requested, requested)
    rhythm = (scene or {}).get("rhythm", "")
    try:
        with Image.open(path) as img:
            ratio = img.width / max(1, img.height)
    except Exception:
        ratio = 1.6
    if rhythm in {"lively_fast", "cinematic_peak"}:
        return "slow_push_in"
    if rhythm == "emotional_pause":
        return "slow_pull_back"
    if ratio > 1.45:
        return "pan_right"
    if ratio < 0.85:
        return "slow_pull_back"
    return "slow_push_in"


def infer_transition(item: dict[str, Any], scene: dict[str, Any] | None = None, index: int = 0) -> str:
    requested = item.get("transition")
    if requested and requested != "auto":
        return requested
    rhythm = (scene or {}).get("rhythm", "")
    if rhythm == "lively_fast":
        return "slide_left" if index % 2 == 0 else "zoom_cut"
    if rhythm == "cinematic_peak":
        return "zoom_cut"
    if rhythm == "emotional_pause":
        return "fade"
    return "dissolve"


def make_motion_photo_clip(path: Path, width: int, height: int, duration: float, motion: str) -> VideoClip:
    src = Image.open(path).convert("RGB")

    def frame(t: float):
        p = 0 if duration <= 0 else min(1, max(0, t / duration))
        if motion == "slow_pull_back":
            extra = 0.14 * (1 - p)
            x_ratio = y_ratio = 0.5
        elif motion == "pan_right":
            extra = 0.08
            x_ratio, y_ratio = p, 0.5
        elif motion == "pan_left":
            extra = 0.08
            x_ratio, y_ratio = 1 - p, 0.5
        else:  # slow_push_in, parallax_soft, handheld_soft, auto fallback
            extra = 0.14 * p
            x_ratio = y_ratio = 0.5
        resized = cover_image(src, width, height, extra)
        return np.array(crop_frame(resized, width, height, x_ratio, y_ratio))

    return VideoClip(frame, duration=duration)


def image_tile(path: Path, w: int, h: int) -> Image.Image:
    img = Image.open(path).convert("RGB")
    scale = max(w / img.width, h / img.height)
    resized = img.resize((int(img.width * scale), int(img.height * scale)), Image.LANCZOS)
    x = (resized.width - w) // 2
    y = (resized.height - h) // 2
    return resized.crop((x, y, x + w, y + h))


def make_multi_photo_image(paths: list[Path], width: int, height: int, layout: str) -> Image.Image:
    canvas = Image.new("RGB", (width, height), (18, 20, 24))
    gap = 18
    if layout == "split_two" and len(paths) >= 2:
        cell_w = (width - gap) // 2
        for i, path in enumerate(paths[:2]):
            canvas.paste(image_tile(path, cell_w, height, ), (i * (cell_w + gap), 0))
        return canvas
    if layout in {"video_wall", "grid_2x2"}:
        rows, cols = 2, 2
        cell_w = (width - gap * (cols + 1)) // cols
        cell_h = (height - gap * (rows + 1)) // rows
        for i, path in enumerate(paths[:4]):
            x = gap + (i % cols) * (cell_w + gap)
            y = gap + (i // cols) * (cell_h + gap)
            canvas.paste(image_tile(path, cell_w, cell_h), (x, y))
        return canvas
    if layout == "mosaic":
        boxes = [
            (gap, gap, int(width * 0.58) - gap, height - gap),
            (int(width * 0.58), gap, width - gap, height // 2 - gap // 2),
            (int(width * 0.58), height // 2 + gap // 2, width - gap, height - gap),
        ]
        for path, (x1, y1, x2, y2) in zip(paths[:3], boxes):
            canvas.paste(image_tile(path, x2 - x1, y2 - y1), (x1, y1))
        return canvas
    # photo_stack fallback: centered overlapping cards.
    base = make_background(paths[0] if paths else None, width, height)
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 80))
    canvas = Image.alpha_composite(base.convert("RGBA"), overlay).convert("RGB")
    card_w, card_h = int(width * 0.42), int(height * 0.52)
    positions = [(-90, 30), (80, -10), (0, 60)]
    for path, (dx, dy) in zip(paths[:3], positions):
        tile = image_tile(path, card_w, card_h)
        border = Image.new("RGB", (card_w + 18, card_h + 18), (245, 245, 238))
        border.paste(tile, (9, 9))
        canvas.paste(border, ((width - border.width) // 2 + dx, (height - border.height) // 2 + dy))
    return canvas


def make_layout_clip(paths: list[Path], item: dict[str, Any], settings: dict[str, Any], scene: dict[str, Any] | None = None) -> ImageClip:
    width, height = int(settings["width"]), int(settings["height"])
    duration = float(item.get("duration", settings.get("duration_per_image", 5)))
    layout = item.get("layout") or infer_layout(paths)
    image = make_multi_photo_image(paths, width, height, layout)
    return ImageClip(np.array(image)).set_duration(duration)


def infer_layout(paths: list[Path]) -> str:
    count = len(paths)
    if count >= 4:
        return "video_wall"
    if count == 3:
        return "mosaic"
    if count == 2:
        return "split_two"
    return "full_bleed"


def subtitle_clip(text: str, duration: float, width: int, height: int, font_path: str | None, font_size: int, bottom: int) -> ImageClip | None:
    if not text.strip():
        return None
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    font = load_font(font_path, font_size)
    lines = wrap_text(draw, text, font, width - 260)[-2:]
    line_h = max(draw.textbbox((0, 0), line, font=font)[3] for line in lines)
    total_h = len(lines) * line_h + (len(lines) - 1) * 10
    y = height - bottom - total_h
    for line in lines:
        box = draw.textbbox((0, 0), line, font=font)
        x = (width - (box[2] - box[0])) // 2
        pad = 18
        draw.rounded_rectangle((x - pad, y - 8, x + (box[2] - box[0]) + pad, y + line_h + 12), radius=12, fill=(0, 0, 0, 145))
        draw.text((x, y), line, font=font, fill=(255, 255, 255), stroke_width=1, stroke_fill=(0, 0, 0))
        y += line_h + 10
    return ImageClip(np.array(img)).set_duration(duration)


def make_media_clip(
    item: dict[str, Any],
    media_root: Path,
    settings: dict[str, Any],
    scene: dict[str, Any] | None = None,
    override_duration: float | None = None,
) -> CompositeVideoClip:
    width, height = int(settings["width"]), int(settings["height"])
    duration = float(override_duration) if override_duration else float(item.get("duration", settings.get("duration_per_image", 5)))
    files = item.get("files")
    if isinstance(files, list) and files:
        paths = [media_root / str(f) for f in files]
        base = make_layout_clip(paths, item, settings, scene).set_duration(duration)
    else:
        path = media_root / item["file"]
        suffix = path.suffix.lower()
        if suffix in {".mp4", ".mov", ".m4v"}:
            base = VideoFileClip(str(path)).resize(height=height)
            if base.w > width:
                base = base.resize(width=width)
            base = base.on_color(size=(width, height), color=(18, 20, 24), pos=("center", "center"))
            base = base.subclip(0, min(duration, base.duration)).set_duration(min(duration, base.duration))
            duration = base.duration
        else:
            motion = infer_motion(path, item, scene)
            base = make_motion_photo_clip(path, width, height, duration, motion)
            effect = item.get("effect")
            if effect in {"fade-in", "blur-in", "pop-in"}:
                try:
                    base = base.fadein(min(0.6, duration / 3))
                except Exception:
                    pass

    safe = settings.get("safe_area") or {}
    sub = subtitle_clip(
        str(item.get("narration") or ""),
        duration,
        width,
        height,
        settings.get("font"),
        int(settings.get("font_size", 42)),
        int(safe.get("subtitle_bottom", 120)),
    )
    return CompositeVideoClip([base] + ([sub] if sub else []), size=(width, height)).set_duration(duration)


def apply_transitions(clips: list[Any], transitions: list[str], durations: list[float], width: int, height: int) -> Any:
    if not clips:
        raise SystemExit("No renderable clips found.")
    processed = [clips[0]]
    for i, clip in enumerate(clips[1:], start=1):
        transition = transitions[i] if i < len(transitions) else "dissolve"
        td = min(0.8, max(0.0, durations[i] if i < len(durations) else 0.5))
        if td > 0 and transition in {"slide_left", "whip_pan"}:
            clip = clip.set_position(lambda t, td=td, width=width: (int(width * max(0, 1 - min(1, t / td))), 0))
        elif td > 0 and transition == "slide_right":
            clip = clip.set_position(lambda t, td=td, width=width: (int(-width * max(0, 1 - min(1, t / td))), 0))
        elif td > 0 and transition == "zoom_cut":
            clip = clip.resize(lambda t, td=td: 1.08 - 0.08 * min(1, max(0, t / td))).set_position(("center", "center"))
        if transition in {"fade", "dissolve", "slide_left", "slide_right", "whip_pan", "zoom_cut", "flash_white", "match_cut"} and td > 0:
            try:
                clip = clip.crossfadein(td)
            except Exception:
                pass
        processed.append(clip)
    padding = CONCAT_PADDING if len(processed) > 1 else 0
    return concatenate_videoclips(processed, method="compose", padding=padding).on_color(
        size=(width, height), color=(0, 0, 0), pos=("center", "center")
    )


async def edge_tts_to_file(text: str, voice: str, output: Path) -> None:
    import edge_tts

    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(str(output))


def build_video(data: dict[str, Any], media_root: Path, bgm: Path | None, output: Path) -> None:
    ensure_render_dependencies()
    settings = {
        "width": int(data.get("width", 1920)),
        "height": int(data.get("height", 1080)),
        "fps": int(data.get("fps", 24)),
        "font": data.get("font"),
        "font_size": int(data.get("font_size", 42)),
        "duration_per_image": float(data.get("duration_per_image", 5)),
        "safe_area": data.get("safe_area") or {},
    }
    mode = data.get("mode")
    audio_settings = data.get("audio") or {}
    voice_name = data.get("voice", "zh-TW-HsiaoChenNeural")
    tts_volume = float(audio_settings.get("tts_volume", 1.0))

    with tempfile.TemporaryDirectory() as td:
        tmpdir = Path(td)

        # Pass 1: flatten scenes into an ordered list of render records so the audio
        # timeline can be aligned to the exact clip each narration belongs to.
        records: list[dict[str, Any]] = []
        media_index = 0
        for scene in data.get("scenes", []):
            for item in scene.get("media", []):
                if item.get("type") == "titlecard":
                    records.append({"kind": "titlecard", "item": item, "scene": scene})
                else:
                    records.append({"kind": "media", "item": item, "scene": scene, "media_index": media_index})
                    pause = float(item.get("pause_after", 0) or 0)
                    if pause > 0:
                        records.append({"kind": "pause", "duration": pause})
                    media_index += 1

        # Pass 2: in voice mode generate one TTS clip per narrated media item and
        # stretch still photos so they last at least as long as their narration.
        if mode == "voice":
            tts_index = 0
            for rec in records:
                if rec["kind"] != "media":
                    continue
                item = rec["item"]
                narration = str(item.get("narration") or "").strip()
                if not narration:
                    continue
                tts_path = tmpdir / f"narration_{tts_index}.mp3"
                tts_index += 1
                try:
                    asyncio.run(edge_tts_to_file(narration, voice_name, tts_path))
                except ImportError as exc:
                    raise SystemExit(
                        "voice mode requires the edge-tts Python package and internet access to Microsoft's online TTS service. "
                        "Install edge-tts in the local environment or use subtitle-only mode."
                    ) from exc
                except Exception as exc:
                    raise SystemExit(
                        "voice mode TTS generation failed. Check internet access, the selected voice name, and Microsoft's online TTS availability; "
                        "or switch the script to subtitle-only mode. "
                        f"Original error: {exc}"
                    ) from exc
                tts_clip = AudioFileClip(str(tts_path))
                rec["tts_clip"] = tts_clip
                files = item.get("files")
                file_value = item.get("file")
                is_video = (
                    not (isinstance(files, list) and files)
                    and isinstance(file_value, str)
                    and Path(file_value).suffix.lower() in {".mp4", ".mov", ".m4v"}
                )
                if not is_video:
                    base_dur = float(item.get("duration", settings["duration_per_image"]))
                    rec["override_duration"] = max(base_dur, tts_clip.duration + 0.3)

        # Pass 3: build the clips in order, recording each media clip's index so its
        # narration can be placed at the matching point on the timeline.
        clips: list[Any] = []
        transitions: list[str] = []
        transition_durations: list[float] = []
        for rec in records:
            if rec["kind"] == "titlecard":
                item = rec["item"]
                clips.append(make_titlecard(item, media_root, settings["width"], settings["height"], settings["font"], settings["font_size"]))
                transitions.append(item.get("transition", "fade"))
                transition_durations.append(float(item.get("transition_duration", 0.6)))
            elif rec["kind"] == "pause":
                clips.append(ColorClip((settings["width"], settings["height"]), color=(0, 0, 0)).set_duration(rec["duration"]))
                transitions.append("hold")
                transition_durations.append(0)
            else:
                item = rec["item"]
                rec["clip_index"] = len(clips)
                clips.append(make_media_clip(item, media_root, settings, rec["scene"], override_duration=rec.get("override_duration")))
                transitions.append(infer_transition(item, rec["scene"], rec["media_index"]))
                transition_durations.append(float(item.get("transition_duration", 0.6)))
        if not clips:
            raise SystemExit("No renderable clips found.")

        durations = [float(c.duration) for c in clips]
        video = apply_transitions(clips, transitions, transition_durations, settings["width"], settings["height"])

        audio_clips: list[Any] = []
        if bgm:
            bgm_clip = AudioFileClip(str(bgm)).volumex(float(audio_settings.get("bgm_volume", 0.25)))
            bgm_track = bgm_clip.subclip(0, min(video.duration, bgm_clip.duration))
            # MV mode wants the song to finish cleanly, so the fade is configurable; 0 = no fade.
            fadeout = float(audio_settings.get("bgm_fadeout", 3))
            if fadeout > 0:
                bgm_track = bgm_track.audio_fadeout(fadeout)
            audio_clips.append(bgm_track)

        if mode == "voice":
            # Clip k starts at sum(durations[:k]) + CONCAT_PADDING*k because the
            # concatenation overlaps every consecutive clip by the same padding.
            effective_padding = CONCAT_PADDING if len(clips) > 1 else 0.0
            starts: list[float] = []
            prefix = 0.0
            for k, d in enumerate(durations):
                starts.append(prefix + effective_padding * k)
                prefix += d
            for rec in records:
                if rec.get("kind") != "media" or "tts_clip" not in rec:
                    continue
                clip_index = rec["clip_index"]
                start = max(0.0, starts[clip_index])
                clip_dur = durations[clip_index]
                tts = rec["tts_clip"].volumex(tts_volume)
                tts = tts.subclip(0, min(tts.duration, clip_dur)).set_start(start)
                audio_clips.append(tts)

        if audio_clips:
            video = video.set_audio(CompositeAudioClip(audio_clips))
        video.write_videofile(str(output), fps=settings["fps"], codec="libx264", audio_codec="aac")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--script", required=True, type=Path)
    parser.add_argument("--media-root", type=Path)
    parser.add_argument("--bgm", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    script_path = args.script.resolve()
    media_root = (args.media_root or script_path.parent).resolve()
    data = json.loads(script_path.read_text(encoding="utf-8-sig"))
    output = args.output or (script_path.parent / data.get("output", "output.mp4"))
    build_video(data, media_root, args.bgm.resolve() if args.bgm else None, output.resolve())
    print(f"Wrote {output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
