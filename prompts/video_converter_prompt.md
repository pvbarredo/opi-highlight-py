# Video Converter Prompt

**Date:** February 15, 2026
**Parent:** [highlight_extractor_prompt.md](highlight_extractor_prompt.md)

## Project Goal
Convert video files to the smallest possible file size while maintaining visual quality using advanced compression techniques.

## Requirements

### Folder Structure
- **Input folder:** `video_files/` - Source videos to compress
- **Output folder:** `compressed_output/` - Optimized compressed videos

### Input
- Source: Any video files from `video_files/` folder
- Supported formats: .mp4, .avi, .mov, .mkv, .flv, .wmv
- Auto-discovery: Automatically finds all video files in input folder
- Batch processing: Process single file or entire folder

### Output
- **Location:** `compressed_output/` folder
- **Format:** MP4 (H.264 codec - best compatibility)
- **Naming:** `{original_name}_compressed.mp4`
- **Quality:** Near-lossless to human eye
- **File size:** 40-70% reduction from original (varies by source)

## Compression Strategy

### Quality-Focused Compression
1. **CRF (Constant Rate Factor):** Uses CRF 23 (lower = better quality, higher = smaller file)
   - CRF 18-23: Visually lossless to nearly lossless
   - CRF 23: Sweet spot for quality vs size (default)
   - CRF 28: Acceptable quality, smaller files
2. **H.264 Codec:** Universal compatibility with high compression efficiency
3. **Two-pass encoding:** Optional for optimal bitrate distribution
4. **Preset:** 'slow' or 'medium' for better compression (slower = smaller file)
5. **Audio compression:** AAC codec at 128-192 kbps (transparent quality)

### Advanced Settings
- **Profile:** High profile for modern devices
- **Pixel format:** yuv420p (universal compatibility)
- **Frame rate:** Preserve original or standardize to 30fps
- **Resolution:** Preserve original (no downscaling unless requested)
- **Bitrate mode:** VBR (Variable Bit Rate) for optimal quality/size ratio

### Compression Levels
```python
# Presets for different use cases
COMPRESSION_PRESETS = {
    'high_quality': {
        'crf': 18,          # Near lossless
        'preset': 'slow',   # Best compression
        'audio_bitrate': '192k'
    },
    'balanced': {
        'crf': 23,          # Default - excellent quality
        'preset': 'medium', # Good compression speed
        'audio_bitrate': '128k'
    },
    'small_file': {
        'crf': 28,          # Acceptable quality
        'preset': 'slow',   # Maximum compression
        'audio_bitrate': '96k'
    }
}
```

## How It Works

### Compression Process
```
Input: 3GB original video file
Process:
1. Load video with MoviePy/FFmpeg
2. Apply H.264 codec with CRF 23
3. Use 'medium' preset for compression efficiency
4. Compress audio to AAC 128kbps
5. Write optimized MP4 file

Output: 1.2GB compressed file (60% reduction)
Quality: Visually identical to original
```

### Key Features
- **Smart defaults:** Optimized settings for best quality/size ratio
- **Batch processing:** Convert entire folder at once
- **Progress tracking:** Real-time conversion progress
- **Quality presets:** Choose high_quality, balanced, or small_file
- **Metadata preservation:** Keeps original video metadata
- **Error handling:** Skips corrupted files, continues batch

## Use Cases

### Perfect For:
- **Storage optimization:** Reduce video library size by 40-70%
- **Cloud uploads:** Smaller files = faster uploads to Google Drive, Dropbox
- **Email/sharing:** Compress videos to fit email size limits
- **Archive storage:** Long-term storage with minimal quality loss
- **YouTube uploads:** Pre-compress before uploading (faster uploads)
- **Hard drive space:** Free up space without deleting videos

### Quality Comparison
| CRF Value | Quality | Use Case | Typical Size Reduction |
|-----------|---------|----------|----------------------|
| 18 | Near lossless | Professional archiving | 30-50% |
| 23 | Excellent | General use (default) | 50-70% |
| 28 | Good | Maximum compression | 70-85% |

