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
   - **Side = "left":** Keeps left ~92.5% of cropped area, trims ~7.5% from right (reduced for wider appearance)
   - **Side = "right":** Keeps right ~92.5% of cropped area, trims ~7.5% from left (reduced for wider appearance)
   - **No side specified:** Keeps center ~92.5% of cropped area
3. **GPU-accelerated text overlays:** Shows "Cam: {camera} | Time: {timestamp}" in top-left corner
   - Reads camera name and timestamp from CSV for each clip
   - Rendered during GPU encoding (no additional processing)
   - White text with black shadow for readability on any background
4. **Action-focused framing:** Removes ~7.5% from opposite side while zoom compensates
5. **Final result:** Standard horizontal 16:9 video with enhanced focus on action side and informative overlays
6. **Preserves context:** Shows most of the field while eliminating less relevant areas
7. **Quality preservation:** Full FFmpeg GPU pipeline (crop→scale→overlay→encode in single pass)

### How It Works
```
CSV: Placement=1, Side="left", Camera="Cam2", Time="1:52:22"
Clip: Cam2-02112026_clip01_01_52_22.mp4

1. Calculate crop area: 1/1.15 = 86.96% of original (this creates the zoom)
2. Read CSV: Placement 1 → Side "left", Camera "Cam2", Timestamp "1:52:22"
3. Extract "clip01" from filename → matches Placement 1
4. Trim ~7.5% from RIGHT side of crop area (keeps left ~92.5% - wider appearance)
5. Build FFmpeg filter chain:
   - Crop directly from ORIGINAL video pixels at calculated position
   - Scale cropped portion to standard 1920x1080 (16:9)
   - Add text overlay: "Cam\: Cam2 | Time\: 1\:52\:22" (colons escaped for FFmpeg)
   - Overlay positioned in top-left, white text size 48 with black shadow
6. Write filter chain to temporary file (avoids command line length limits)
7. Execute single FFmpeg command processing entire pipeline on GPU
8. Result: Enhanced horizontal video with overlay, optimized quality (~150MB file size)

Note: Full GPU pipeline approach
- All operations (crop, scale, overlay, encode) in single FFmpeg pass
- Text overlays rendered during GPU encoding (no additional time)
- Supports 48+ clips using filter_complex_script method
- Real-time progress tracking with tqdm-style output
- Automatic cleanup of temporary filter files
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
    'opposite_side_trim': 0.075,  # Trim 7.5% from opposite side (keeps 92.5% - wider appearance)
    'add_transitions': True,
    'transition_type': 'fade',  # 'fade', 'cut' (crossfade between clips)
    'transition_duration': 0.5,  # seconds
    'fps': 30,
    # GPU encoding settings
    'gpu_preset': 'p4',  # NVENC preset
    'gpu_cq': 30,  # Quality setting for ~150MB files
    'gpu_maxrate': '25M',  # Max bitrate
    'gpu_bufsize': '5M',  # Buffer size
    # CPU encoding fallback
    'cpu_preset': 'veryfast',
    'cpu_crf': 26,  # Similar visual quality to GPU CQ=30
    'cpu_threads': 8,
    # Audio settings
    'audio_bitrate': '128k',  # Optimized for smaller file size
    # Overlay settings
    'overlay_fontsize': 48,
    'overlay_fontfile': 'C:/Windows/Fonts/arial.ttf',
    'overlay_position': 'top-left',  # x=10:y=10
}
```

### GPU Acceleration
- **Automatic Detection:** Detects NVIDIA GPU (NVENC) on startup
- **GPU Available:** Uses `h264_nvenc` codec (10-20x faster than CPU)
  - Preset: `p4` (balanced quality/speed)
  - Quality: `cq=30` (high quality with optimized file size ~150MB)
  - Bitrate: 25M max with VBR (variable bitrate), 5M buffer
  - Audio: 128k AAC (optimized for file size)
  - Speed: 60-120 fps typical encoding speed
- **No GPU / Fallback:** Uses CPU `libx264` codec
  - Threads: 8 (multi-core CPU utilization)
  - Preset: `veryfast` (optimized for speed)
  - Quality: `crf=26` (similar visual quality to GPU CQ=30)
  - Speed: 5-15 fps typical encoding speed
