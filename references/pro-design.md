# Professional Design Presets

Use this when the video must feel more polished than a plain slideshow.

## Visual profiles

- `warm_cinematic`: graduation, farewell, memory. Warm highlights, soft contrast, gentle vignette.
- `bright_documentary`: teaching record. Clean color, readable text, restrained transitions.
- `lively_school`: games, trips, celebrations. Bright, energetic, quick rhythm.
- `ceremony_gold`: formal ceremony, awards, anniversary. Dignified gold accents.
- `soft_pastel`: younger grades or cute class memories.
- `natural`: minimal grading.

## Layout rules

- `full_bleed`: strongest single image or video.
- `photo_stack`: group photos, warm memories.
- `split_two`: before/after, teacher/student, process/result.
- `scrapbook`: class-life memory sequence.
- `film_frame`: performances, sports, peak action.
- `detail_focus`: hands, awards, artwork, tools, nature, notes.
- `letterbox_video`: vertical or non-16:9 footage.
- `video_wall`: 4 photos shown like a TV wall; best for lively activity bursts.
- `grid_2x2`: clean four-photo layout for teaching records or achievement summaries.
- `mosaic`: one large photo plus two smaller details; best when one image is the hero.

Avoid using the same layout more than 3-4 times in a row unless the scene is intentionally calm.

## Rhythm rules

- `warm_slow`: 4.5-6.5s/photo, dissolve/fade, slow push/pull.
- `lively_fast`: 2.5-4s/photo, slide/whip/zoom sparingly.
- `cinematic_peak`: 2-3.5s/photo, short narration or silence, music carries impact.
- `emotional_pause`: 5-7s/photo, fade, less movement, small silence around key lines.
- `documentary`: 4-6s/photo, clean chapter markers, chronological process.

## Transition discipline

- Use `dissolve` within warm scenes.
- Use `slide_left` / `slide_right` for time or location movement.
- Use `zoom_cut` for one or two strong highlights.
- Use `flash_white` only for applause, stage, award, or beat moments.
- Use `match_cut` when two images have similar composition.
- Use `fade` for title cards and emotional pauses.
- Use `hold` plus `pause_after` for a visual comma or beat stop.

Strong transitions become cheap when repeated too often. For teaching records, default to `dissolve`/`fade`; use slide or zoom transitions only at chapter changes or true highlight beats. Keep `transition_duration` around 0.25-0.45 seconds for smoother output.

## Automatic motion selection

Use `motion: "auto"` unless a specific move is needed. The baseline renderer infers:

- Wide image: pan left or right.
- Portrait image: slow pull back.
- Square/group image: slow push in.
- Lively/peak scene: stronger push in or zoom-cut transition.
- Emotional scene: slow pull back and fade.

Every still image should either specify `motion` or use `auto`.

## Proofing discipline

Before final rendering, remove or explicitly approve:

- exact duplicate files and visually similar repeats,
- low-resolution images that look soft at 1080p,
- extreme portrait/panorama crops unless the renderer uses letterbox or a multi-photo layout,
- screenshots, forms, IDs, grades, phone numbers, addresses, and medical/private records,
- blurred, closed-eye, accidental, or unflattering photos.

## Filter discipline

- `none`: teaching records, screenshots, documents, whiteboards, accurate-color images.
- `vibrant`: outdoor activities, hands-on learning, cheerful moments.
- `vintage`: memory sequences and softer class-life scenes.
- `sepia`: warm retrospective moments; use sparingly.
- `film`: performances, sports, experiments, field trips.
- `bw`: one serious reflective pause.

The baseline renderer applies these styles to still photos. Keep filters subtle; changing filters on every photo makes transitions feel less smooth.

## Sound cue discipline

Use about 3-8 cues per 2-minute video, not one per photo.

- `soft_hit`: title reveal or final message.
- `soft_whoosh`: gentle layout change.
- `beat_hit`: peak action cut.
- `camera_click`: scrapbook/photo-stack moment.
