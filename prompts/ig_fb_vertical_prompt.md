# Instagram & Facebook Vertical Prompt

**Date:** February 14, 2026
**Parent:** [highlight_extractor_prompt.md](highlight_extractor_prompt.md)

## Project Goal
Create optimized vertical videos specifically formatted for Instagram Stories, Reels, and Facebook Stories with platform-specific requirements.

## Platform Specifications

### Instagram Reels
- **Aspect Ratio:** 9:16 (1080x1920)
- **Max Duration:** 90 seconds
- **Min Duration:** 3 seconds
- **Format:** MP4 (H.264)
- **Frame Rate:** 30 fps minimum
- **File Size:** Max 4GB
- **Audio:** AAC, max 48kHz

### Instagram Stories
- **Aspect Ratio:** 9:16 (1080x1920)
- **Max Duration:** 15 seconds per story (can chain multiple)
- **Format:** MP4 or MOV
- **Safe zones:** Avoid content in top 250px and bottom 250px
- **Profile icon:** Reserve top-left corner
- **Interactive elements:** Reserve bottom third for stickers/CTA

### Facebook Stories
- **Aspect Ratio:** 9:16 (1080x1920)
- **Max Duration:** 20 seconds
- **Format:** MP4 (H.264)
- **Safe zones:** Avoid top 14% and bottom 14%
- **File Size:** Max 4GB

## Requirements

### Folder Structure
- **Input folder:** `output/` - Horizontal clips from video_clip_extractor.py
- **Output folder:** `vertical_output/` - Platform-optimized vertical videos

### Input
- Source clips from `output/` folder (auto-discovered)
- Clip naming format: `{VideoName}_clip{##}_HH_MM_SS.mp4`
  - Example: `Cam2-02112026_clip01_01_52_22.mp4`
  - Placement number zero-padded (clip01, clip02, etc.)
  - Timestamp in HH_MM_SS format
  - Extractor skips existing files > 1MB (already processed)
  - 5 retry attempts with 2-second delays for reliability
- Optional: Team branding assets (logos, colors)
- Optional: Call-to-action graphics
- Supports: .mp4, .avi, .mov, .mkv formats

### Output Files (saved to `vertical_output/`)
- **Instagram Reels:** `instagram_reels_YYYYMMDD.mp4` (up to 90s)
- **Instagram Stories:** `instagram_stories_Part1_YYYYMMDD.mp4` (15s segments, auto-split)
- **Facebook Stories:** `facebook_stories_YYYYMMDD.mp4` (20s)

## IG/FB-Specific Features

### Visual Optimization
1. **Letterbox mode with black bars:**
   - 10% crop-zoom: Extracts 90.9% of original video (like phone pinch zoom) for better quality
   - Shows 70% of cropped area in center after side-based trimming
   - Black bars top/bottom provide space for platform-optimized overlays
   - Reads CSV "Side" column (left/right) for smart trimming
   - Left side → Keeps left 70%, trims right 30%
   - Right side → Keeps right 70%, trims left 30%
   - Maximizes visibility of important game action while preserving context
   - Quality advantage: Crops from original pixels, scales once (better than resize-then-crop)
2. **Safe zones:** Content in black bar areas (top 14%, bottom 20%)
3. **Design space:** Use black bars for: 
   - Avoid top 14% (profile/username area)
   - Avoid bottom 20% (interaction buttons)
3. **High contrast:** Ensure visibility on mobile screens
4. **Vertical crops:** Focus on player action, not sidelines

### Engagement Features
- **Captions/Subtitles:** Auto-generated for sound-off viewing
- **Hashtags overlay:** Display relevant hashtags
- **CTA (Call-to-Action):** 
  - "Swipe up" prompt
  - "Follow for more"
  - "Tag a friend"
- **Sticker zones:** Reserve space for poll, quiz, or question stickers
- **Music/Audio:** Trending audio compatibility

### Branding Elements
- **Team logo:** Small, unobtrusive (top corners)
- **Team colors:** Background or border accents
- **Handle/Username:** Display team social handle
- **Score/Stats:** Optionally overlay game stats
- **Date/Opponent:** Context information

## Current Implementation
```python
# vertical_video_generator.py
generator = VerticalVideoGenerator(clips_folder="output", output_dir="vertical_output")

# Create Instagram Reel (up to 90s)
generator.create_ig_fb_vertical(platform='instagram_reels')

# Create Instagram Stories (auto-splits at 15s)
generator.create_ig_fb_vertical(platform='instagram_stories')

# Create Facebook Stories (up to 20s)
generator.create_ig_fb_vertical(platform='facebook_stories')
```

## Platform Configuration
```python
max_durations = {
    'instagram_reels': 90,
    'instagram_stories': 15,
    'facebook_stories': 20
}

config = {
    'resolution': (1080, 1920),  # 9:16 aspect ratio
    'crop_method': 'center',  # 'center', 'top', 'bottom'
    'add_transitions': True,
    'transition_duration': 0.5,
    'fps': 30,
    'safe_zone_top': 0.14,  # 14% from top
    'safe_zone_bottom': 0.20,  # 20% from bottom
    'add_captions': True,
    'caption_style': {
        'font': 'Arial-Bold',
        'size': 60,
        'color': 'white',
        'stroke_color': 'black',
        'stroke_width': 3,
        'position': 'center'
    },
    'add_cta': True,
    'cta_text': 'Follow for more highlights! 🔥',
    'cta_duration': 3,  # Show CTA for last 3 seconds
    'add_hashtags': True,
    'hashtags': ['#Sports', '#Highlights', '#GameDay'],
    'logo_path': None,  # Path to team logo
    'logo_position': 'top-right',
    'logo_size': (80, 80),
    'handle': '@teamname',
    'handle_position': 'bottom-center'
}
```

## Auto-Splitting for Stories
- **Instagram Stories:** Automatically split videos longer than 15s into multiple story segments
- **Smooth transitions:** Ensure natural break points between segments
- **Progress indicators:** Add "1/3", "2/3", "3/3" indicators
- **Seamless playback:** Chain segments for continuous viewing

## Content Strategy Templates

### Template 1: Single Play Highlight
- Duration: 5-15 seconds
- Focus: One amazing play
- Text: Player name + action description
- CTA: "Follow for daily highlights"

### Template 2: Top 3 Plays
- Duration: 30-45 seconds
- Format: Countdown style (3, 2, 1)
- Transitions: Quick cuts with text overlays
- CTA: "Which was your favorite? Comment below!"

### Template 3: Game Recap
- Duration: 60-90 seconds (Reels only)
- Format: Multiple highlights from one game
- Text: Score updates, key moments
- CTA: "Full game highlights on YouTube"

## Quality Checklist
- [ ] Video fills entire vertical frame (no black bars)
- [ ] Important action visible in safe zones
- [ ] Text readable on mobile screens
- [ ] Audio levels consistent
- [ ] Captions accurate and synced
- [ ] Logo/branding not obscuring content
- [ ] File size under platform limits
- [ ] Meets minimum duration requirements
- [ ] CTA clear and compelling
- [ ] Hashtags relevant and not excessive

## Future Enhancements
- [ ] AI caption generation from audio
- [ ] Trending audio integration
- [ ] Auto-resize for multiple platforms simultaneously
- [ ] A/B testing for different CTA messages
- [ ] Analytics tracking for engagement
- [ ] Template library for different sports
- [ ] Interactive element placeholders (polls, quizzes)
- [ ] Auto-scheduling for optimal post times

---

*This prompt focuses on platform-optimized vertical video for Instagram and Facebook*
