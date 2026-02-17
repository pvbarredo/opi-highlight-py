# Weekly Highlight Vertical Prompt

**Date:** February 14, 2026
**Parent:** [highlight_extractor_prompt.md](highlight_extractor_prompt.md)

## Project Goal
Create individual vertical format videos (9:16 aspect ratio) from extracted highlight clips for social media platforms.

**Default Mode:** Generates individual vertical videos for each horizontal clip
**Optional:** Can compile all clips into single video compilations

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
- **Naming:** `{original_clip_name}_vertical.mp4`
  - Example: `Cam2-02112026_clip01_00_04_34_vertical.mp4`
- **Processing:** Each clip converted individually and saved separately
- **Smart Skip:** Skips existing files > 1MB (already processed successfully)
- **Retry Logic:** Failed clips retried after main processing with randomized order
- **Sequential Processing:** 3-second waits before/after each clip for subprocess stability

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
Clip: Cam2-02112026_clip01_01_52_22.mp4

1. Calculate crop area: 1/1.10 = 90.9% of original (this creates the zoom)
2. Read CSV: Placement 1 → Side "left"
3. Extract "clip01" from filename → matches Placement 1
4. Trim 30% from RIGHT side of crop area (keeps left 70%)
5. Crop directly from ORIGINAL video pixels at calculated position
6. Scale cropped portion to fit 1080px width
7. Add black bars top/bottom to reach 1920px height
8. Result: Zoomed action on left, better quality, space for designs

Note: Clip naming format changed to {VideoName}_clip{##}_HH_MM_SS.mp4
- Placement number is zero-padded (clip01, clip02, etc.)
- Timestamp in HH_MM_SS format for easy identification
- Extractor skips existing files > 1MB to avoid re-processing
- Vertical generator also skips existing files > 1MB
- Both use retry logic for subprocess reliability
- 3-second waits before/after processing ensure stability
```

### Processing Features
- **Individual Conversion:** Each clip processed and saved separately
- **GPU Acceleration:** Automatic NVIDIA GPU detection (NVENC)
  - GPU Available: Uses `h264_nvenc` codec (10-20x faster)
  - No GPU: Automatically falls back to CPU `libx264` codec  
  - Works on any PC - adapts to available hardware
  - GPU: 60-120 fps encoding | CPU: 5-15 fps encoding
- **Progress Tracking:** Shows current clip being processed (e.g., "Processing clip 5/44")
- **Skip Existing:** Automatically skips files > 1MB that already exist
- **Retry Failed Clips:** Tracks failed clips and retries after main processing
- **Two-Tier Write:** Standard write first, then fallback method if fails
- **Resource Management:** Garbage collection and temp file cleanup between clips
- **File Verification:** Checks file size after write to confirm success

### Optional Compilation Features
For creating combined videos, uncomment compilation methods in main():
- **Clip ordering:** By timestamp or custom order
- **Transitions:** Smooth transitions between clips (fade, cut, slide)
- **Intro/Outro:** Optional intro card (3-5 seconds) and outro
- **Text overlays:**
  - Clip number/placement
  - Timestamp or time of play
  - Week identifier
- **Background music:** Optional background track

### Social Media Compilation Specifications
- **Target platforms:** Instagram Reels, TikTok, YouTube Shorts
- **Optimal length:** 30-90 seconds
- **Clip selection:** Best highlights from the week
- **Branding:** Team logo in corner (optional)
- **Date range:** Display week range in intro

## Implementation Details (Current)
- **Mode:** Individual vertical video generation (default)
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
- **Filename Parsing:** Extracts placement from clip filename (e.g., "clip01" → Placement 1)
- **Auto-conversion:** All clips from `output/` folder processed individually
- **Resolution:** 1080x1920 (9:16 vertical)
- **FPS:** 30fps
- **Skip Existing:** Files > 1MB are skipped (already processed)
- **Retry Logic:** Failed clips retried with randomized order
- **Resource Management:** Garbage collection, temp file cleanup, 3s waits

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
   - Converts each clip to vertical (9:16) individually
   - Skips existing files > 1MB
   - Retries failed clips after main processing
   - Shows progress for each clip
3. Output individual vertical videos in `vertical_output/` folder
   - Each clip saved as `{original_name}_vertical.mp4`
   - Ready to upload individually to social media

## File Structure
```
opi-highlight-py/
├── output/                                      # Input: Horizontal clips
│   ├── Cam2-02112026_clip01_00_04_34.mp4
│   ├── Cam2-02112026_clip02_00_04_56.mp4
│   └── ...
├── vertical_output/                             # Output: Individual vertical videos
│   ├── Cam2-02112026_clip01_00_04_34_vertical.mp4
│   ├── Cam2-02112026_clip02_00_04_56_vertical.mp4
│   └── ...
└── vertical_video_generator.py                  # Run this script
```

## Example Output
```
Creating Individual Vertical Videos...
==================================================
✓ Found 44 clips to process

Processing clip 1/44: Cam2-02112026_clip01_00_04_34.mp4
  ✓ Converted to vertical (1080x1920) - Mode: Letterbox, Side: right
  Writing: Cam2-02112026_clip01_00_04_34_vertical.mp4
  ✓ Saved: Cam2-02112026_clip01_00_04_34_vertical.mp4 (2.35 MB)

⊘ Skipping: Cam2-02112026_clip02_00_04_56_vertical.mp4 (already exists, 2.41 MB)

Processing clip 3/44: Cam2-02112026_clip03_00_05_32.mp4
  ✓ Converted to vertical (1080x1920) - Mode: Letterbox, Side: left
  Writing: Cam2-02112026_clip03_00_05_32_vertical.mp4
  ✓ Saved: Cam2-02112026_clip03_00_05_32_vertical.mp4 (2.28 MB)
...

==================================================
Processing complete!
  Successful: 42
  Failed: 2
  Output directory: vertical_output
==================================================
```

## Future Enhancements
- [x] Individual vertical video generation
- [x] Skip existing files > 1MB
- [x] Retry logic for failed clips
- [x] Progress tracking
- [ ] Auto-select top N clips by duration or placement
- [ ] Add animated text effects
- [ ] Support for multiple weeks in batch
- [ ] Custom branding templates
- [ ] Auto-post to social media platforms
- [ ] Audio normalization across clips
- [ ] Speed ramping for dramatic effect
- [ ] Parallel processing for faster conversion

## Optional: Creating Compilations
To create compiled videos instead of individual clips, uncomment in `main()`:
```python
# Create weekly highlight compilation
generator.create_weekly_highlight()

# Create Instagram Reel
generator.create_ig_fb_vertical(platform='instagram_reels')

# Create Instagram Stories (auto-splits at 15s)
generator.create_ig_fb_vertical(platform='instagram_stories')
```

---

*This prompt extends the main highlight extractor for vertical video content creation*
