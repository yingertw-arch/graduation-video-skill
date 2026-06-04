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

## Suno prompts

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

## QA

```powershell
ffprobe -v error -show_entries format=duration -show_streams "output.mp4"
ffmpeg -y -i "output.mp4" -vf "fps=1/30" "qa_frame_%03d.jpg"
```

Check: file size, resolution, duration, audio stream, subtitle placement, title-card fit, cropping, BGM balance, and whether privacy-sensitive material appears.
