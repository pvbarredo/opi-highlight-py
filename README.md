# OPI Highlight - Video Processing Suite

A comprehensive Python-based video processing toolkit for sports highlight extraction, compilation, and optimization. Designed for creating professional highlight reels from game footage with intelligent cropping, multi-format output, and maximum compression.

## Project Overview

This project provides a complete workflow for sports video processing:

1. **Extract Clips** - Extract 5-second highlight clips from full game footage based on CSV timestamps
2. **Generate Vertical Videos** - Create 9:16 social media compilations (Instagram, TikTok, YouTube Shorts) with intelligent side-based cropping and letterbox mode
3. **Generate Horizontal Videos** - Create 16:9 traditional format compilations (YouTube, streaming platforms) with enhanced zoom and focus
4. **Compress Videos** - Reduce file sizes by 50-70% while maintaining visual quality using advanced H.264 compression

## Key Features

### 🎯 Smart Clip Extraction
- 📹 CSV-driven timestamp extraction (timestamp - 3s to + 2s = 5-second clips)
- 🎥 Automatic camera name matching from video folder
- ⏱️ Multiple timestamp formats supported (HH:MM:SS, MM:SS, seconds)
- 📊 Side-based metadata (left/right) for intelligent processing

### 📱 Vertical Video Generation (9:16)
- 🖼️ Letterbox mode with black bars for design space
- 🔍 10% crop-zoom (like phone pinch zoom) for quality preservation
- ↔️ Side-based trimming (30% from opposite side) using CSV data
- 🎬 Perfect for Instagram Reels, TikTok, YouTube Shorts, Facebook Stories

### 🖥️ Horizontal Video Generation (16:9)
- 🔍 15% crop-zoom for enhanced action focus
- ↔️ Side-based trimming (15% from opposite side) for optimal framing
- 🎬 Perfect for YouTube, streaming platforms, TV playback

### 💾 Video Compression
- 📉 50-70% file size reduction with balanced preset
- 🎨 Near-lossless quality using H.264 CRF encoding
- ⚙️ Three presets: high_quality, balanced, small_file
- 🚀 Batch processing for entire folders

## Project Structure

```
opi-highlight-py/
├── prompts/                          # Documentation and guides
│   ├── highlight_extractor_prompt.md      # Main workflow documentation
│   ├── weekly_highlight_vertical_prompt.md # Vertical video specs
│   ├── weekly_highlight_horizontal_prompt.md # Horizontal video specs
│   ├── ig_fb_vertical_prompt.md           # Social media platform specs
│   └── video_converter_prompt.md          # Compression guide
├── csv_files/                        # CSV timestamps with side data
│   └── timestamps.csv                     # Format: Date, Placement, Camera, Time, Side
├── video_files/                      # Source game footage
├── output/                           # Extracted 5-second clips
├── vertical_output/                  # Compiled 9:16 vertical videos
├── horizontal_output/                # Compiled 16:9 horizontal videos
├── compressed_output/                # Compressed videos
├── video_clip_extractor.py          # Step 1: Extract clips from CSV
├── vertical_video_generator.py      # Step 2A: Create vertical compilations
├── horizontal_video_generator.py    # Step 2B: Create horizontal compilations
├── video_converter.py               # Step 3: Compress for storage/sharing
├── requirements.txt                 # Python dependencies
├── .gitignore                       # Git ignore patterns
└── README.md                        # This file
```

## Installation

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## CSV File Format

The CSV file contains timestamp data with side information for intelligent video processing.

### Required Format (`csv_files/timestamps.csv`):

```csv
Date: 2026-02-15
Placement,Camera,Time,Side
1,Cam1,1:52:22,left
2,Cam2,2:15:30,right
3,Cam1,2:45:18,left
4,Cam3,3:12:45,right
```

**CSV Structure:**
- **First row:** `Date: YYYY-MM-DD` (metadata header)
- **Second row:** Column headers
- **Columns:**
  - `Placement` - Clip number/identifier
  - `Camera` - Camera name (matches video filename, e.g., Cam1 → Cam1.mp4)
  - `Time` - Timestamp in format HH:MM:SS, MM:SS, or seconds
  -Quick Start

