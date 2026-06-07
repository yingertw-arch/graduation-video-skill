#!/usr/bin/env python3
"""Inventory school montage media folders.

Outputs JSON with supported, unsupported, warning, and privacy-risk findings.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SUPPORTED = {".jpg", ".jpeg", ".png", ".heic", ".mp4", ".mov", ".m4v"}
IGNORED_SUFFIXES = {".json", ".md", ".txt", ".srt", ".vtt", ".mp3", ".wav"}
PRIVACY_PATTERNS = [
    re.compile(r"(身分證|身份證|戶口|護照|電話|手機|地址|成績|病歷|診斷|個資|password|secret|token)", re.I),
    re.compile(r"\b[A-Z][12]\d{8}\b"),
    re.compile(r"\b09\d{8}\b"),
]


def file_hash_prefix(path: Path, limit: int = 1024 * 1024) -> str:
    h = hashlib.sha1()
    with path.open("rb") as f:
        h.update(f.read(limit))
    return h.hexdigest()


def image_taken_at(path: Path) -> str | None:
    if path.suffix.lower() not in {".jpg", ".jpeg", ".png", ".heic"}:
        return None
    try:
        from PIL import Image, ExifTags

        with Image.open(path) as img:
            exif = img.getexif()
            if not exif:
                return None
            tags = {ExifTags.TAGS.get(k, k): v for k, v in exif.items()}
            raw = tags.get("DateTimeOriginal") or tags.get("DateTime")
            if not raw:
                return None
            dt = datetime.strptime(str(raw), "%Y:%m:%d %H:%M:%S")
            return dt.isoformat()
    except Exception:
        return None


def image_info(path: Path) -> dict[str, Any]:
    if path.suffix.lower() not in {".jpg", ".jpeg", ".png", ".heic"}:
        return {}
    try:
        from PIL import Image

        with Image.open(path) as img:
            ratio = img.width / max(1, img.height)
            if ratio > 1.45:
                suggested_motion = "pan_right"
            elif ratio < 0.85:
                suggested_motion = "slow_pull_back"
            else:
                suggested_motion = "slow_push_in"
            return {
                "width": img.width,
                "height": img.height,
                "aspect_ratio": round(ratio, 3),
                "orientation": "landscape" if ratio > 1.2 else "portrait" if ratio < 0.9 else "square",
                "suggested_motion": suggested_motion,
                "quality_warnings": image_quality_warnings(img.width, img.height, ratio),
                "visual_hash": average_hash(img),
                "visual_mean": average_brightness(img),
            }
    except Exception as exc:
        return {"image_error": str(exc)}



def average_hash(img: Any, size: int = 8) -> str:
    gray = img.convert("L").resize((size, size))
    data = gray.get_flattened_data() if hasattr(gray, "get_flattened_data") else gray.getdata()
    pixels = list(data)
    avg = sum(pixels) / len(pixels)
    bits = ["1" if p >= avg else "0" for p in pixels]
    return "".join(f"{int(''.join(bits[i:i+4]), 2):x}" for i in range(0, len(bits), 4))


def average_brightness(img: Any) -> float:
    gray = img.convert("L").resize((8, 8))
    data = gray.get_flattened_data() if hasattr(gray, "get_flattened_data") else gray.getdata()
    pixels = list(data)
    return round(sum(pixels) / len(pixels), 2)


def hamming(a: str, b: str) -> int:
    return sum(x != y for x, y in zip(a, b)) + abs(len(a) - len(b))


def image_quality_warnings(width: int, height: int, ratio: float) -> list[str]:
    warnings: list[str] = []
    if width < 1280 or height < 720:
        warnings.append("low resolution for 1080p output")
    if ratio < 0.45 or ratio > 2.4:
        warnings.append("extreme aspect ratio; may crop poorly")
    return warnings


def scan(root: Path) -> dict[str, Any]:
    items: list[dict[str, Any]] = []
    unsupported: list[str] = []
    warnings: list[str] = []
    privacy: list[str] = []
    hashes: dict[str, str] = {}
    visual_hashes: list[tuple[str, str, float]] = []
    duplicate_groups: list[list[str]] = []

    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        rel = path.relative_to(root).as_posix()
        suffix = path.suffix.lower()
        stat = path.stat()

        if suffix in IGNORED_SUFFIXES:
            continue
        if suffix not in SUPPORTED:
            unsupported.append(rel)
            continue

        item: dict[str, Any] = {
            "file": rel,
            "extension": suffix,
            "size_bytes": stat.st_size,
            "modified": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
            "taken_at": image_taken_at(path),
            "warnings": [],
        }
        item.update(image_info(path))
        item["review_status"] = "candidate"

        if stat.st_size == 0:
            item["warnings"].append("empty file")
        elif stat.st_size < 20_000:
            item["warnings"].append("very small file; may be thumbnail/corrupt")

        for pattern in PRIVACY_PATTERNS:
            if pattern.search(rel):
                item["warnings"].append("filename suggests privacy-sensitive content")
                privacy.append(rel)
                break

        try:
            digest = file_hash_prefix(path)
            if digest in hashes:
                item["warnings"].append(f"possible duplicate of {hashes[digest]}")
                item["review_status"] = "skip_duplicate"
                duplicate_groups.append([hashes[digest], rel])
            else:
                hashes[digest] = rel
        except Exception as exc:
            item["warnings"].append(f"could not hash file: {exc}")

        visual_hash = item.get("visual_hash")
        if isinstance(visual_hash, str):
            visual_mean = float(item.get("visual_mean") or 0)
            if item["review_status"] != "skip_duplicate":
                for previous_hash, previous_file, previous_mean in visual_hashes:
                    if hamming(visual_hash, previous_hash) <= 5 and abs(visual_mean - previous_mean) <= 25:
                        item["warnings"].append(f"visually similar to {previous_file}")
                        item["review_status"] = "review_duplicate"
                        duplicate_groups.append([previous_file, rel])
                        break
            visual_hashes.append((visual_hash, rel, visual_mean))

        quality_warnings = item.get("quality_warnings") or []
        if quality_warnings:
            item["warnings"].extend(quality_warnings)
            if item["review_status"] == "candidate":
                item["review_status"] = "review_quality"
        if item.get("image_error"):
            item["warnings"].append(f"image could not be read: {item['image_error']}")
            item["review_status"] = "skip_unreadable"

        if item["warnings"]:
            warnings.append(rel)
        items.append(item)

    items.sort(key=lambda x: (x.get("taken_at") or x.get("modified") or "", x["file"]))
    return {
        "root": str(root),
        "supported_count": len(items),
        "unsupported_count": len(unsupported),
        "privacy_risk_count": len(set(privacy)),
        "items": items,
        "unsupported": unsupported,
        "warning_files": warnings,
        "privacy_risk_files": sorted(set(privacy)),
        "duplicate_groups": duplicate_groups,
    }


def write_review_csv(data: dict[str, Any], output: Path) -> None:
    fields = [
        "review_status",
        "file",
        "extension",
        "width",
        "height",
        "orientation",
        "size_bytes",
        "taken_at",
        "warnings",
    ]
    with output.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for item in data["items"]:
            row = {field: item.get(field, "") for field in fields}
            row["warnings"] = "; ".join(item.get("warnings") or [])
            writer.writerow(row)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("folder", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--review-csv", type=Path, help="Write a teacher-proofing CSV with candidate/skip/review status.")
    args = parser.parse_args()

    root = args.folder.resolve()
    if not root.is_dir():
        print(f"ERROR: folder not found: {root}")
        return 2

    data = scan(root)
    text = json.dumps(data, ensure_ascii=False, indent=2)
    if args.output:
        args.output.write_text(text, encoding="utf-8")
        print(f"Wrote {args.output}")
    else:
        print(text)
    if args.review_csv:
        write_review_csv(data, args.review_csv)
        print(f"Wrote {args.review_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
