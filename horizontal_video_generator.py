"""
Horizontal Video Generator
Creates horizontal format videos (16:9) from extracted highlight clips
with smart zooming and side-based trimming for YouTube, streaming platforms
"""

import os
import subprocess
from pathlib import Path
from datetime import datetime
import pandas as pd
import re
try:
    from moviepy.editor import VideoFileClip, concatenate_videoclips
except ImportError:
    from moviepy import VideoFileClip, concatenate_videoclips


class HorizontalVideoGenerator:
    def __init__(self, clips_folder="output", output_dir="horizontal_output", csv_path="csv_files/timestamps.csv"):
        """
        Initialize the Horizontal Video Generator.
        
        Args:
            clips_folder (str): Folder containing extracted clips
            output_dir (str): Directory to save horizontal videos
            csv_path (str): Path to CSV file with Side information
        """
        self.clips_folder = clips_folder
        self.output_dir = output_dir
        self.csv_path = csv_path
        self.side_mapping = {}  # Maps clip names to side preference
        self.gpu_available = self._check_gpu_availability()
        
        # Load side information from CSV
        self._load_side_info()
        
        # Create output directory
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
        
        # Default configuration
        self.config = {
            'resolution': (1920, 1080),  # 16:9 aspect ratio
            'zoom_factor': 1.15,  # 15% zoom (1.15 = 115% of original size)
            'opposite_side_trim': 0.15,  # Trim 15% from opposite side (keeps 85%)
            'add_transitions': True,
            'transition_duration': 0.5,
            'fps': 30,
        }
    
    def _check_gpu_availability(self):
        """
        Check if NVIDIA GPU (NVENC) is available for hardware encoding.
        
        Returns:
            bool: True if GPU encoding is available, False otherwise
        """
        try:
            # Try to get ffmpeg path from moviepy/imageio
            ffmpeg_path = 'ffmpeg'
            try:
                from moviepy.config import get_setting
                ffmpeg_path = get_setting("FFMPEG_BINARY")
            except:
                try:
                    import imageio_ffmpeg
                    ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
                except:
                    pass
            
            result = subprocess.run(
                [ffmpeg_path, '-hide_banner', '-encoders'],
                capture_output=True,
                text=True,
                timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            if 'h264_nvenc' in result.stdout:
                print("✓ NVIDIA GPU detected - Hardware encoding enabled")
                return True
            else:
                print("⚠ No NVIDIA GPU detected - Using CPU encoding")
                return False
        except Exception as e:
            print(f"⚠ Could not detect GPU ({e}) - Using CPU encoding")
            return False
    
    def _load_side_info(self):
        """
        Load side information from CSV file to determine trimming positioning.
        Maps clip placement numbers to their side preference (left/right).
        """
        try:
            # Read CSV (skip date header row)
            df = pd.read_csv(self.csv_path)
            if 'Date' in df.columns and len(df.columns) > 3:
                df = pd.read_csv(self.csv_path, skiprows=1)
            
            # Create mapping of placement to side
            if 'Placement' in df.columns and 'Side' in df.columns:
                for _, row in df.iterrows():
                    placement = row['Placement']
                    side = str(row['Side']).lower().strip()
                    self.side_mapping[placement] = side
                print(f"✓ Loaded side preferences for {len(self.side_mapping)} clips")
            else:
                print("⚠ CSV missing Placement or Side columns, using center framing")
        except Exception as e:
            print(f"⚠ Could not load CSV side info: {e}")
            print("  Using center framing for all clips")
    
    def _get_side_for_clip(self, clip_filename):
        """
        Extract placement number from clip filename and return side preference.
        
        Args:
            clip_filename (str): Filename like 'Cam1_clip001_6742.00s.mp4'
            
        Returns:
            str: 'left', 'right', or 'center'
        """
        # Try to extract placement number from filename
        # Format: {video}_{camera}_clip{placement}_{timestamp}s.mp4
        match = re.search(r'clip(\d+)', clip_filename)
        if match:
            placement = int(match.group(1))
            side = self.side_mapping.get(placement, 'center')
            return side
        return 'center'
    
    def get_clip_files(self, pattern=None):
        """
        Get all video clip files from the clips folder.
        
        Args:
            pattern (str): Optional filename pattern to filter clips
            
        Returns:
            list: Sorted list of clip file paths
        """
        video_extensions = ['.mp4', '.avi', '.mov', '.mkv']
        clips = []
        
        for filename in os.listdir(self.clips_folder):
            if any(filename.lower().endswith(ext) for ext in video_extensions):
                if pattern is None or pattern.lower() in filename.lower():
                    clips.append(os.path.join(self.clips_folder, filename))
        
        return sorted(clips)
    
    def process_to_horizontal(self, clip, side='center'):
        """
        Process horizontal video with zoom and smart trimming.
        
        Args:
            clip: VideoFileClip object
            side (str): 'left', 'right', or 'center' - determines trim position
            
        Returns:
            VideoFileClip: Processed horizontal video
        """
        target_width, target_height = self.config['resolution']
        original_width = clip.w
        original_height = clip.h
        
        zoom = self.config['zoom_factor']
        trim_percent = self.config['opposite_side_trim']
        
        # Step 1: Calculate crop area from original video (like phone pinch zoom)
        # zoom=1.15 means we want to see 1/1.15 = 86.96% of the original (zoomed in)
        crop_width = int(original_width / zoom)
        crop_height = int(original_height / zoom)
        
        # Step 2: Calculate how much to trim from opposite side
        # We want to keep (1 - trim_percent) of the CROPPED width
        target_visible_width = int(crop_width * (1 - trim_percent))
        target_visible_height = crop_height
        
        # Step 3: Calculate position in ORIGINAL video to crop from
        if side == 'left':
            # Keep left side, trim from right
            x1 = 0
            x2 = target_visible_width
            y1 = (original_height - target_visible_height) // 2
            y2 = y1 + target_visible_height
        elif side == 'right':
            # Keep right side, trim from left
            x1 = original_width - target_visible_width
            x2 = original_width
            y1 = (original_height - target_visible_height) // 2
            y2 = y1 + target_visible_height
        else:
            # Center: keep middle portion
            x1 = (original_width - target_visible_width) // 2
            x2 = x1 + target_visible_width
            y1 = (original_height - target_visible_height) // 2
            y2 = y1 + target_visible_height
        
        # Step 4: Crop from ORIGINAL video (this creates the zoom effect)
        try:
            cropped = clip.cropped(x1=x1, y1=y1, x2=x2, y2=y2)
        except (AttributeError, TypeError):
            cropped = clip.crop(x1=x1, y1=y1, x2=x2, y2=y2)
        
        # Step 5: Scale the cropped portion to target resolution (1920x1080)
        try:
            final = cropped.resized(self.config['resolution'])
        except (AttributeError, TypeError):
            final = cropped.resize(self.config['resolution'])
        
        return final
    
    def create_weekly_highlight(self, clip_files=None, output_name=None):
        """
        Create a weekly highlight horizontal video from clips.
        
        Args:
            clip_files (list): List of clip file paths. If None, uses all clips.
            output_name (str): Output filename. If None, auto-generates.
            
        Returns:
            str: Path to generated video
        """
        print("Creating Weekly Highlight Horizontal Video...")
        print("=" * 50)
        
        # Get clips to process
        if clip_files is None:
            clip_files = self.get_clip_files()
        
        if not clip_files:
            print("✗ No clips found to process")
            return None
        
        print(f"✓ Found {len(clip_files)} clips to process")
        
        # Load and process clips
        processed_clips = []
        for idx, clip_path in enumerate(clip_files):
            try:
                clip_filename = os.path.basename(clip_path)
                print(f"Processing clip {idx + 1}/{len(clip_files)}: {clip_filename}")
                
                # Get side preference for this clip
                side = self._get_side_for_clip(clip_filename)
                
                clip = VideoFileClip(clip_path)
                processed_clip = self.process_to_horizontal(clip, side=side)
                processed_clips.append(processed_clip)
                print(f"  ✓ Processed to {self.config['resolution'][0]}x{self.config['resolution'][1]} - Zoom: 15%, Side: {side}")
            except Exception as e:
                print(f"  ✗ Error processing clip: {e}")
        
        if not processed_clips:
            print("✗ No clips successfully processed")
            return None
        
        # Concatenate clips
        print(f"\nCombining {len(processed_clips)} clips...")
        try:
            if self.config['add_transitions']:
                # Add crossfade transitions
                final_clip = concatenate_videoclips(
                    processed_clips,
                    method="compose",
                    padding=-self.config['transition_duration']
                )
            else:
                final_clip = concatenate_videoclips(processed_clips, method="compose")
            
            print(f"✓ Combined clips - Total duration: {final_clip.duration:.2f}s")
        except Exception as e:
            print(f"✗ Error combining clips: {e}")
            return None
        
        # Generate output filename
        if output_name is None:
            date_str = datetime.now().strftime("%Y-%m-%d")
            output_name = f"Weekly_Highlight_Horizontal_{date_str}.mp4"
        
        output_path = os.path.join(self.output_dir, output_name)
        
        # Write video file with GPU/CPU auto-detection
        print(f"\nWriting video to: {output_path}")
        encoder_type = "NVIDIA GPU (NVENC)" if self.gpu_available else "CPU (x264)"
        print(f"Using {encoder_type} encoding...")
        
        try:
            if self.gpu_available:
                # GPU encoding with NVENC - direct write, no temp file
                final_clip.write_videofile(
                    output_path,
                    fps=self.config['fps'],
                    preset='medium',
                    audio_codec='aac',
                    ffmpeg_params=[
                        '-c:v', 'h264_nvenc',
                        '-preset', 'p4',
                        '-rc', 'vbr',
                        '-cq', '23',
                        '-b:v', '0',
                        '-bufsize', '10M',
                        '-maxrate', '50M',
                        '-bf', '3',
                        '-g', '250',
                        '-movflags', '+faststart'
                    ]
                )
            else:
                # CPU encoding
                final_clip.write_videofile(
                    output_path,
                    codec='libx264',
                    audio_codec='aac',
                    fps=self.config['fps'],
                    threads=8,
                    preset='veryfast',
                    ffmpeg_params=['-crf', '23']
                )
            
            print(f"✓ Video created successfully!")
            print(f"  Resolution: {self.config['resolution'][0]}x{self.config['resolution'][1]}")
            print(f"  Duration: {final_clip.duration:.2f}s")
            print(f"  Zoom: {int((self.config['zoom_factor'] - 1) * 100)}%")
            print(f"  Trim: {int(self.config['opposite_side_trim'] * 100)}% from opposite side")
            print(f"  Encoder: {encoder_type}")
            print(f"  Location: {output_path}")
            
        except Exception as e:
            print(f"✗ Error with {encoder_type} encoding: {e}")
            if self.gpu_available:
                # Fallback to CPU if GPU fails
                print("  Retrying with CPU encoding...")
                try:
                    final_clip.write_videofile(
                        output_path,
                        codec='libx264',
                        audio_codec='aac',
                        fps=self.config['fps'],
                        threads=8,
                        preset='veryfast',
                        ffmpeg_params=['-crf', '23']
                    )
                    print(f"✓ Video created with CPU fallback")
                except Exception as e2:
                    print(f"✗ CPU fallback also failed: {e2}")
            else:
                print(f"✗ Error writing video: {e}")
        
        # Clean up
        final_clip.close()
        for clip in processed_clips:
            clip.close()
        
        return output_path


def main():
    """Main function for testing horizontal video generation."""
    print("Horizontal Video Generator")
    print("=" * 50)
    
    # Initialize generator
    csv_path = "csv_files/timestamps.csv"
    generator = HorizontalVideoGenerator(
        clips_folder="output",
        output_dir="horizontal_output",
        csv_path=csv_path
    )
    
    print(f"CSV file: {csv_path}")
    print(f"Source folder: {generator.clips_folder}")
    print(f"Output folder: {generator.output_dir}")
    
    # Create weekly highlight
    print("\nCreating Weekly Highlight Horizontal Video...")
    generator.create_weekly_highlight()


if __name__ == "__main__":
    main()