### Prerequisites
```bash
pip install -r requirements.txt
```

### Complete Workflow

#### Step 1: Extract Clips from Game Footage
```bash
python video_clip_extractor.py
```
- **Input:** CSV timestamps + video folder
- **Output:** Individual 5-second clips in `output/` folder
- **Naming:** `{video}_{camera}_clip{placement}_{timestamp}s.mp4`
- **Example:** `GameFootage_Cam1_clip001_6742.00s.mp4`

#### Step 2A: Create Vertical Video (Social Media)
```bash
python vertical_video_generator.py
```
- **Input:** Clips from `output/` folder + CSV side data
- **Output:** Compiled vertical video in `vertical_output/`
- **Format:** 9:16 (1080x1920) with letterbox mode
- **Features:** 10% crop-zoom, 30% side trim, black bars for overlays
- **Use for:** Instagram Reels, TikTok, YouTube Shorts

#### Step 2B: Create Horizontal Video (Traditional Platforms)
```bash
python horizontal_video_generator.py
```
### 1. Clip Extraction
For each timestamp in your CSV:
1. Reads CSV row: Placement, Camera, Time, Side
2. Finds matching video file in `video_files/` folder (Camera name → filename)
3. Calculates clip range: `[timestamp - 3s, timestamp + 2s]` = 5-second clip
4. Extracts clip and saves to `output/` folder
5. Filename includes placement number for side-mapping later

### 2. Vertical Video Generation (Crop-Zoom Approach)
For each clip:
1. Reads Side value from CSV using placement number
2. Calculates crop area from original video (zoom_factor 1.10 = crop 90.9% of original)
3. Applies side-based trim: keeps 70% from priority side, removes 30% from opposite
4. Crops directly from ORIGINAL video pixels (quality preservation)
5. Scales cropped portion to fit 1080px width (single scale operation)
6. Adds black bars top/bottom to reach 1920px height (letterbox mode)
7. Compiles all clips with optional transitions

**Result:** Professional vertical video with action focused on left/right side, space for text overlays

### 3. Horizontal Video Generation (Crop-Zoom Approach)
For each clip:
1. Reads Side value from CSV using placement number
2. Calculates crop area from original video (zoom_factor 1.15 = crop 86.96% of original)
3. Applies side-based trim: keeps 85% from priority side, removes 15% from opposite
4. Crops directly from ORIGINAL video pixels (quality preservation)
5. Scales cropped portion to 1920x1080 resolution
6. Compiles all clips with optional transitions

**Result:** Enhanced horizontal video with 15% closer view, focused on action side

### 4. Video Compression
For each video:
1. Loads video with MoviePy/FFmpeg
2. Applies H.264 codec with CRF (Constant Rate Factor)
3. Uses optimal encoding preset (slow/medium for better compression)
4. Compresses audio to AAC (128kbps for balanced preset)
5. Writes optimized MP4 file

**Result:** 50-70% smaller file size with visually identical quality

## Technical Details

### Crop-Zoom Technology
Unlike traditional "resize then crop" which can degrade quality, this project uses **crop-zoom**:
### Clip Extraction Issues
**"No matching video file found for camera: Cam1"**
- Ensure video filename contains camera name (e.g., `GameFootage_Cam1.mp4`)
- Camera names are case-sensitive
- Supported formats: .mp4, .avi, .mov, .mkv, .flv, .wmv

**"Timestamp exceeds video duration"**
- Check CSV timestamps are within video length
- Script will skip invalid timestamps and continue

### Video Generation Issues
**"No clips found in output folder"**
- Run `video_clip_extractor.py` first to create clips
- Check that `output/` folder contains .mp4 files

**"Side information not found"**
- Verify CSV has "Side" column with "left" or "right" values
- Script defaults to "center" if side not specified

**MoviePy import errors**
- Try: `pip install --upgrade moviepy`
- Install FFmpeg: `pip install ffmpeg-python`

### Compression Issues
**"Conversion very slow"**
- Use faster preset: `--preset balanced` or add `--encoding-preset fast`
- GPU acceleration (future feature) will improve speed

