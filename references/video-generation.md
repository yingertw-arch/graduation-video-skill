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

If packages are missing, ask before installing. Prefer a local virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install moviepy==1.0.3 pillow edge-tts
```

For HEIC photos, also ask before installing:

```powershell
.\.venv\Scripts\python.exe -m pip install pillow-heif
```

Install FFmpeg only with approval:

```powershell
winget install Gyan.FFmpeg --source winget
```

## Inventory

```powershell
python scripts\inventory_media.py "C:\path\to\materials" --output "C:\path\to\materials\media_inventory.json"
```

## Validate

```powershell
python scripts\validate_script.py "C:\path\to\materials\script.json" --media-root "C:\path\to\materials" --target-duration 120
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

Voice mode requires `edge-tts`; if unavailable, render subtitle-only or ask to install it.

The baseline renderer supports:

- `motion: "auto"`: infer pan/zoom from image aspect ratio and scene rhythm.
- Photo motion: `slow_push_in`, `slow_pull_back`, `pan_right`, `pan_left`.
- Multi-photo layouts through `files`: `video_wall`, `grid_2x2`, `mosaic`, `split_two`, `photo_stack`.
- Transitions: `auto`, `fade`, `dissolve`, `slide_left`, `slide_right`, `zoom_cut`, `hold`.
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

Lively school activity instrumental:

```text
Cheerful school celebration music, bright piano, ukulele and light percussion, uplifting and warm, youthful energy, no vocals, BPM 108
```

Teaching record/documentary:

```text
Calm professional educational documentary background music, light piano with ambient pads, focused, warm and inspiring, no vocals, BPM 75
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

Check: file size, resolution, duration, audio stream, subtitle placement, title-card fit, cropping, BGM balance, and whether privacy-sensitive material appears.
