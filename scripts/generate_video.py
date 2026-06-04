#!/usr/bin/env python3
"""Baseline renderer for graduation-video script.json.

This intentionally implements a reliable subset of the schema:
- title cards
- photos with subtitle text
- video clips with subtitle text
- simple resize/letterbox composition
- optional BGM
- optional single TTS narration track through edge-tts

Advanced fields such as layout, transition, motion, style, frame, and sound_cue are
kept in the schema for more capable renderers. This baseline renderer ignores
unsupported decorative fields rather than failing.
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
AudioFileClip = CompositeAudioClip = CompositeVideoClip = ImageClip = VideoFileClip = concatenate_videoclips = None


def ensure_render_dependencies() -> None:
    """Import heavy optional packages only when rendering, not for --help."""
    global np, Image, ImageDraw, ImageFilter, ImageFont
    global AudioFileClip, CompositeAudioClip, CompositeVideoClip, ImageClip, VideoFileClip, concatenate_videoclips
    try:
        import numpy as _np
        from PIL import Image as _Image, ImageDraw as _ImageDraw, ImageFilter as _ImageFilter, ImageFont as _ImageFont
        from moviepy.editor import (
            AudioFileClip as _AudioFileClip,
            CompositeAudioClip as _CompositeAudioClip,
            CompositeVideoClip as _CompositeVideoClip,
            ImageClip as _ImageClip,
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
    AudioFileClip, CompositeAudioClip, CompositeVideoClip = _AudioFileClip, _CompositeAudioClip, _CompositeVideoClip
    ImageClip, VideoFileClip, concatenate_videoclips = _ImageClip, _VideoFileClip, _concatenate_videoclips

    try:  # Optional HEIC support.
        from pillow_heif import register_heif_opener

        register_heif_opener()
    except Exception:
        pass


def load_font(font_path: str | None, size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [font_path, "C:/Windows/Fonts/msjh.ttc", "C:/Windows/Fonts/mingliu.ttc"]
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


def make_media_clip(item: dict[str, Any], media_root: Path, settings: dict[str, Any]) -> CompositeVideoClip:
    width, height = int(settings["width"]), int(settings["height"])
    duration = float(item.get("duration", settings.get("duration_per_image", 5)))
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
        base = ImageClip(np.array(fit_image(path, width, height))).set_duration(duration)

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


async def edge_tts_to_file(text: str, voice: str, output: Path) -> None:
    import edge_tts

    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(str(output))


def collect_narration(data: dict[str, Any]) -> str:
    parts: list[str] = []
    for scene in data.get("scenes", []):
        for item in scene.get("media", []):
            if item.get("type") == "titlecard":
                continue
            text = str(item.get("narration") or "").strip()
            if text:
                parts.append(text)
    return "\n".join(parts)


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
    clips = []
    for scene in data.get("scenes", []):
        for item in scene.get("media", []):
            if item.get("type") == "titlecard":
                clips.append(make_titlecard(item, media_root, settings["width"], settings["height"], settings["font"], settings["font_size"]))
            else:
                clips.append(make_media_clip(item, media_root, settings))
    if not clips:
        raise SystemExit("No renderable clips found.")

    video = concatenate_videoclips(clips, method="compose")
    audio_clips = []
    audio_settings = data.get("audio") or {}
    if bgm:
        bgm_clip = AudioFileClip(str(bgm)).volumex(float(audio_settings.get("bgm_volume", 0.25)))
        audio_clips.append(bgm_clip.subclip(0, min(video.duration, bgm_clip.duration)).audio_fadeout(3))

    if data.get("mode") == "voice":
        narration = collect_narration(data)
        if narration:
            with tempfile.TemporaryDirectory() as td:
                tts_path = Path(td) / "narration.mp3"
                try:
                    asyncio.run(edge_tts_to_file(narration, data.get("voice", "zh-TW-HsiaoChenNeural"), tts_path))
                    tts_clip = AudioFileClip(str(tts_path)).volumex(float(audio_settings.get("tts_volume", 1.0)))
                    audio_clips.append(tts_clip.subclip(0, min(video.duration, tts_clip.duration)))
                    if audio_clips:
                        video = video.set_audio(CompositeAudioClip(audio_clips))
                    video.write_videofile(str(output), fps=settings["fps"], codec="libx264", audio_codec="aac")
                    return
                except ImportError as exc:
                    raise SystemExit("voice mode requires edge-tts. Install it or use subtitle-only mode.") from exc
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
