# Professional Design Presets

Use this reference when the user says the output feels too plain, too slideshow-like, or not professional enough.

## Upgrade Strategy

Make the video feel designed, not decorated:

1. Choose one global visual profile.
2. Use a premium motion title template.
3. Vary photo layouts by content.
4. Use scene rhythms to control pacing.
5. Add chapter markers for structure.
6. Use sound cues sparingly at visual beats.
7. Keep color consistent across the film.
8. Apply photo filters and transitions as part of the story rhythm, not as decoration.

## Visual Profiles

`warm_cinematic`

- Best for graduation, memory, farewell.
- Warm highlights, soft contrast, gentle vignette.
- Use `cinematic_blur`, `paper_memory`, `photo_stack`, `scrapbook`.

`bright_documentary`

- Best for teaching records and classroom process.
- Clean natural color, readable subtitles, restrained transitions.
- Use `clean_documentary`, `full_bleed`, `detail_focus`.

`lively_school`

- Best for field trips, sports, achievement showcases.
- Bright but not neon; faster rhythm and punchier transitions.
- Use `full_bleed`, `film_frame`, `split_two`, `whip_pan`.

`ceremony_gold`

- Best for formal ceremonies, awards, anniversaries.
- Gold accent lines, slow moves, dignified titles.
- Use `ceremony_gold` title template and gentle dissolves.

`soft_pastel`

- Best for younger students or cute class memories.
- Soft color, paper shapes, playful but clean movement.

## Motion Title Recipes

Premium opening:

```json
{
  "type": "titlecard",
  "template": "cinematic_blur",
  "background_file": "best_group_photo.jpg",
  "title": "??箇",
  "subtitle": "Haishan Elementary Class 603",
  "kicker": "Graduation 2026",
  "duration": 5,
  "motion": "slow_push_in",
  "sound_cue": "soft_hit"
}
```

Warm memory closing:

```json
{
  "type": "titlecard",
  "template": "paper_memory",
  "background_file": "final_group_photo.jpg",
  "title": "????",
  "subtitle": "Thank you for growing together",
  "duration": 5,
  "motion": "slow_pull_back",
  "sound_cue": "soft_whoosh"
}
```

Formal ceremony:

```json
{
  "type": "titlecard",
  "template": "ceremony_gold",
  "title": "?Ｘ平?貊旨",
  "subtitle": "2026",
  "duration": 5,
  "motion": "slow_push_in",
  "sound_cue": "soft_hit"
}
```

## Layout Selection

- Use `full_bleed` for the strongest image in a scene.
- Use `photo_stack` for group photos and memory sequences.
- Use `split_two` to show before/after, teacher/student, preparation/result.
- Use `scrapbook` for warm class-life memories.
- Use `film_frame` for performances, sports, and peak action.
- Use `detail_focus` for hands, awards, artwork, tools, nature, notes.
- Use `letterbox_video` for vertical clips or non-16:9 footage.

Avoid using the same layout more than 3-4 times in a row unless the scene is intentionally calm.

## Rhythm Rules

`warm_slow`

- 4.5-6.5 seconds per photo.
- Dissolve/fade transitions.
- Slow push or pull movement.

`lively_fast`

- 2.5-4 seconds per photo.
- Use whip pan, slide, zoom cut sparingly.
- Good for activity sequences and field trips.

`cinematic_peak`

- 2-3.5 seconds per photo, with occasional hold on the best image.
- Use beat hit, flash white, zoom cut.
- Keep narration short or pause narration so music can carry impact.

`emotional_pause`

- 5-7 seconds per photo.
- Use fade, warm look, less motion.
- Leave small silence before/after key lines.

`documentary`

- 4-6 seconds per photo.
- Clean lower-thirds or chapter markers.
- Prioritize readability and process order.

## Chapter Markers

Use a chapter marker when a scene shift needs clarity:

```json
{
  "chapter_marker": {
    "text": "The Challenge Begins",
    "style": "lower_third_line"
  }
}
```

Good chapter texts:

- "Getting Ready"
- "The Challenge Begins"
- "A Bright Moment"
- "Growing Together"
- "One Last Look"

For Chinese output, keep chapter markers short, usually 4-8 characters.

## Transition Discipline

- Use `dissolve` within a warm scene.
- Use `slide_left` or `slide_right` for location/time movement.
- Use `zoom_cut` for one or two strong peak moments.
- Use `flash_white` only at applause, stage, award, or beat moments.
- Use `match_cut` when two photos have similar poses or composition.
- Use `fade` for title cards and emotional pauses.

Never apply strong transitions uniformly. Strong transitions become cheap when repeated too often.
## Photo Filter Discipline

Use media item `style` as the photo filter field. Keep the global `visual_profile` and scene `color_look` consistent, then vary `style` only when it helps the scene read better:

- `none`: clean teaching-record photos, screenshots, documents, whiteboards, and any image where accurate color matters.
- `vibrant`: outdoor activities, hands-on learning, displays, games, and cheerful classroom moments.
- `vintage`: memory sequences, preparation, old-photo mood, or softer class-life scenes.
- `sepia`: warm retrospective scenes; use sparingly so the video does not look old-fashioned by accident.
- `film`: performances, sports, experiments, field trips, and highlight sequences.
- `bw`: reflective turns, farewell, gratitude, or a single serious pause.

For teaching-record videos, default to `none` or `vibrant`; avoid heavy nostalgia filters unless the script explicitly shifts into reflection.

## Sound Cue Discipline

Use sound cues only when they add structure:

- `soft_hit`: title reveal, ceremony title, final message.
- `soft_whoosh`: gentle layout change.
- `beat_hit`: peak action cut.
- `camera_click`: scrapbook/photo-stack moment.

Do not place a cue on every photo. Use about 3-8 cues per 2-minute video.