## Configuration Options
```python
CONVERTER_CONFIG = {
    'preset': 'balanced',  # 'high_quality', 'balanced', 'small_file'
    'crf': 23,  # Manual override (18-28 recommended)
    'encoding_preset': 'medium',  # 'slow', 'medium', 'fast'
    'audio_bitrate': '128k',  # '96k', '128k', '192k'
    'preserve_resolution': True,  # Keep original resolution
    'preserve_fps': True,  # Keep original frame rate
    'output_format': 'mp4',  # Output container format
}
```

## Implementation Details

### FFmpeg Parameters
- **Video codec:** `-c:v libx264` (H.264 encoder)
- **CRF:** `-crf 23` (constant rate factor)
- **Preset:** `-preset medium` (encoding speed/compression balance)
- **Profile:** `-profile:v high` (best quality features)
- **Audio codec:** `-c:a aac` (AAC audio encoder)
- **Audio bitrate:** `-b:a 128k` (128 kbps audio)
- **Pixel format:** `-pix_fmt yuv420p` (universal compatibility)

### Processing Flow
1. Scan input folder for video files
2. For each video:
   - Load video file
   - Apply compression settings
   - Write to compressed_output folder
   - Display progress and file size comparison
3. Generate summary report:
   - Total files processed
   - Total size before/after
   - Average compression ratio
   - Time elapsed

## Expected Results

### Example Conversions
```
Original: game_footage.mp4 (2.5 GB)
Compressed: game_footage_compressed.mp4 (1.1 GB)
Reduction: 56% | Quality: Visually lossless

Original: highlight_reel.mov (1.8 GB)
Compressed: highlight_reel_compressed.mp4 (750 MB)
Reduction: 58% | Quality: Excellent

Original: raw_camera.avi (5.2 GB)
Compressed: raw_camera_compressed.mp4 (1.9 GB)
Reduction: 63% | Quality: Near perfect
```

## Technical Notes

### Why H.264 (not H.265)?
- **Universal compatibility:** Plays on all devices, browsers, players
- **Hardware acceleration:** GPU encoding/decoding on most devices
- **Mature encoder:** x264 is highly optimized
- **Fast encoding:** Faster than HEVC/H.265
- **Good enough:** Excellent compression for most use cases

### H.265/HEVC Option (Future)
- 25-50% better compression than H.264
- Slower encoding
- Less compatible (newer devices only)
- Use when: Target devices support HEVC and need maximum compression

## Usage Instructions

### Single File Conversion
```bash
python video_converter.py --input video_files/game.mp4
```

### Batch Folder Conversion
```bash
python video_converter.py --folder video_files/
```

### Custom Quality Setting
```bash
python video_converter.py --folder video_files/ --preset high_quality
```

### Manual CRF Override
```bash
python video_converter.py --folder video_files/ --crf 20
```

## Performance Expectations

### Conversion Speed (Approximate)
- **Hardware:** Depends on CPU/GPU
- **1080p video:** ~1-3x realtime (1 hour video = 20-60 min conversion)
- **4K video:** ~0.5-1x realtime (1 hour video = 60-120 min conversion)
- **GPU acceleration:** Can speed up 2-5x with NVENC/QuickSync

### Disk Space Requirements
- **Temporary:** None (direct write to output)
- **Output folder:** Plan for 30-60% of original size
- **Example:** 100GB input → ~40GB output

## Troubleshooting

### Common Issues
- **Slow conversion:** Use 'fast' or 'medium' preset instead of 'slow'
- **File too large:** Lower CRF value (try 25 or 28)
- **Quality loss visible:** Raise CRF value (try 20 or 18)
- **Audio sync issues:** Ensure frame rate preservation enabled
- **Codec not found:** Install FFmpeg with libx264 support

## Future Enhancements
- [ ] H.265/HEVC codec option for newer devices
- [ ] GPU acceleration support (NVENC, QuickSync, AMD VCE)
- [ ] Resolution downscaling option (4K → 1080p)
- [ ] Custom bitrate mode (CBR, ABR, VBR)
- [ ] Batch scheduling (process overnight)
- [ ] Cloud integration (auto-compress uploaded videos)
