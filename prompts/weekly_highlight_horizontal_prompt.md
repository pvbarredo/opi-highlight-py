# Weekly Highlight Horizontal Prompt

**Date:** February 14, 2026
**Parent:** [highlight_extractor_prompt.md](highlight_extractor_prompt.md)

## Project Goal
Create horizontal video compilations (16:9 aspect ratio) from extracted highlight clips with smart zooming and side-based trimming for enhanced viewing.

## Requirements

### Folder Structure
- **Input folder:** `output/` - Extracted clips from main video_clip_extractor.py
- **Output folder:** `horizontal_output/` - Generated horizontal highlight videos

### Input
- Source: Extracted clips from `output/` folder
- Format: Horizontal video clips (16:9 or other landscape formats)
- Metadata: Placement, Camera, Timestamp from filenames
- CSV Data: Side information for intelligent trimming
- Auto-discovery: Automatically finds all .mp4, .avi, .mov, .mkv files in output folder

### Output
- **Location:** `horizontal_output/` folder
- **Aspect Ratio:** 16:9 (Horizontal - 1920x1080)
- **Format:** MP4 (H.264 codec)
- **Audio:** Preserved from original clips
- **Duration:** Combined duration of all selected clips
- **Filename:** `Weekly_Highlight_Horizontal_YYYY-MM-DD.mp4`

## Video Processing Strategy

### Enhanced Horizontal Conversion
1. **15% Crop-Zoom:** Extracts a smaller area (86.96% of original) from the source video, creating a zoom effect like pinch-to-zoom on your phone
2. **Smart side-based trimming:** Uses CSV "Side" column to determine which side to keep
   - **Side = "left":** Keeps left 85% of cropped area, trims 15% from right
   - **Side = "right":** Keeps right 85% of cropped area, trims 15% from left
   - **No side specified:** Keeps center 85% of cropped area
3. **Action-focused framing:** Removes 15% from opposite side while zoom compensates
4. **Final result:** Standard horizontal 16:9 video with enhanced focus on action side
5. **Preserves context:** Shows most of the field while eliminating less relevant areas
6. **Quality preservation:** Crops from original video pixels, then scales once (better quality than resize-then-crop)

### How It Works
```
CSV: Placement=1, Side="left"
Clip: Cam1_clip001_6742.00s.mp4

1. Calculate crop area: 1/1.15 = 86.96% of original (this creates the zoom)
2. Read CSV: Placement 1 → Side "left"
3. Extract "clip001" from filename → matches Placement 1
4. Trim 15% from RIGHT side of crop area (keeps left 85%)
5. Crop directly from ORIGINAL video pixels at calculated position
6. Scale cropped portion to standard 1920x1080 (16:9)
7. Result: Enhanced horizontal video, better quality, focused on left action
```

### Mathematical Balance
- **Zoom:** 115% (adds 15% to all dimensions)
- **Trim:** Remove 15% from opposite side
- **Net Effect:** Maintains similar field coverage while focusing on action area
- **Aspect Ratio:** Maintains 16:9 for YouTube, TV, streaming platforms

## Configuration Options
```python
HORIZONTAL_CONFIG = {
    'resolution': (1920, 1080),  # 16:9 for YouTube, streaming
    'zoom_factor': 1.15,  # 15% zoom (1.15 = 115% of original size)
    'opposite_side_trim': 0.15,  # Trim 15% from opposite side (keeps 85%)
    'add_transitions': True,
    'transition_type': 'fade',  # 'fade', 'cut' (crossfade between clips)
    'transition_duration': 0.5,  # seconds
    'fps': 30,
}
```

### Adjustable Parameters
- **zoom_factor:** 1.0 (no zoom) to 1.3 (30% zoom) - Default: 1.15 (15% zoom)
- **opposite_side_trim:** 0.0 (keep full width) to 0.3 (trim 30%) - Default: 0.15 (15%)
- **resolution:** (1920, 1080) standard HD, or (2560, 1440) for 2K, (3840, 2160) for 4K

## Use Cases

### Perfect For:
- **YouTube Highlights:** Standard 16:9 format for YouTube uploads
- **TV/Monitor Playback:** Full-screen viewing on widescreen displays
- **Streaming Platforms:** Twitch, YouTube, Facebook video
- **Game Recap Videos:** Weekly or season highlight compilations
- **Recruitment Videos:** Showcase player skills in standard format
- **Website Embeds:** Standard video player compatibility

### Advantages Over Original Clips:
1. **Closer action:** 15% zoom brings viewers into the game
2. **Focused framing:** Removes less relevant side of field
3. **Consistent presentation:** All clips processed uniformly
4. **Professional polish:** Smooth transitions between highlights
5. **Optimized viewing:** Enhanced for main action area

## Usage Flow
1. Extract individual clips using main script → saves to `output/` folder
2. Run horizontal video generator: `python horizontal_video_generator.py`
   - Auto-reads all clips from `output/` folder
   - Applies 15% zoom and smart trimming based on CSV Side data
   - Combines clips with transitions
3. Output professional horizontal highlight video in `horizontal_output/` folder

## File Structure
```
opi-highlight-py/
├── output/                          # Input: Original clips
│   ├── Cam1-02112026_Cam1_clip001_6742.00s.mp4
│   ├── Cam1-02112026_Cam1_clip002_8542.00s.mp4
│   └── ...
├── horizontal_output/               # Output: Horizontal highlights
│   └── Weekly_Highlight_Horizontal_2026-02-14.mp4
└── horizontal_video_generator.py    # Run this script
```

## Implementation Details
- **CSV Integration:** Reads `csv_files/timestamps.csv` for Side information
- **Side Mapping:** Maps clip placement numbers to side preferences (left/right)
- **Processing Pipeline:**
  1. Zoom video by 15% (configurable)
  2. Trim 15% from opposite side based on CSV Side value
  3. Scale to standard 1920x1080 resolution
- **Smart Trimming:** 
  - Left → Keeps left 85%, removes right 15%
  - Right → Keeps right 85%, removes left 15%
  - Center → Keeps center 85%
- **Filename Parsing:** Extracts placement from clip filename
- **Auto-conversion:** All clips from `output/` folder processed automatically
- **Resolution:** 1920x1080 (16:9 horizontal)
- **FPS:** 30fps
- **Transitions:** Optional crossfade between clips (0.5s default)

## Comparison: Horizontal vs Vertical

| Feature | Horizontal Generator | Vertical Generator |
|---------|---------------------|-------------------|
| **Output Format** | 16:9 (1920x1080) | 9:16 (1080x1920) |
| **Zoom Level** | 15% | 10% |
| **Trim Amount** | 15% opposite side | 30% opposite side |
| **Black Bars** | None | Top/bottom for designs |
| **Best For** | YouTube, TV, streaming | Instagram, TikTok, Reels |
| **Aspect Focus** | Wide field view | Tall portrait view |

## Future Enhancements
- [ ] Auto-select top N clips by action intensity
- [ ] Custom intro/outro sequences for horizontal format
- [ ] Picture-in-picture for multi-camera angles
- [ ] Score overlay integration
- [ ] Slow-motion effect on key plays
- [ ] Audio commentary track integration
- [ ] Chapter markers for YouTube
- [ ] Automated thumbnail generation
- [ ] Export in multiple resolutions (720p, 1080p, 4K)

---

*This prompt focuses on horizontal video compilation for traditional streaming and viewing platforms*
