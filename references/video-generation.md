# Video Generation Reference

Use this reference when preparing dependencies, music, rendering commands, and QA.

## Dependency Check

Check before installing:

```powershell
python --version
ffmpeg -version
ffprobe -version
python -c "import moviepy, PIL; import edge_tts; print('ok')"
```

If packages are missing, ask before installing. Prefer a virtual environment in the project or material folder:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install "moviepy==1.0.3" edge-tts "Pillow<10"
```

Install FFmpeg only with approval:

```powershell
winget install Gyan.FFmpeg --source winget
```

## Rendering Command Pattern

Use PowerShell backticks for multiline commands:

```powershell
python -X utf8 "C:\path\to\generate_video.py" `
  --script "C:\path\to\materials\script.json" `
  --bgm "C:\path\to\materials\music.mp3"
```

If no BGM:

```powershell
python -X utf8 "C:\path\to\generate_video.py" `
  --script "C:\path\to\materials\script.json"
```

If the generator path is unknown, locate it from user context or ask for it. Do not rely on a hard-coded personal Desktop path.

## Suno Prompts

Pick one and adapt the title/tone.

Graduation, instrumental:

```text
Warm nostalgic graduation background music, solo piano with gentle strings, slow and emotional, bittersweet and hopeful, no vocals, BPM 68
```

Graduation, vocals:

```text
Warm Mandarin graduation song, piano with gentle strings, meaningful lyrics about growth, gratitude, friendship and farewell, clear vocals, BPM 68
```

Lively school activity, instrumental:

```text
Cheerful school celebration music, bright piano, ukulele and light percussion, uplifting and warm, youthful energy, no vocals, BPM 108
```

Lively school activity, vocals:

```text
Fun Mandarin school activity song, bright piano and upbeat percussion, cheerful lyrics about teamwork, friendship and achievement, clear vocals, BPM 108
```

Teaching record/documentary:

```text
Calm professional educational documentary background music, light piano with ambient pads, focused, warm and inspiring, no vocals, BPM 75
```

School anniversary or ceremony:

```text
Grand warm school ceremony music, piano, strings and soft percussion, dignified, hopeful and celebratory, no vocals, BPM 82
```

## QA Checklist

After rendering:

```powershell
ffprobe -v error -show_entries format=duration -show_streams "output.mp4"
```

Verify:

- MP4 exists and file size is plausible.
- Resolution is 1920x1080 unless the user requested otherwise.
- Duration is near target.
- Audio stream exists when BGM or TTS was requested.
- Subtitles are not cut off and do not cover faces in key scenes.
- Title cards fit comfortably and do not exceed the intended visual length.
- BGM does not overpower narration.

Optional frame extraction:

```powershell
ffmpeg -y -i "output.mp4" -vf "fps=1/30" "qa_frame_%03d.jpg"
```

Inspect several frames visually before calling the job done.