- **Full GPU Pipeline:** Complete FFmpeg filter chain processing (crop → scale → overlay → encode)
  - All video operations happen in single GPU pass
  - No temporary files or multi-pass CPU operations
  - Text overlays rendered during encoding using FFmpeg `drawtext` filter
- **Portability:** Works on any PC - automatically adapts to available hardware

### Adjustable Parameters
- **zoom_factor:** 1.0 (no zoom) to 1.3 (30% zoom) - Default: 1.15 (15% zoom)
- **opposite_side_trim:** 0.0 (keep full width) to 0.3 (trim 30%) - Default: 0.075 (7.5% - reduced for wider appearance)
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
- **Architecture:** Pure FFmpeg filter chain pipeline (replaced MoviePy processing)
- **CSV Integration:** Reads `csv_files/timestamps.csv` for Side, Camera, and Timestamp information
- **Clip Metadata:** Stores camera name and timestamp for each clip in `clip_data` dictionary
- **Processing Pipeline:**
  
  **Stage 1: Video Information Gathering**
  - `_get_ffmpeg_path()`: Locates FFmpeg executable (MoviePy bundled or system PATH)
  - `_get_video_info()`: Uses ffprobe to extract video dimensions via JSON parsing
  - `_load_side_info()`: Enhanced to read Camera, Timestamp, and Side columns from CSV
  
  **Stage 2: Crop Calculation**
  - `_calculate_crop_params()`: Computes FFmpeg crop coordinates based on side preference
  - Zoom: 15% (crops to 86.96% of original, scaled to 1920x1080)
  - Trim: 7.5% from opposite side (keeps 92.5% width for wider appearance)
  - Precision: Direct pixel calculations for exact framing
  
  **Stage 3: Filter Chain Construction**
  - Build FFmpeg filter for each clip: `[idx:v]crop=w:h:x:y,scale=1920:1080,drawtext=...,[vidx]`
  - Crop parameters from _calculate_crop_params()
  - Scale to standard 1920x1080 resolution
  - Drawtext overlay: "Cam: {camera} | Time: {timestamp}" in top-left
  - Font: C:/Windows/Fonts/arial.ttf (Windows system font)
  - Text styling: White fontsize=48 with black shadow for readability
  - Colon escaping: Timestamps use `\:` for FFmpeg filter compatibility
  - Concat all clips: `concat=n={num_clips}:v=1:a=1[outv][outa]`
  
  **Stage 4: Filter File Approach**
  - Uses `filter_complex_script` parameter to avoid Windows command line length limits (~8191 chars)
  - Writes complete filter chain to temporary file
  - Supports unlimited clip count (48+ clips tested successfully)
  - Automatic cleanup: Temp file deleted after processing
  
  **Stage 5: GPU Encoding**
  - Single FFmpeg command processes entire filter chain
  - GPU: h264_nvenc with CQ=30, 25M maxrate, 5M bufsize
  - CPU fallback: libx264 with CRF=26, 8 threads
  - Result: ~150MB output files with excellent quality
  
- **Progress Tracking:**
  - Real-time FFmpeg stderr parsing for progress metrics
  - Displays: Percentage, visual progress bar (█/░), current/total seconds
  - Shows: Elapsed time, ETA, encoding FPS, speed multiplier
  - Tqdm-style output for professional monitoring
  - Error capture: Stores FFmpeg error_lines for debugging
  
- **Side Mapping:** Maps clip placement numbers to side preferences (left/right/center)
  - Left → Keeps left side, removes right 7.5%
  - Right → Keeps right side, removes left 7.5%
  - Center → Symmetrical crop from both sides
- **Filename Parsing:** Extracts placement from clip filename (e.g., "clip01" → Placement 1)
- **Auto-conversion:** All clips from `output/` folder processed automatically
- **Resolution:** 1920x1080 (16:9 horizontal)
- **FPS:** 30fps
- **Quality Optimizations:** CQ=30 (GPU) or CRF=26 (CPU) for ~150MB target file size
- **Audio:** AAC 128kbps for smaller file sizes
- **Overlay Data:** Reads Camera and timestamp columns from CSV for informative overlays

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
