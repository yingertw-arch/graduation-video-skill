# Graduation Video Skill

Turn a folder of school photos and clips into a polished, narrated or subtitled MP4
montage — graduation ceremonies, teaching records, achievement showcases, school
anniversaries, field trips, and class events.

Two ways to drive the timeline:

- **Mode A — material-first (default):** photos/clips drive the story; you write the
  narration/subtitles and add background music afterward.
- **Mode B — song-first MV:** give a song plus timed lyrics (LRC or a few section times) and
  the lyric timeline becomes the skeleton — each lyric line/section is matched to a photo or
  clip, the chorus gets your hero shots, and the song itself is the main audio. See
  [`references/mv-mode.md`](references/mv-mode.md).

The skill is driven by an AI agent (see [`SKILL.md`](SKILL.md)), but the bundled
Python scripts can also be run directly: inventory media, validate a `script.json`,
and render the final video.

## What you need

| Tool | Required for | Install |
|------|--------------|---------|
| Python 3.9+ | everything | python.org |
| FFmpeg / ffprobe | rendering + QA | system install (see below) |
| moviepy, Pillow, numpy | rendering | `pip install -r requirements.txt` |
| edge-tts + internet | `voice` mode TTS | `pip install edge-tts` |
| pillow-heif | `.heic` photos | `pip install pillow-heif` |

`voice` mode uses Microsoft's online TTS through the `edge-tts` package — it needs the
package and internet access, **not** the Edge browser. If it is unavailable, use
`subtitle-only` mode.

## Install

```bash
# 1. Create a local virtual environment
python -m venv .venv

# Windows
.\.venv\Scripts\python -m pip install -r requirements.txt
# macOS / Linux
./.venv/bin/python -m pip install -r requirements.txt

# 2. Install FFmpeg (system dependency, not pip)
#   Windows: winget install Gyan.FFmpeg
#   macOS:   brew install ffmpeg
#   Linux:   sudo apt-get install ffmpeg

# 3. Optional extras
pip install edge-tts pillow-heif
```

## Minimal example

Create `materials/script.json` (subtitle-only, so no TTS/internet needed):

```json
{
  "title": "Demo",
  "mode": "subtitle-only",
  "output": "demo.mp4",
  "width": 1920,
  "height": 1080,
  "scenes": [
    {
      "id": 0,
      "name": "Opening",
      "media": [{"type": "titlecard", "text": "我們畢業了", "duration": 3}]
    },
    {
      "id": 1,
      "name": "Photos",
      "media": [
        {"file": "IMG_001.jpg", "narration": "難忘的一天", "duration": 5}
      ]
    }
  ]
}
```

Render it:

```bash
python scripts/generate_video.py --script materials/script.json --media-root materials
```

The MP4 is written next to the script (or use `--output`).

## Full materials → MP4 workflow

1. **Inventory** the folder (sorts by date, flags tiny/duplicate/privacy-risk files):
   ```bash
   python scripts/inventory_media.py materials --output materials/media_inventory.json --review-csv materials/media_review.csv
   ```
2. **Plan & write** `script.json` — see [`references/script-json.md`](references/script-json.md)
   for the schema and [`references/pro-design.md`](references/pro-design.md) for visual presets.
3. **Validate** before rendering:
   ```bash
   python scripts/validate_script.py materials/script.json --media-root materials --target-duration 120 --probe-video-durations
   ```
4. **(Optional) Background music** — generate a Suno prompt from the approved script
   (prompts in [`references/video-generation.md`](references/video-generation.md)),
   then drop the MP3 into the materials folder.
5. **Render**:
   ```bash
   python scripts/generate_video.py --draft --script materials/script.json --media-root materials --bgm materials/music.mp3 --output materials/draft.mp4
   # After proofreading/approval:
   python scripts/generate_video.py --script materials/script.json --media-root materials --bgm materials/music.mp3
   ```
6. **QA** the result:
   ```bash
   ffprobe -v error -show_entries format=duration -show_streams materials/demo.mp4
   ```

Full cross-platform commands are in [`references/video-generation.md`](references/video-generation.md).

## Song-first MV example (Mode B)

Given a song and an LRC (or section times), build a `script.json` whose length matches the song:

```bash
python scripts/lyrics_to_script.py \
  --lrc materials/song.lrc \
  --song materials/song.mp3 \
  --granularity line \
  --out materials/script.json
```

Each lyric line becomes a media slot with a blank `file` placeholder (chorus slots are marked);
fill each with a matching photo or clip — or pre-fill with `--media-dir materials` — then validate
and render with the song as the main audio:

```bash
python scripts/generate_video.py --script materials/script.json --media-root materials --bgm materials/song.mp3
```

Set `audio.bgm_fadeout` to `0` (the MV default) to let the song finish cleanly. Full details:
[`references/mv-mode.md`](references/mv-mode.md).

## Modes

- **`voice`** — each narrated photo gets its own TTS clip; still photos are
  automatically stretched so they last at least as long as their narration, keeping
  audio aligned with the picture. Requires `edge-tts` + internet.
- **`subtitle-only`** — burned-in subtitles, fixed per-photo durations, no TTS.

## Notes & limits

- Default output: 1920×1080 MP4, 24 fps.
- The bundled renderer is a **deterministic baseline**. It supports title cards,
  per-photo Ken Burns motion, multi-photo layouts (video_wall / grid_2x2 / mosaic /
  split_two / photo_stack), basic transitions, beat pauses, BGM, and per-clip TTS.
  Photo `style` filters are rendered for stills and multi-photo layouts; transition effects are intentionally restrained for smoother playback. Some advanced decorative schema fields are still accepted by the validator but may be approximated by the baseline renderer.
- Use `--draft` for a much faster 960x540/15fps proofreading MP4 before committing to full 1080p output.
- `inventory_media.py --review-csv` creates a teacher-proofing CSV that flags exact/visual duplicates, low-resolution images, awkward aspect ratios, unreadable files, and privacy-risk filenames.
- For public playback, use background music you are allowed to publish.
- Protect student privacy: avoid IDs, grades, addresses, phone numbers, and medical
  details in narration and on-screen text.

## Files

- [`SKILL.md`](SKILL.md) — agent workflow and approval gates
- [`scripts/inventory_media.py`](scripts/inventory_media.py) — media inventory + privacy/duplicate checks
- [`scripts/validate_script.py`](scripts/validate_script.py) — `script.json` validation
- [`scripts/lyrics_to_script.py`](scripts/lyrics_to_script.py) — song-first MV skeleton from timed lyrics (Mode B)
- [`scripts/generate_video.py`](scripts/generate_video.py) — baseline renderer
- [`references/`](references) — schema, design presets, and full command reference
