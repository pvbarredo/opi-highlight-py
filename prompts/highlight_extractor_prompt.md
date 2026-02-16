# Highlight Extractor Prompt

**Date:** February 14, 2026
**Last Updated:** February 14, 2026

## Project Goal
Create a Python program that reads a CSV file with timestamps and automatically extracts video clips from matching video files based on camera names.

## Requirements

### Folder Structure
- `prompts/` - Save and change prompts as we code
- `csv_files/` - Source folder for CSV files
- `video_files/` - Source folder for ALL video files (multiple cameras)
- `output/` - Extracted clips destination

### Core Functionality
- **Input:** CSV file with timestamps and camera identifiers
- **Input:** Folder path (not individual files) containing video files
- **Process:** Match camera names in CSV to video filenames in folder
- **Output:** Extract clips with the following logic:
  - **Start time:** timestamp - 3 seconds
  - **End time:** timestamp + 3 seconds
  - **Total clip duration:** 6 seconds per highlight

### Video File Matching Logic
- Script accepts a **folder path** as input (e.g., `video_files/`)
- For each row in CSV, reads the Camera value (e.g., "Cam1")
- Searches folder for video file containing that camera name in the filename
- Example: CSV has "Cam1" → finds `Cam1_recording.mp4` in folder
- **Case-insensitive matching:** "Cam1" matches "cam1_video.mp4"
- **Supports formats:** .mp4, .avi, .mov, .mkv, .flv, .wmv
- **Caching:** Each video loads once, even if multiple clips from same camera

### CSV Format
**Actual format (2/14/2026):**
```
Date,2/14/2026,,,
Placement,Camera,Time,Side
1,Cam1,1:52:22,left
2,Cam1,2:22:22,left
3,Cam1,1:22:22,left
4,Cam1,1:25:22,left
5,Cam1,2:21:22,left
```

**Columns:**
- `Date` - Header row with date (automatically skipped)
- `Placement` - Clip number/position (used in output filename)
- `Camera` - Camera identifier (e.g., Cam1, Cam2 - used in output filename)
- `Time` - Timestamp in H:MM:SS or HH:MM:SS format
- `Side` - **Position indicator (left/right) - CRITICAL for vertical video**
  - Used by vertical_video_generator.py for intelligent letterbox trimming
  - "left" = keeps left 70% of video, trims right 30% (prioritizes left action)
  - "right" = keeps right 70% of video, trims left 30% (prioritizes right action)
  - Letterbox mode: Video is zoomed 10% then trimmed, centered with black bars top/bottom
  - Black bars provide space for text, graphics, and branding overlays

**Time Format:** H:MM:SS or HH:MM:SS (e.g., 1:52:22 = 1 hour 52 minutes 22 seconds)

## Implementation Details
- **Video Processing:** Using `moviepy` library (v2.1.2+)
- **CSV Handling:** Using `pandas` library
- **Auto-skips date header row** in CSV
- **Detects "Time" column** automatically (supports: Time, time, Timestamp, timestamp)
- **Dynamic video loading:** Matches camera names to files in folder
- **Video caching:** Loads each camera's video once for efficiency
- **Output format:** `{video}_clip{Placement:02d}_HH_MM_SS.mp4`
  - Example: `Cam2-02112026_clip01_01_52_22.mp4`
  - Placement zero-padded to 2 digits (01, 02, 03...)
  - Time in HH_MM_SS format for easy identification
- **Smart skip:** Skips existing files > 1MB (already processed successfully)
- **Retry logic:** Up to 5 retries with 2-second delays for subprocess issues
- **Sequential processing:** Ensures each clip finishes before starting next (prevents simultaneous write conflicts)
- **Error handling:** Edge cases (beginning/end of video, missing files)
- **User-friendly console output** with progress indicators
- **MoviePy version compatibility:** 
  - Supports both old (subclip) and new (subclipped) API
  - Adaptive import system for different moviepy versions
  - Single-threaded processing to avoid subprocess race conditions

## Technical Notes (Resolved Issues)
### MoviePy Compatibility
- **Issue:** Different moviepy versions use different API methods
- **Solution:** Try/except blocks for both import paths and method calls
- **Import:** Tries `moviepy.editor.VideoFileClip` first, falls back to `moviepy.VideoFileClip`
- **Subclip method:** Uses `subclipped()` for v2.1+, falls back to `subclip()` for older versions
- *Install dependencies: `pip install moviepy pandas numpy`
2. Place CSV file in `csv_files/` folder
3. Place ALL video files in `video_files/` folder (multiple cameras allowed)
4. Run script: `python video_clip_extractor.py`
5. Extracted clips appear in `output/` folder with names like:
   - `Cam2-02112026_clip01_01_52_22.mp4` (timestamp: 1:52:22)
   - `Cam2-02112026_clip02_02_22_22.mp4` (timestamp: 2:22:22)
   - Format breakdown: `{VideoName}_clip{#}_HH_MM_SS.mp4`

