#!/usr/bin/env python3
"""Build a script.json skeleton for song-first MV mode (Mode B).

The timeline comes from timed lyrics instead of story pacing:
- LRC file (`[mm:ss.xx]lyric` lines), or
- a sections JSON (`[{"time": "0:15", "text": "..."}, ...]`) for songs without an
  LRC (e.g. most Suno graduation songs) where the teacher marks a few section times.

Each lyric line (or section) becomes one media item whose duration is the gap to
the next timestamp, so the rendered video length matches the song. The song itself
is the main audio (`audio.bgm_volume = 1.0`), shown with `mode: "subtitle-only"`.

`file` is left blank as a placeholder for the AI/teacher to fill with the photo or
clip that matches each lyric — or pass `--media-list` to fill them sequentially.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

IMAGE_MEDIA = {".jpg", ".jpeg", ".png", ".heic"}
VIDEO_MEDIA = {".mp4", ".mov", ".m4v"}
SUPPORTED_MEDIA = IMAGE_MEDIA | VIDEO_MEDIA

# generate_video.py concatenates clips with this much overlap (see its CONCAT_PADDING),
# so each clip after the first starts ~CLIP_OVERLAP earlier than its raw timeline position.
# For an MV the lyric timestamps ARE the timeline, so we pad each slot's duration by the
# overlap; after the renderer pulls each clip back, every photo lands on its lyric's start
# and the video runs the full length of the song instead of finishing early.
CLIP_OVERLAP = 0.6

LRC_STAMP = re.compile(r"\[(\d+):(\d+(?:\.\d+)?)\]")


def parse_time(value: str) -> float:
    """Accept 'm:ss(.xx)', 'h:mm:ss', or plain seconds."""
    value = str(value).strip()
    if ":" in value:
        parts = value.split(":")
        parts = [float(p) for p in parts]
        seconds = 0.0
        for p in parts:
            seconds = seconds * 60 + p
        return seconds
    return float(value)


def parse_lrc(text: str) -> list[tuple[float, str]]:
    """Return sorted (time_seconds, lyric) entries; metadata tags are ignored."""
    entries: list[tuple[float, str]] = []
    for line in text.splitlines():
        stamps = list(LRC_STAMP.finditer(line))
        if not stamps:
            continue
        lyric = LRC_STAMP.sub("", line).strip()
        for m in stamps:
            t = int(m.group(1)) * 60 + float(m.group(2))
            entries.append((t, lyric))
    entries.sort(key=lambda x: x[0])
    return entries


def parse_sections(data: Any) -> list[tuple[float, str]]:
    """Sections JSON: list of {"time": <m:ss|seconds>, "text": <lyric>}."""
    if not isinstance(data, list):
        raise SystemExit("sections JSON must be a list of {\"time\", \"text\"} objects.")
    entries: list[tuple[float, str]] = []
    for i, item in enumerate(data):
        if not isinstance(item, dict) or "time" not in item:
            raise SystemExit(f"sections[{i}] must be an object with a 'time' field.")
        entries.append((parse_time(item["time"]), str(item.get("text", "")).strip()))
    entries.sort(key=lambda x: x[0])
    return entries


def ffprobe_duration(path: Path) -> float | None:
    if shutil.which("ffprobe") is None:
        return None
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
            capture_output=True, text=True, check=True, timeout=15,
        )
        return float(result.stdout.strip())
    except Exception:
        return None


def normalize(lyric: str) -> str:
    return re.sub(r"\s+", "", re.sub(r"[^\w\u4e00-\u9fff]", "", lyric)).lower()


def find_chorus(lyrics: list[str]) -> set[str]:
    """Normalized lyric lines that repeat are treated as chorus candidates."""
    counts: dict[str, int] = {}
    for lyric in lyrics:
        key = normalize(lyric)
        if key:
            counts[key] = counts.get(key, 0) + 1
    return {key for key, n in counts.items() if n >= 2}


def build_line_segments(entries: list[tuple[float, str]], song_duration: float) -> list[dict[str, Any]]:
    chorus_keys = find_chorus([lyric for _, lyric in entries])
    segments: list[dict[str, Any]] = []
    for i, (start, lyric) in enumerate(entries):
        end = entries[i + 1][0] if i + 1 < len(entries) else song_duration
        if end <= start:
            continue
        segments.append({
            "start": start,
            "end": end,
            "lyric": lyric,
            "is_chorus": bool(lyric) and normalize(lyric) in chorus_keys,
        })
    return segments


def build_section_segments(line_segments: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Group consecutive non-empty lines into sections; empty lyrics are boundaries."""
    sections: list[dict[str, Any]] = []
    current: list[dict[str, Any]] = []

    def flush() -> None:
        if not current:
            return
        sections.append({
            "start": current[0]["start"],
            "end": current[-1]["end"],
            "lyric": "",  # multi-line section: hold one photo, no per-line subtitle
            "is_chorus": any(s["is_chorus"] for s in current),
            "lines": [s["lyric"] for s in current if s["lyric"]],
        })
        current.clear()

    for seg in line_segments:
        if not seg["lyric"]:
            flush()
            sections.append({**seg, "lines": []})  # instrumental beat
        else:
            current.append(seg)
    flush()
    return sections