**"File size not reduced enough"**
- Try lower CRF: `--crf 28` (smaller file, slightly lower quality)
- Use `--preset small_file` for maximum compression

**"Quality loss visible"**
- Try higher CRF: `--crf 20` or `--crf 18`
- Use `--preset high_quality` for near-lossless

## System Requirements

- **Python:** 3.7+ (tested on 3.12.8)
- **FFmpeg:** Required for video processing (installed via moviepy dependencies)
- **Disk Space:** Plan for 2-3x original video size during processing
- **RAM:** 4GB minimum, 8GB+ recommended for 1080p/4K videos
- **CPU:** Multi-core recommended for faster encoding

## Dependencies

```
moviepy==2.1.2
pandas==3.0.0
numpy==2.4.2
```

Install all dependencies:
```bash
pip install -r requirements.txt
```


## License

This project is open source and available for personal and educational use.

## Credits

Built with:
- [MoviePy](https://zulko.github.io/moviepy/) - Video editing library
- [Pandas](https://pandas.pydata.org/) - CSV data processing
- [FFmpeg](https://ffmpeg.org/) - Video encoding/decoding
## Configuration

### Vertical Video Settings
Edit `vertical_video_generator.py`:
```python
VERTICAL_CONFIG = {
    'resolution': (1080, 1920),      # 9:16 vertical
    'letterbox_mode': True,           # Black bars on/off
    'zoom_factor': 1.10,              # 10% crop-zoom (1.0 = no zoom)
    'opposite_side_trim': 0.30,       # Trim 30% from opposite side
    'add_transitions': True,          # Crossfade between clips
    'transition_duration': 0.5,       # 0.5 second transitions
    'fps': 30,
}
```

### Horizontal Video Settings
Edit `horizontal_video_generator.py`:
```python
HORIZONTAL_CONFIG = {
    'resolution': (1920, 1080),       # 16:9 horizontal
    'zoom_factor': 1.15,              # 15% crop-zoom
    'opposite_side_trim': 0.15,       # Trim 15% from opposite side
    'add_transitions': True,
    'transition_duration': 0.5,
    'fps': 30,
}
```

### Compression Presets
```python
# In video_converter.py
--preset high_quality   # CRF 18, 30-50% reduction, near lossless
--preset balanced       # CRF 23, 50-70% reduction (default)
--preset small_file     # CRF 28, 70-85% reduction
```

## Documentation

The `prompts/` folder contains comprehensive documentation:
- **highlight_extractor_prompt.md** - Complete workflow guide
- **weekly_highlight_vertical_prompt.md** - Vertical video specifications
- **weekly_highlight_horizontal_prompt.md** - Horizontal video specifications
- **ig_fb_vertical_prompt.md** - Social media platform requirements
- **video_converter_prompt.md** - Compression techniques and settings
python video_converter.py --folder vertical_output/ --preset small_file
``
   python video_clip_extractor.py
   ```

4. **Find your clips:**
   Extracted clips will be saved in the `output/` folder with names like:
   - `video_clip_001_30.50s.mp4`
   - `video_clip_002_90.00s.mp4`

## How It Works

For each timestamp in your CSV:
1. Reads the timestamp value
2. Calculates clip range: `[timestamp - 3s, timestamp + 2s]`
3. Extracts a 5-second clip (centered slightly before the timestamp)
4. Saves the clip with a descriptive filename

## Prompts Folder

The `prompts/` folder is for storing:
- Development prompts
- Feature ideas
- Code snippets
- Notes and documentation

Feel free to add markdown files or text files to track your development process!

## Troubleshooting

**"No timestamp column found in CSV"**
- Make sure your CSV has a column named `timestamp`, `time`, `Time`, or `Timestamp`

**"Video file not found"**
- Check that your video file is in the `video_files/` folder
- Verify the filename in the script matches your actual file

**Clip extraction fails**
- Ensure the timestamp doesn't exceed video duration
- Check that FFmpeg is installed (required by moviepy)

## Requirements

- Python 3.7+
- FFmpeg (for video processing)

## License

This project is open source and available for personal and educational use.
