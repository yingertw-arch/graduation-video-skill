#!/usr/bin/env python3
"""Inventory school montage media folders.

Outputs JSON with supported, unsupported, warning, and privacy-risk findings.
"""

from __future__ import annotations

import argparse
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


def scan(root: Path) -> dict[str, Any]:
    items: list[dict[str, Any]] = []
    unsupported: list[str] = []
    warnings: list[str] = []
    privacy: list[str] = []
    hashes: dict[str, str] = {}

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
            else:
                hashes[digest] = rel
        except Exception as exc:
            item["warnings"].append(f"could not hash file: {exc}")

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
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("folder", type=Path)
    parser.add_argument("--output", type=Path)
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
