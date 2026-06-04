# Video Generation Reference

## Dependency check

```powershell
python --version
ffmpeg -version
ffprobe -version
python -c "import PIL, moviepy; print('ok')"
```

Optional for voice mode:

```powershell
python -c "import edge_tts; print('edge_tts ok')"
```

`edge-tts` uses Microsoft's online TTS service through the Python package. It requires the package and internet access, but not the Edge browser. If it is unavailable, switch to `subtitle-only`.

If packages are missing, ask before installing. Prefer a local virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install moviepy==1.0.3 pillow edge-tts
```

macOS/Linux:

```bash
python3 -m venv .venv
./.venv/bin/python -m pip install moviepy==1.0.3 pillow edge-tts
```

For HEIC photos, also ask before installing:

```powershell
.\.venv\Scripts\python.exe -m pip install pillow-heif
```

macOS/Linux:

```bash
./.venv/bin/python -m pip install pillow-heif
```

Install FFmpeg only with approval:

```powershell
winget install Gyan.FFmpeg --source winget
```

macOS/Linux examples:

```bash
# macOS with Homebrew
brew install ffmpeg

# Debian/Ubuntu
sudo apt-get update && sudo apt-get install -y ffmpeg
```

## Inventory

```powershell
python scripts\inventory_media.py "C:\path\to\materials" --output "C:\path\to\materials\media_inventory.json"
```

macOS/Linux:

```bash
python scripts/inventory_media.py "/path/to/materials" --output "/path/to/materials/media_inventory.json"
```

## Validate

```powershell
python scripts\validate_script.py "C:\path\to\materials\script.json" --media-root "C:\path\to\materials" --target-duration 120 --probe-video-durations
```

macOS/Linux:

```bash
python scripts/validate_script.py "/path/to/materials/script.json" --media-root "/path/to/materials" --target-duration 120 --probe-video-durations
```

## Automated final generation

After photo/material approval, script approval, and MP3/BGM approval are complete, Codex should run the final generation commands itself. Do not tell the user to copy/paste commands unless execution is blocked by permissions, missing dependencies, or missing files.

Required automatic sequence:

1. Verify the approved `script.json` exists.
2. Verify the material folder exists.
3. Verify the approved MP3/BGM exists when music is part of the plan.
4. Run validation.
5. Stop and fix/report if validation has errors.
6. Run the renderer.
7. Run QA checks when `ffprobe`/`ffmpeg` are available.

## Render with bundled baseline renderer

Subtitle-only:

```powershell
python scripts\generate_video.py --script "C:\path\to\materials\script.json" --media-root "C:\path\to\materials"
```

With BGM:

```powershell
python scripts\generate_video.py --script "C:\path\to\materials\script.json" --media-root "C:\path\to\materials" --bgm "C:\path\to\music.mp3"
```

macOS/Linux:

```bash
python scripts/generate_video.py --script "/path/to/materials/script.json" --media-root "/path/to/materials"
python scripts/generate_video.py --script "/path/to/materials/script.json" --media-root "/path/to/materials" --bgm "/path/to/music.mp3"
```

Voice mode requires the `edge-tts` Python package and internet access to Microsoft's online TTS service; it does not require the Edge browser. If unavailable, render subtitle-only or ask before installing it.

The baseline renderer supports:

- `motion: "auto"`: infer pan/zoom from image aspect ratio and scene rhythm.
- Photo motion: `slow_push_in`, `slow_pull_back`, `pan_right`, `pan_left`.
- Video clips as single `file` media items (`.mp4`, `.mov`, `.m4v`); clips are trimmed to `min(script duration, real clip duration)`.
- Multi-photo layouts through image-only `files`: `video_wall`, `grid_2x2`, `mosaic`, `split_two`, `photo_stack`.
- Transitions: `auto`, `fade`, `dissolve`, approximate `slide_left`, `slide_right`, `zoom_cut`, `hold`.
- Beat pauses: `pause_after`.

## Suno prompts

Create Suno prompts from the approved script, not just the video type. Use the script's story arc, emotional curve, target duration, tone, and final use case. Include:

- instrumental or vocal
- language if vocal
- mood and emotional arc
- instrumentation
- BPM range
- "no copyrighted melody"
- public school playback/upload suitability

Graduation instrumental:

```text
Warm nostalgic graduation background music, solo piano with gentle strings, slow and emotional, bittersweet and hopeful, no vocals, BPM 68
```

Graduation vocal:

```text
Warm Mandarin graduation song for elementary school students, clear gentle vocal, meaningful lyrics about growth, gratitude, friendship, teachers, and saying goodbye, piano and strings, hopeful emotional chorus, BPM 68-78, suitable for public school ceremony playback, original melody, no copyrighted melody
```

Lively school activity instrumental:

```text
Cheerful school celebration music, bright piano, ukulele and light percussion, uplifting and warm, youthful energy, no vocals, BPM 108
```

Lively school activity vocal:

```text
Upbeat Mandarin school activity song with clear vocals, cheerful lyrics about teamwork, courage, friendship, learning, and celebration, bright piano, ukulele, claps, light percussion, youthful and warm, BPM 105-118, original melody, no copyrighted melody
```

Teaching record/documentary:

```text
Calm professional educational documentary background music, light piano with ambient pads, focused, warm and inspiring, no vocals, BPM 75
```

Teaching record vocal, only when explicitly requested:

```text
Soft Mandarin educational theme song with gentle vocals, simple lyrics about curiosity, learning, cooperation, and growth, light piano, acoustic guitar, subtle strings, calm and inspiring, BPM 72-84, original melody, no copyrighted melody
```

Ceremony:

```text
Grand warm school ceremony music, piano, strings and soft percussion, dignified, hopeful and celebratory, no vocals, BPM 82
```

Example customized prompt:

```text
Instrumental background music for a 3-minute elementary school graduation montage. Warm nostalgic opening, brighter hopeful middle, emotional but uplifting ending. Piano, gentle strings, light percussion, BPM 72-82, suitable for public school ceremony playback, no vocals, no copyrighted melody.
```

## QA

```powershell
ffprobe -v error -show_entries format=duration -show_streams "output.mp4"
ffmpeg -y -i "output.mp4" -vf "fps=1/30" "qa_frame_%03d.jpg"
```

macOS/Linux:

```bash
ffprobe -v error -show_entries format=duration -show_streams "output.mp4"
ffmpeg -y -i "output.mp4" -vf "fps=1/30" "qa_frame_%03d.jpg"
```

Check: file size, resolution, duration, audio stream, subtitle placement, title-card fit, cropping, BGM balance, and whether privacy-sensitive material appears.