def resolve_media_list(media_list: str | None, media_dir: str | None) -> list[str]:
    if media_list:
        return [m.strip() for m in media_list.split(",") if m.strip()]
    if media_dir:
        root = Path(media_dir)
        files = sorted(
            p.name for p in root.iterdir()
            if p.is_file() and p.suffix.lower() in SUPPORTED_MEDIA
        )
        return files
    return []


def build_script(
    entries: list[tuple[float, str]],
    song_duration: float,
    title: str,
    output: str,
    granularity: str,
    show_lyrics: bool,
    fadeout: float,
    media: list[str],
    width: int,
    height: int,
    fps: int,
) -> dict[str, Any]:
    line_segments = build_line_segments(entries, song_duration)
    if granularity == "section":
        segments = build_section_segments(line_segments)
    else:
        segments = line_segments

    media_items: list[dict[str, Any]] = []
    for i, seg in enumerate(segments):
        span = seg["end"] - seg["start"]
        if span <= 0:
            continue
        # Pad by the renderer's clip overlap so playback stays aligned with the lyric times.
        duration = round(span + CLIP_OVERLAP, 2)
        lyric = seg.get("lyric", "")
        item: dict[str, Any] = {
            "file": media[i % len(media)] if media else "",
            "duration": duration,
            "motion": "auto",
            "transition": "zoom_cut" if seg["is_chorus"] else "auto",
        }
        if show_lyrics and lyric:
            item["narration"] = lyric
        # Annotations (underscore-prefixed) help the AI/teacher fill in photos.
        item["_start"] = round(seg["start"], 2)
        if granularity == "section" and seg.get("lines"):
            item["_lyrics"] = seg["lines"]
        elif lyric:
            item["_lyric"] = lyric
        if seg["is_chorus"]:
            item["_section"] = "chorus"
        media_items.append(item)

    return {
        "title": title,
        "mode": "subtitle-only",
        "output": output,
        "width": width,
        "height": height,
        "fps": fps,
        "visual_profile": "warm_cinematic",
        "audio": {"bgm_volume": 1.0, "bgm_fadeout": fadeout},
        "scenes": [{"id": 1, "name": "MV", "rhythm": "lively_fast", "media": media_items}],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build an MV script.json skeleton from timed lyrics.")
    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument("--lrc", type=Path, help="LRC file with [mm:ss.xx] timestamps.")
    src.add_argument("--sections", type=Path, help="Sections JSON: [{\"time\", \"text\"}, ...].")
    parser.add_argument("--song", type=Path, help="Song file; used to auto-detect duration via ffprobe.")
    parser.add_argument("--song-duration", type=float, help="Song length in seconds (overrides ffprobe).")
    parser.add_argument("--title", default="MV")
    parser.add_argument("--output", default="mv.mp4", help="Rendered MP4 filename.")
    parser.add_argument("--granularity", choices=["line", "section"], default="line")
    parser.add_argument("--no-lyrics", action="store_true", help="Do not show lyric subtitles.")
    parser.add_argument("--fadeout", type=float, default=0.0, help="Ending BGM fade-out seconds (0 = none).")
    parser.add_argument("--media-list", help="Comma-separated media filenames to fill items sequentially.")
    parser.add_argument("--media-dir", help="Folder whose supported media fill items sequentially.")
    parser.add_argument("--width", type=int, default=1920)
    parser.add_argument("--height", type=int, default=1080)
    parser.add_argument("--fps", type=int, default=24)
    parser.add_argument("--out", type=Path, help="Where to write script.json (default: alongside the input).")
    args = parser.parse_args()

    if args.lrc:
        entries = parse_lrc(args.lrc.read_text(encoding="utf-8-sig"))
        source = args.lrc
    else:
        entries = parse_sections(json.loads(args.sections.read_text(encoding="utf-8-sig")))
        source = args.sections
    if not entries:
        raise SystemExit("No timed lyric entries found in the input.")

    song_duration = args.song_duration
    if song_duration is None and args.song:
        song_duration = ffprobe_duration(args.song.resolve())
    if song_duration is None:
        # Fallback: extend the last line by the median of earlier line durations.
        gaps = [entries[i + 1][0] - entries[i][0] for i in range(len(entries) - 1)]
        median = sorted(gaps)[len(gaps) // 2] if gaps else 4.0
        song_duration = entries[-1][0] + median
        print(f"WARNING: no song duration given; last line extended by {median:.1f}s "
              f"(pass --song or --song-duration for accuracy).")

    media = resolve_media_list(args.media_list, args.media_dir)

    script = build_script(
        entries=entries,
        song_duration=float(song_duration),
        title=args.title,
        output=args.output,
        granularity=args.granularity,
        show_lyrics=not args.no_lyrics,
        fadeout=float(args.fadeout),
        media=media,
        width=args.width,
        height=args.height,
        fps=args.fps,
    )

    out_path = args.out or source.with_name("script.json")
    out_path.write_text(json.dumps(script, ensure_ascii=False, indent=2), encoding="utf-8")
    n_items = len(script["scenes"][0]["media"])
    filled = sum(1 for m in script["scenes"][0]["media"] if m["file"])
    print(f"Wrote {out_path} — {n_items} media items, {filled} with media, "
          f"total ~{song_duration:.1f}s. "
          f"{'Fill empty file fields, then validate.' if filled < n_items else 'Validate next.'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