## Example Output
```
✓ Loaded CSV file: csv_files/timestamps.csv
  Found 5 timestamps to process
✓ Loaded video for Cam2: Cam2-02112026.mp4
  Duration: 11085.59 seconds
✓ Extracted clip 1/5: Cam2-02112026_clip01_01_52_22.mp4 (1.23 MB)
  Time range: 6739.00s - 6745.00s (6.00s)
  Timestamp: 01:52:22
⊘ Skipping clip 2/5: Cam2-02112026_clip02_02_22_22.mp4 (already exists, 1.45 MB)
...
Extraction complete! Successful: 5, Failed: 0
```

## Related Prompts & Workflows

### Post-Processing Video Creation
After extracting clips with this tool, you can create various video formats:

1. **[Weekly Highlight Vertical](weekly_highlight_vertical_prompt.md)** - Social Media
   - 9:16 vertical format (Instagram, TikTok, Reels)
   - 10% zoom with letterbox mode
   - Black bars for text/graphics
   - Run: `python vertical_video_generator.py`

2. **[Weekly Highlight Horizontal](weekly_highlight_horizontal_prompt.md)** - YouTube/Streaming
   - 16:9 horizontal format (YouTube, TV, streaming)
   - 15% zoom with smart trimming
   - Standard viewing format
   - Run: `python horizontal_video_generator.py`

3. **[Instagram & Facebook Vertical](ig_fb_vertical_prompt.md)** - Platform-Optimized
   - Instagram Reels (90s max)
   - Instagram Stories (auto-splits at 15s)
   - Facebook Stories (20s max)
   - Includes safe zones, captions, CTAs

### Workflow Pipeline
```
1. Extract Clips (video_clip_extractor.py)
   ├─ Input: CSV timestamps + video folder
   └─> Output: Individual 6-second clips → output/
   
2A. Generate Vertical Videos (vertical_video_generator.py)
    ├─ Input: Clips from output/ folder + CSV Side data
    ├─ Process: 10% zoom, 30% trim, letterbox mode
    └─> Output: Vertical videos → vertical_output/
        ├─> Weekly_Highlight_2026-02-14.mp4 (9:16)
        ├─> instagram_reels_20260214.mp4 (90s max)
        └─> instagram_stories_Part1_20260214.mp4 (auto-split)

2B. Generate Horizontal Videos (horizontal_video_generator.py)
    ├─ Input: Clips from output/ folder + CSV Side data
    ├─ Process: 15% zoom, 15% trim, standard 16:9
    └─> Output: Horizontal videos → horizontal_output/
        └─> Weekly_Highlight_Horizontal_2026-02-14.mp4 (16:9)
```

## Complete Folder Structure
```
opi-highlight-py/
├── csv_files/                      # Input CSV files
├── video_files/                    # Input video files
├── output/                         # Extracted horizontal clips
├── vertical_output/                # Generated vertical videos (9:16)
├── horizontal_output/              # Generated horizontal videos (16:9)
├── video_clip_extractor.py         # Step 1: Extract clips
├── vertical_video_generator.py     # Step 2A: Create vertical videos
└── horizontal_video_generator.py   # Step 2B: Create horizontal videos
```
- MoviePy 2.1.2
- Pandas 3.0.0
- NumPy 2.4.2
- Successfully extracted 5 clips from 3-hour video (11085 seconds)

## Example Video Folder Structure
```
video_files/
├── Cam1_recording.mp4    ← Matches "Cam1" in CSV
├── Cam2_footage.mp4      ← Matches "Cam2" in CSV  
├── Cam3_video.avi        ← Matches "Cam3" in CSV
└── backup_cam1.mp4       ← Also matches "Cam1" (first match used)
```

## Usage Flow
1. Place CSV file in `csv_files/` folder
2. Place ALL video files in `video_files/` folder (multiple cameras allowed)
3. Run script - it automatically matches camera names to video files
4. Extracted clips appear in `output/` folder

## Future Enhancements (Ideas)
- [ ] Allow custom time offsets (not just -3s/+2s)
- [ ] Merge all clips into a single highlights video
- [ ] Add text overlays with descriptions from CSV
- [ ] Support for multiple video matches per camera (user selection)
- [ ] GUI interface for folder/file selection
- [ ] Batch processing multiple CSV files

---

*Use this file to track development progress and ideas!*
