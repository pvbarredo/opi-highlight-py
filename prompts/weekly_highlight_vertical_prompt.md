# Weekly Highlight Vertical Prompt

**Date:** February 14, 2026
**Parent:** [highlight_extractor_prompt.md](highlight_extractor_prompt.md)

## Project Goal
Create vertical video compilations (9:16 aspect ratio) from extracted highlight clips for weekly recap videos.

## Requirements

### Folder Structure
- **Input folder:** `output/` - Extracted clips from main video_clip_extractor.py
- **Output folder:** `vertical_output/` - Generated vertical videos

### Input
- Source: Extracted clips from `output/` folder
- Format: Horizontal video clips (16:9 or other landscape formats)
- Metadata: Placement, Camera, Timestamp from filenames
- Auto-discovery: Automatically finds all .mp4, .avi, .mov, .mkv files in output folder

### Output
- **Location:** `vertical_output/` folder
- **Aspect Ratio:** 9:16 (Vertical/Portrait - 1080x1920)
- **Format:** MP4 (H.264 codec)
- **Audio:** Preserved from original clips
- **Duration:** Combined duration of all selected clips
- **Filename:** `Weekly_Highlight_YYYY-MM-DD.mp4`

## Video Processing Requirements

### Vertical Conversion Strategy

**LETTERBOX MODE (Default):**
1. **10% Crop-Zoom:** Extracts a smaller area (90.9% of original) from the source video, creating a zoom effect like pinch-to-zoom on your phone
2. **Smart side-based trimming:** Uses CSV "Side" column to determine which side to keep
   - **Side = "left":** Keeps left 70% of cropped area, trims 30% from right
   - **Side = "right":** Keeps right 70% of cropped area, trims 30% from left
   - **No side specified:** Keeps center 70% of cropped area
3. **Letterbox with black bars:** Centers video horizontally with black bars top/bottom
4. **Design space:** Large black bars provide space for overlays, text, graphics, logos
5. **Preserves context:** Shows most of the field while prioritizing action side
6. **Quality preservation:** Crops from original video pixels, then scales once (better quality than resize-then-crop)

**FILL MODE (Alternative):**
- Set `letterbox_mode: False` for traditional crop-to-fill
- Crops video to completely fill 9:16 frame (no black bars)
- Uses side-based positioning for crop location

### How It Works (Letterbox Mode)
```
CSV: Placement=1, Side="left"
Clip: Cam1_clip001_6742.00s.mp4

1. Calculate crop area: 1/1.10 = 90.9% of original (this creates the zoom)
2. Read CSV: Placement 1 → Side "left"
3. Extract "clip001" from filename → matches Placement 1
4. Trim 30% from RIGHT side of crop area (keeps left 70%)
5. Crop directly from ORIGINAL video pixels at calculated position
6. Scale cropped portion to fit 1080px width
7. Add black bars top/bottom to reach 1920px height
8. Result: Zoomed action on left, better quality, space for designs
```

### Compilation Features
- **Clip ordering:** By timestamp or custom order
- **Transitions:** Smooth transitions between clips (fade, cut, slide)
- **Intro/Outro:** Optional intro card (3-5 seconds) and outro
- **Text overlays:**
  - Clip number/placement
  - Timestamp or time of play
  - Week identifier
- **Background music:** Optional background track

### Weekly Highlight Specifications
- **Target platforms:** Instagram Reels, TikTok, YouTube Shorts
- **Optimal length:** 30-90 seconds
- **Clip selection:** Best highlights from the week
- **Branding:** Team logo in corner (optional)
- **Date range:** Display week range in intro

## Implementation Details (Current)
- **CSV Integration:** Reads `csv_files/timestamps.csv` for Side information
- **Side Mapping:** Maps clip placement numbers to side preferences (left/right)
- **Crop-Zoom Processing:**
  1. Calculate crop area from original video (zoom_factor 1.10 = crop 90.9%)
  2. Apply side-based trim to crop area (30% from opposite side)
  3. Crop directly from ORIGINAL video at calculated position
  4. Scale cropped portion to fit 1080px width (single scaling operation)
  5. Add black bars top/bottom to reach 1920px height
- **Quality Advantage:** Works with original pixels until final scale (better than resize-then-crop)
- **Smart Trimming:** 
  - Left → Keeps left 70%, removes right 30%
  - Right → Keeps right 70%, removes left 30%
  - Center → Keeps center 70%
- **Filename Parsing:** Extracts placement from clip filename (e.g., "clip001" → Placement 1)
- **Auto-conversion:** All clips from `output/` folder processed with their side preferences
- **Resolution:** 1080x1920 (9:16 vertical)
- **FPS:** 30fps
- **Transitions:** Optional crossfade between clips (0.5s default)

## Configuration Options
```python
VERTICAL_CONFIG = {
    'resolution': (1080, 1920),  # 9:16 for social media
    'letterbox_mode': True,  # True = black bars with most of video; False = crop to fill
    'zoom_factor': 1.10,  # 10% zoom (1.10 = 110% of original size)
    'opposite_side_trim': 0.30,  # Trim 30% from opposite side (keeps 70%)
    'crop_method': 'center',  # Used when letterbox_mode=False
    'add_transitions': True,
    'transition_type': 'fade',  # 'fade', 'cut' (crossfade between clips)
    'transition_duration': 0.5,  # seconds
    'fps': 30,
}
```

### Adjustable Parameters
- **zoom_factor:** 1.0 (no zoom) to 1.5 (50% zoom) - Default: 1.10 (10% zoom)
- **opposite_side_trim:** 0.0 (keep full width) to 0.5 (trim 50%) - Default: 0.30 (30%)
- **letterbox_mode:** True (black bars) or False (fill screen)

### Visual Layout (Letterbox Mode)
```
┌─────────────────────┐ ─┐
│   BLACK BAR         │  │ Design space for:
│   (Add text/logo)   │  │ - Team logo
├─────────────────────┤  │ - Title text
│                     │  │ - Score overlay
│   GAME FOOTAGE      │ ─┘
│   (Zoomed 10%,      │
│    Left 70% shown)  │
│                     │
├─────────────────────┤ ─┐
│   BLACK BAR         │  │ Design space for:
│   (Add CTA/info)    │  │ - Date/opponent
└─────────────────────┘ ─┘ - Social handle
                           - CTA button
```

## Usage Flow
1. Extract individual clips using main script → saves to `output/` folder
2. Run vertical video generator: `python vertical_video_generator.py`
   - Auto-reads all clips from `output/` folder
   - Converts each clip to vertical (9:16)
   - Combines clips with transitions
3. Output ready-to-upload vertical video in `vertical_output/` folder

## File Structure
```
opi-highlight-py/
├── output/                          # Input: Horizontal clips
│   ├── Cam1-02112026_Cam1_clip001_6742.00s.mp4
│   ├── Cam1-02112026_Cam1_clip002_8542.00s.mp4
│   └── ...
├── vertical_output/                 # Output: Vertical videos
│   └── Weekly_Highlight_2026-02-14.mp4
└── vertical_video_generator.py      # Run this script
```

## Future Enhancements
- [ ] Auto-select top N clips by duration or placement
- [ ] Add animated text effects
- [ ] Support for multiple weeks in batch
- [ ] Custom branding templates
- [ ] Auto-post to social media platforms
- [ ] Audio normalization across clips
- [ ] Speed ramping for dramatic effect

---

*This prompt extends the main highlight extractor for vertical video content creation*
