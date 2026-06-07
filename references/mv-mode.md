# Song-first MV mode (Mode B)

In Mode B the **song's lyric timeline is the skeleton**. Instead of pacing a story and adding
BGM afterward (Mode A), you give a song plus timed lyrics, and each lyric line (or section)
becomes one media slot to fill with a photo or clip. The song itself is the main audio.

The renderer (`scripts/generate_video.py`) is unchanged — Mode B just produces a normal
`subtitle-only` `script.json` whose timings come from the lyrics. `scripts/lyrics_to_script.py`
builds that skeleton.

## Inputs (pick one)

Most Suno graduation songs have no LRC, so two input formats are supported:

1. **LRC file** — standard `[mm:ss.xx]lyric` lines:

   ```text
   [00:00.00]燈光亮起的這一刻
   [00:06.50]我們一起走過
   [00:13.00]副歌：謝謝你
   ```

   Metadata tags (`[ti:]`, `[ar:]`, …) are ignored. A line may carry several timestamps; each
   becomes its own entry.

2. **Sections JSON** — a list of `{"time", "text"}` objects, for songs without an LRC where the
   teacher just marks a few section start times:

   ```json
   [
     {"time": "0:00", "text": "前奏"},
     {"time": "0:15", "text": "第一段主歌"},
     {"time": "0:48", "text": "副歌 謝謝你"}
   ]
   ```

   `time` accepts `m:ss(.xx)`, `h:mm:ss`, or plain seconds.

## How durations are derived

Each entry's duration is **the gap to the next timestamp**; the last entry runs to the end of the
song. So the rendered video length naturally equals the song length (which keeps it within the
validator's ±15% target check). Provide the song length one of three ways:

- `--song path/to/song.mp3` — auto-detected via `ffprobe` when available, or
- `--song-duration 215` — length in seconds (overrides ffprobe), or
- neither — the last line is extended by the median of earlier line gaps and a warning is printed.

The bundled renderer overlaps consecutive clips slightly (`CONCAT_PADDING` in
`generate_video.py`), which would otherwise pull every photo earlier than its lyric and make the
video finish before the song. To keep playback locked to the lyric times, the tool pads each
slot's `duration` by that overlap (`CLIP_OVERLAP`, 0.6s); after the renderer pulls each clip back,
each photo lands on its lyric's start and the video runs the full song length. The `_start`
annotation still records the true lyric timestamp. If you swap in a renderer that does **not**
overlap clips, subtract 0.6s from each duration (or set `CLIP_OVERLAP = 0`).

## Granularity: line vs section

`--granularity line` (default) → one media slot per lyric line. Best for fast montages where the
picture changes with every line.

`--granularity section` → consecutive non-empty lines are grouped into one slot that holds a
single photo for the whole verse/chorus block. **Empty lyric lines act as boundaries** (and become
their own instrumental beat), so put a blank line between sections in the LRC, or use the sections
JSON. Section slots carry a `_lyrics` array listing the grouped lines.

## Chorus detection

Normalized lyric lines (punctuation/spacing stripped) that **repeat two or more times** are treated
as the chorus. Chorus slots get:

- `_section: "chorus"` annotation, and
- a punchier `transition: "zoom_cut"` instead of `"auto"`.

This is where you place the strongest media — the most moving graduation photos, whole-class
photos, or activity highlights.

## Filling the media

Every slot's `file` starts blank (`"file": ""`) with annotations to guide filling:

- `_lyric` — the single lyric line (line granularity), or `_lyrics` — the grouped lines (section).
- `_start` — the slot's start time in seconds.
- `_section: "chorus"` — marks chorus slots.

Map a photo/clip to each slot by its content, prioritizing hero media on chorus slots. To pre-fill
sequentially, pass `--media-list a.jpg,b.jpg,...` or `--media-dir <folder>` (supported media only);
the files cycle through the slots in order, after which you adjust by hand.

## Output shape

The generated `script.json` is `subtitle-only` with a single scene (`rhythm: "lively_fast"`):

- `audio.bgm_volume: 1.0` — the song is the main audio, not background.
- `audio.bgm_fadeout` — from `--fadeout` (default `0`, so the song finishes cleanly).
- each item: `duration` from the lyric gap, `motion: "auto"`, `transition` `zoom_cut` on chorus
  else `auto`, and `narration` = the lyric line unless `--no-lyrics` is given.

## Example

```bash
python scripts/lyrics_to_script.py \
  --lrc materials/song.lrc \
  --song materials/song.mp3 \
  --granularity line \
  --title "畢業快樂 MV" \
  --output mv.mp4 \
  --out materials/script.json
```

Then fill the empty `file` fields (hero media on the `chorus` slots), validate, and render with the
song as `--bgm`:

```bash
python scripts/validate_script.py materials/script.json --media-root materials
python scripts/generate_video.py --script materials/script.json --media-root materials --bgm materials/song.mp3
```

## CLI options

| Option | Purpose |
|--------|---------|
| `--lrc` / `--sections` | input timeline (mutually exclusive, one required) |
| `--song` | song file; auto-detect duration via ffprobe |
| `--song-duration` | song length in seconds (overrides ffprobe) |
| `--granularity line\|section` | per-line or per-section media slots (default `line`) |
| `--no-lyrics` | do not write lyric subtitles |
| `--fadeout` | ending BGM fade-out seconds (default `0` = none) |
| `--media-list` / `--media-dir` | fill `file` slots sequentially |
| `--title` / `--output` | script title and rendered MP4 filename |
| `--width` / `--height` / `--fps` | output dimensions (default 1920×1080, 24 fps) |
| `--out` | where to write `script.json` (default: alongside the input) |

## Scope (v1)

- Alignment granularity is the **lyric line/section**, not individual beats. Hard beat-synced cuts
  (onset detection via librosa) are a future option, kept out of v1 to avoid heavy dependencies.
- You must provide an LRC or section times. Auto-transcription / forced alignment (whisper) is
  future work.
- Subtitles use the existing bottom-subtitle style; centered/karaoke per-character highlighting
  would be a larger renderer change and is not in v1.
