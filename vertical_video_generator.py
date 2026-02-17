"""
Vertical Video Generator
Creates vertical format videos (9:16) from horizontal highlight clips
for social media platforms (Instagram Reels, Stories, Facebook, TikTok)

Default mode: Generates individual vertical videos for each clip
Optional: Can compile all clips into single video compilations
"""

import os
import time
import gc
import glob
import random
import subprocess
from pathlib import Path
from datetime import datetime
import pandas as pd
try:
    from moviepy.editor import VideoFileClip, concatenate_videoclips, CompositeVideoClip, TextClip, ImageClip
except ImportError:
    from moviepy import VideoFileClip, concatenate_videoclips, CompositeVideoClip, TextClip, ImageClip


class VerticalVideoGenerator:
    def __init__(self, clips_folder="output", output_dir="vertical_output", csv_path="csv_files/timestamps.csv"):
        """
        Initialize the Vertical Video Generator.
        
        Args:
            clips_folder (str): Folder containing extracted clips
            output_dir (str): Directory to save vertical videos
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
            'resolution': (1080, 1920),  # 9:16 aspect ratio
            'crop_method': 'center',  # 'center', 'top', 'bottom', 'left', 'right'
            'add_transitions': True,
            'transition_duration': 0.5,
            'fps': 30,
            'letterbox_mode': True,  # If True, shows full horizontal video with black bars; if False, crops to fill frame
            'opposite_side_trim': 0.30,  # Trim 30% from opposite side when letterboxing
            'zoom_factor': 1.10,  # Zoom in by 10% (1.10 = 110% of original size)
        }
    
    def _check_gpu_availability(self):
        """
        Check if NVIDIA GPU (NVENC) is available for hardware encoding.
        
        Returns:
            bool: True if GPU encoding is available, False otherwise
        """
        try:
            result = subprocess.run(
                ['ffmpeg', '-hide_banner', '-encoders'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if 'h264_nvenc' in result.stdout:
                print("✓ NVIDIA GPU detected - Hardware encoding enabled")
                return True
            else:
                print("⚠ No NVIDIA GPU detected - Using CPU encoding")
                return False
        except Exception:
            print("⚠ Could not detect GPU - Using CPU encoding")
            return False
    
    def _load_side_info(self):
        """
        Load side information from CSV file to determine crop positioning.
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
                print("⚠ CSV missing Placement or Side columns, using center crop")
        except Exception as e:
            print(f"⚠ Could not load CSV side info: {e}")
            print("  Using center crop for all clips")
    
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
        import re
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
    
    def crop_to_vertical(self, clip, side='center'):
        """
        Crop horizontal video to vertical format (9:16) with side-based positioning.
        Supports two modes:
        1. Fill mode (letterbox_mode=False): Crops to fill entire vertical frame
        2. Letterbox mode (letterbox_mode=True): Shows most of horizontal video with black bars
        
        Args:
            clip: VideoFileClip object
            side (str): 'left', 'right', or 'center' - determines crop/trim position
            
        Returns:
            VideoFileClip: Cropped/letterboxed vertical video
        """
        target_width, target_height = self.config['resolution']
        original_width = clip.w
        original_height = clip.h
        
        if self.config['letterbox_mode']:
            # LETTERBOX MODE: Show most of horizontal video with black bars top/bottom
            # Step 1: Calculate crop area based on zoom (like phone pinch zoom)
            # Step 2: Trim opposite side based on 'side' parameter
            
            zoom = self.config['zoom_factor']
            trim_percent = self.config['opposite_side_trim']
            
            # Calculate the area to crop from original video (inverse of zoom)
            # zoom=1.10 means we want to see 1/1.10 = 90.9% of the original
            crop_width = int(original_width / zoom)
            crop_height = int(original_height / zoom)
            
            # Now calculate how much to trim from opposite side
            # We want to keep (1 - trim_percent) of the CROPPED width
            target_visible_width = int(crop_width * (1 - trim_percent))
            
            # Calculate position in ORIGINAL video to crop from
            if side == 'left':
                # Keep left side, trim from right
                x1 = 0
                x2 = target_visible_width
                y1 = (original_height - crop_height) // 2
                y2 = y1 + crop_height
            elif side == 'right':
                # Keep right side, trim from left
                x1 = original_width - target_visible_width
                x2 = original_width
                y1 = (original_height - crop_height) // 2
                y2 = y1 + crop_height
            else:
                # Center: keep middle portion
                x1 = (original_width - target_visible_width) // 2
                x2 = x1 + target_visible_width
                y1 = (original_height - crop_height) // 2
                y2 = y1 + crop_height
            
            # Crop from the ORIGINAL video (this is the zoom effect)
            try:
                cropped = clip.cropped(x1=x1, y1=y1, x2=x2, y2=y2)
            except (AttributeError, TypeError):
                cropped = clip.crop(x1=x1, y1=y1, x2=x2, y2=y2)
            
            # Resize cropped portion to fit vertical frame width (maintain aspect ratio)
            # Scale to fit width of 1080
            cropped_width = x2 - x1
            cropped_height = y2 - y1
            scale_factor = target_width / cropped_width
            new_width = target_width
            new_height = int(cropped_height * scale_factor)
            
            try:
                resized = cropped.resized((new_width, new_height))
            except (AttributeError, TypeError):
                resized = cropped.resize((new_width, new_height))
            
            # Add black bars (letterbox) top and bottom to reach target_height
            if new_height < target_height:
                y_offset = (target_height - new_height) // 2
                
                # Create black background
                from moviepy.video.VideoClip import ColorClip
                try:
                    background = ColorClip(size=(target_width, target_height), color=(0, 0, 0), duration=resized.duration)
                except:
                    # Fallback: just return resized if ColorClip doesn't work
                    return resized
                
                # Composite video on black background
                try:
                    final = CompositeVideoClip([background, resized.with_position(('center', y_offset))], size=(target_width, target_height))
                except:
                    final = resized
                
                return final
            else:
                return resized
        
        else:
            # FILL MODE: Original behavior - crop to fill entire frame
            target_aspect = target_height / target_width
            
            # Calculate crop dimensions to maintain 9:16 aspect ratio
            crop_width = int(original_height / target_aspect)
            crop_height = original_height
            
            # If calculated width is larger than original, adjust based on width
            if crop_width > original_width:
                crop_width = original_width
                crop_height = int(original_width * target_aspect)
            
            # Calculate crop position based on side preference
            if side == 'left':
                # Prioritize left side of the frame
                x1 = 0
                y1 = (original_height - crop_height) // 2
            elif side == 'right':
                # Prioritize right side of the frame
                x1 = original_width - crop_width
                y1 = (original_height - crop_height) // 2
            else:
                # Center crop (default)
                x1 = (original_width - crop_width) // 2
                y1 = (original_height - crop_height) // 2
        
        x2 = x1 + crop_width
        y2 = y1 + crop_height
        
        # Crop the video
        try:
            cropped = clip.cropped(x1=x1, y1=y1, x2=x2, y2=y2)
        except (AttributeError, TypeError):
            cropped = clip.crop(x1=x1, y1=y1, x2=x2, y2=y2)
        
        # Resize to target resolution
        try:
            resized = cropped.resized(self.config['resolution'])
        except (AttributeError, TypeError):
            resized = cropped.resize(self.config['resolution'])
        
        return resized
    
    def create_individual_verticals(self, clip_files=None):
        """
        Create individual vertical videos from each clip.
        Each clip is converted to vertical format and saved separately.
        
        Args:
            clip_files (list): List of clip file paths. If None, uses all clips.
            
        Returns:
            list: Paths to generated vertical videos
        """
        print("Creating Individual Vertical Videos...")
        print("=" * 50)
        
        # Get clips to process
        if clip_files is None:
            clip_files = self.get_clip_files()
        
        if not clip_files:
            print("✗ No clips found to process")
            return []
        
        print(f"✓ Found {len(clip_files)} clips to process")
        
        # Process each clip individually
        output_paths = []
        successful = 0
        failed = 0
        failed_clip_queue = []  # Track failed clips for retry
        
        for idx, clip_path in enumerate(clip_files):
            try:
                clip_filename = os.path.basename(clip_path)
                clip_name = Path(clip_filename).stem
                print(f"\nProcessing clip {idx + 1}/{len(clip_files)}: {clip_filename}")
                
                # Generate output filename
                output_name = f"{clip_name}_vertical.mp4"
                output_path = os.path.join(self.output_dir, output_name)
                
                # Skip if file already exists and is > 1MB
                if os.path.exists(output_path):
                    file_size = os.path.getsize(output_path)
                    if file_size > 1024 * 1024:  # > 1MB
                        print(f"⊘ Skipping: {output_name} (already exists, {file_size / (1024*1024):.2f} MB)")
                        output_paths.append(output_path)
                        successful += 1
                        continue
                    else:
                        print(f"  ⚠ Replacing incomplete file: {output_name} ({file_size / 1024:.2f} KB)")
                
                # Get side preference for this clip
                side = self._get_side_for_clip(clip_filename)
                
                # Clean up temp files and force garbage collection before processing
                temp_pattern = os.path.join(self.output_dir, "*TEMP_MPY*")
                for temp_file in glob.glob(temp_pattern):
                    try:
                        os.remove(temp_file)
                    except:
                        pass
                gc.collect()
                time.sleep(3.0)  # Wait before processing
                
                # Load clip
                clip = VideoFileClip(clip_path)
                
                # Convert to vertical
                vertical_clip = self.crop_to_vertical(clip, side=side)
                mode = "Letterbox" if self.config['letterbox_mode'] else "Fill"
                print(f"  ✓ Converted to vertical ({self.config['resolution'][0]}x{self.config['resolution'][1]}) - Mode: {mode}, Side: {side}")
                
                # Write video file with GPU/CPU selection
                write_success = False
                encoder_type = "GPU" if self.gpu_available else "CPU"
                try:
                    print(f"  Writing with {encoder_type}: {output_name}")
                    if self.gpu_available:
                        vertical_clip.write_videofile(
                            output_path,
                            codec='h264_nvenc',
                            audio_codec='aac',
                            fps=self.config['fps'],
                            bitrate='15M',
                            preset='p4',
                            write_logfile=False,
                            ffmpeg_params=[
                                '-gpu', '0',
                                '-rc', 'vbr',
                                '-cq', '23',
                                '-b:v', '15M',
                                '-maxrate', '30M',
                                '-bufsize', '60M',
                            ]
                        )
                    else:
                        vertical_clip.write_videofile(
                            output_path,
                            codec='libx264',
                            audio_codec='aac',
                            fps=self.config['fps'],
                            threads=4,
                            preset='veryfast',
                            write_logfile=False
                        )
                    write_success = True
                except Exception as e:
                    # Try alternative method (CPU fallback)
                    print(f"  ⚠ GPU encoding failed: {e}")
                    print(f"  ⟳ Trying CPU encoding fallback...")
                    gc.collect()
                    time.sleep(2)
                    try:
                        vertical_clip.write_videofile(
                            output_path,
                            codec='libx264',
                            threads=4,
                            preset='veryfast',
                            write_logfile=False
                        )
                        write_success = True
                    except Exception as e2:
                        print(f"  ✗ Alternative method also failed: {e2}")
                        raise
                
                # Close and cleanup
                vertical_clip.close()
                clip.close()
                del vertical_clip
                del clip
                gc.collect()
                
                # Clean up any remaining temp files
                for temp_file in glob.glob(temp_pattern):
                    try:
                        os.remove(temp_file)
                    except:
                        pass
                
                # Wait for complete subprocess cleanup
                time.sleep(3.0)
                
                # Verify file was written successfully
                if write_success and os.path.exists(output_path):
                    file_size = os.path.getsize(output_path)
                    print(f"  ✓ Saved: {output_name} ({file_size / (1024*1024):.2f} MB)")
                    output_paths.append(output_path)
                    successful += 1
                else:
                    print(f"  ✗ Failed to verify: {output_name}")
                    failed += 1
                    failed_clip_queue.append(clip_path)
                
            except Exception as e:
                print(f"  ✗ Error processing clip: {e}")
                failed += 1
                failed_clip_queue.append(clip_path)
        
        # Retry failed clips
        if failed_clip_queue:
            print(f"\n{'='*50}")
            print(f"⟳ Retrying {len(failed_clip_queue)} failed clip(s)...")
            print(f"{'='*50}\n")
            
            random.shuffle(failed_clip_queue)  # Randomize retry order
            
            retry_successful = 0
            retry_failed = 0
            
            for clip_path in failed_clip_queue:
                try:
                    clip_filename = os.path.basename(clip_path)
                    clip_name = Path(clip_filename).stem
                    print(f"⟳ Retrying: {clip_filename}")
                    
                    # Generate output filename
                    output_name = f"{clip_name}_vertical.mp4"
                    output_path = os.path.join(self.output_dir, output_name)
                    
                    # Get side preference
                    side = self._get_side_for_clip(clip_filename)
                    
                    # Clean up and wait
                    temp_pattern = os.path.join(self.output_dir, "*TEMP_MPY*")
                    for temp_file in glob.glob(temp_pattern):
                        try:
                            os.remove(temp_file)
                        except:
                            pass
                    gc.collect()
                    time.sleep(3.0)
                    
                    # Load and convert
                    clip = VideoFileClip(clip_path)
                    vertical_clip = self.crop_to_vertical(clip, side=side)
                    
                    # Try to write (retry)
                    write_success = False
                    try:
                        if self.gpu_available:
                            vertical_clip.write_videofile(
                                output_path,
                                codec='h264_nvenc',
                                audio_codec='aac',
                                fps=self.config['fps'],
                                bitrate='15M',
                                preset='p4',
                                write_logfile=False,
                                ffmpeg_params=[
                                    '-gpu', '0',
                                    '-rc', 'vbr',
                                    '-cq', '23',
                                    '-b:v', '15M',
                                    '-maxrate', '30M',
                                    '-bufsize', '60M',
                                ]
                            )
                        else:
                            vertical_clip.write_videofile(
                                output_path,
                                codec='libx264',
                                audio_codec='aac',
                                fps=self.config['fps'],
                                threads=4,
                                preset='veryfast',
                                write_logfile=False
                            )
                        write_success = True
                    except Exception as e:
                        print(f"  ⚠ Retry attempt failed: {e}")
                    
                    # Cleanup
                    vertical_clip.close()
                    clip.close()
                    del vertical_clip
                    del clip
                    gc.collect()
                    
                    for temp_file in glob.glob(temp_pattern):
                        try:
                            os.remove(temp_file)
                        except:
                            pass
                    
                    time.sleep(3.0)
                    
                    # Verify
                    if write_success and os.path.exists(output_path):
                        file_size = os.path.getsize(output_path)
                        if file_size > 1024 * 1024:
                            print(f"✓ Retry successful: {output_name} ({file_size / (1024*1024):.2f} MB)\n")
                            retry_successful += 1
                            output_paths.append(output_path)
                            successful += 1
                            failed -= 1
                        else:
                            print(f"✗ Retry failed: File too small\n")
                            retry_failed += 1
                    else:
                        print(f"✗ Retry failed: Could not verify file\n")
                        retry_failed += 1
                        
                except Exception as e:
                    print(f"✗ Retry error: {e}\n")
                    retry_failed += 1
            
            print(f"\nRetry results: {retry_successful} successful, {retry_failed} failed\n")
        
        # Summary
        print(f"\n{'='*50}")
        print(f"Processing complete!")
        print(f"  Successful: {successful}")
        print(f"  Failed: {failed}")
        print(f"  Output directory: {self.output_dir}")
        print(f"{'='*50}")
        
        return output_paths
    
    def create_weekly_highlight(self, clip_files=None, output_name=None):
        """
        Create a weekly highlight vertical video from clips.
        
        Args:
            clip_files (list): List of clip file paths. If None, uses all clips.
            output_name (str): Output filename. If None, auto-generates.
            
        Returns:
            str: Path to generated video
        """
        print("Creating Weekly Highlight Vertical Video...")
        print("=" * 50)
        
        # Get clips to process
        if clip_files is None:
            clip_files = self.get_clip_files()
        
        if not clip_files:
            print("✗ No clips found to process")
            return None
        
        print(f"✓ Found {len(clip_files)} clips to process")
        
        # Load and convert clips to vertical
        vertical_clips = []
        for idx, clip_path in enumerate(clip_files):
            try:
                clip_filename = os.path.basename(clip_path)
                print(f"Processing clip {idx + 1}/{len(clip_files)}: {clip_filename}")
                
                # Get side preference for this clip
                side = self._get_side_for_clip(clip_filename)
                
                clip = VideoFileClip(clip_path)
                vertical_clip = self.crop_to_vertical(clip, side=side)
                vertical_clips.append(vertical_clip)
                mode = "Letterbox" if self.config['letterbox_mode'] else "Fill"
                print(f"  ✓ Converted to vertical ({self.config['resolution'][0]}x{self.config['resolution'][1]}) - Mode: {mode}, Side: {side}")
            except Exception as e:
                print(f"  ✗ Error processing clip: {e}")
        
        if not vertical_clips:
            print("✗ No clips successfully processed")
            return None
        
        # Concatenate clips
        print(f"\nCombining {len(vertical_clips)} clips...")
        try:
            if self.config['add_transitions']:
                # Add crossfade transitions
                final_clip = concatenate_videoclips(
                    vertical_clips,
                    method="compose",
                    padding=-self.config['transition_duration']
                )
            else:
                final_clip = concatenate_videoclips(vertical_clips, method="compose")
            
            print(f"✓ Combined clips - Total duration: {final_clip.duration:.2f}s")
        except Exception as e:
            print(f"✗ Error combining clips: {e}")
            return None
        
        # Generate output filename
        if output_name is None:
            date_str = datetime.now().strftime("%Y-%m-%d")
            output_name = f"Weekly_Highlight_{date_str}.mp4"
        
        output_path = os.path.join(self.output_dir, output_name)
        
        # Write video file with GPU/CPU auto-detection
        print(f"\nWriting video to: {output_path}")
        encoder_type = "NVIDIA GPU (NVENC)" if self.gpu_available else "CPU (x264)"
        print(f"Using {encoder_type} encoding...")
        try:
            if self.gpu_available:
                final_clip.write_videofile(
                    output_path,
                    codec='h264_nvenc',
                    audio_codec='aac',
                    fps=self.config['fps'],
                    bitrate='15M',
                    preset='p4',
                    ffmpeg_params=[
                        '-gpu', '0',
                        '-rc', 'vbr',
                        '-cq', '23',
                        '-b:v', '15M',
                        '-maxrate', '30M',
                        '-bufsize', '60M',
                    ]
                )
            else:
                final_clip.write_videofile(
                    output_path,
                    codec='libx264',
                    audio_codec='aac',
                    fps=self.config['fps'],
                    threads=8,
                    preset='veryfast'
                )
            print(f"✓ Video created successfully!")
            print(f"  Resolution: {self.config['resolution'][0]}x{self.config['resolution'][1]}")
            print(f"  Duration: {final_clip.duration:.2f}s")
            print(f"  Location: {output_path}")
        except Exception as e:
            print(f"✗ Error writing video: {e}")
            return None
        finally:
            # Clean up
            final_clip.close()
            for clip in vertical_clips:
                clip.close()
        
        return output_path
    
    def create_ig_fb_vertical(self, clip_files=None, platform='instagram_reels', output_name=None):
        """
        Create Instagram/Facebook optimized vertical video.
        
        Args:
            clip_files (list): List of clip file paths
            platform (str): 'instagram_reels', 'instagram_stories', or 'facebook_stories'
            output_name (str): Output filename
            
        Returns:
            str or list: Path(s) to generated video(s)
        """
        max_durations = {
            'instagram_reels': 90,
            'instagram_stories': 15,
            'facebook_stories': 20
        }
        
        print(f"Creating {platform.replace('_', ' ').title()} Video...")
        print("=" * 50)
        
        # Get clips
        if clip_files is None:
            clip_files = self.get_clip_files()
        
        if not clip_files:
            print("✗ No clips found")
            return None
        
        # Create base vertical video
        vertical_path = self.create_weekly_highlight(clip_files, "temp_vertical.mp4")
        
        if vertical_path is None:
            return None
        
        # Load the created video
        video = VideoFileClip(vertical_path)
        max_duration = max_durations.get(platform, 90)
        
        # Split if needed for Stories
        if platform in ['instagram_stories', 'facebook_stories'] and video.duration > max_duration:
            print(f"\n✓ Video duration ({video.duration:.2f}s) exceeds {platform} limit ({max_duration}s)")
            print(f"  Splitting into segments...")
            
            segments = []
            num_segments = int(video.duration / max_duration) + 1
            
            for i in range(num_segments):
                start = i * max_duration
                end = min((i + 1) * max_duration, video.duration)
                
                try:
                    segment = video.subclipped(start, end)
                except AttributeError:
                    segment = video.subclip(start, end)
                
                seg_name = f"{platform}_Part{i+1}_{datetime.now().strftime('%Y%m%d')}.mp4"
                seg_path = os.path.join(self.output_dir, seg_name)
                
                if self.gpu_available:
                    segment.write_videofile(
                        seg_path,
                        codec='h264_nvenc',
                        audio_codec='aac',
                        fps=self.config['fps'],
                        bitrate='15M',
                        preset='p4',
                        ffmpeg_params=['-gpu', '0', '-rc', 'vbr', '-cq', '23']
                    )
                else:
                    segment.write_videofile(
                        seg_path,
                        codec='libx264',
                        audio_codec='aac',
                        fps=self.config['fps'],
                        threads=8,
                        preset='veryfast'
                    )
                segments.append(seg_path)
                print(f"  ✓ Created segment {i+1}/{num_segments}: {seg_name}")
                segment.close()
            
            video.close()
            os.remove(vertical_path)  # Remove temp file
            return segments
        
        else:
            # Single video within limits
            if output_name is None:
                output_name = f"{platform}_{datetime.now().strftime('%Y%m%d')}.mp4"
            
            final_path = os.path.join(self.output_dir, output_name)
            os.rename(vertical_path, final_path)
            video.close()
            
            print(f"\n✓ Created {platform} video: {output_name}")
            return final_path


def main():
    """Main function for testing vertical video generation."""
    print("Vertical Video Generator")
    print("=" * 50)
    
    # Initialize generator - uses 'output' folder from clip extractor as source
    csv_path = "csv_files/timestamps.csv"
    generator = VerticalVideoGenerator(clips_folder="output", output_dir="vertical_output", csv_path=csv_path)
    
    print(f"CSV file: {csv_path}")
    print(f"Source folder: {generator.clips_folder}")
    print(f"Output folder: {generator.output_dir}")
    
    # Create individual vertical videos for each clip
    print("\nCreating Individual Vertical Videos...")
    generator.create_individual_verticals()
    
    # OPTIONAL: Uncomment to create compiled videos instead
    # print("\n1. Creating Weekly Highlight Vertical Video...")
    # generator.create_weekly_highlight()
    
    # print("\n2. Creating Instagram Reel...")
    # generator.create_ig_fb_vertical(platform='instagram_reels')
    
    # print("\n3. Creating Instagram Stories...")
    # generator.create_ig_fb_vertical(platform='instagram_stories')


if __name__ == "__main__":
    main()
