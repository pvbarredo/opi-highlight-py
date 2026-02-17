"""
Video Clip Extractor
Extracts video clips based on timestamps from a CSV file.
Each clip is extracted from (timestamp - 3 seconds) to (timestamp + 3 seconds).
"""

import os
import time
import gc
import glob
import subprocess
import pandas as pd
try:
    from moviepy.editor import VideoFileClip
except ImportError:
    from moviepy import VideoFileClip
from pathlib import Path


class VideoClipExtractor:
    def __init__(self, csv_path, video_folder, output_dir="output"):
        """
        Initialize the Video Clip Extractor.
        
        Args:
            csv_path (str): Path to the CSV file containing timestamps
            video_folder (str): Path to the folder containing video files
            output_dir (str): Directory to save extracted clips
        """
        self.csv_path = csv_path
        self.video_folder = video_folder
        self.output_dir = output_dir
        self.video_cache = {}  # Cache loaded videos
        self.gpu_available = self._check_gpu_availability()
        
        # Create output directory if it doesn't exist
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
    
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
            
            # Check if ffmpeg supports h264_nvenc codec
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
    
    def get_overlay_ffmpeg_params(self, camera, timestamp_str, side, placement, clip_width, clip_height):
        """
        Generate FFmpeg drawtext parameters for GPU-accelerated overlay.
        Text is burned in during encoding for better performance.
        
        Args:
            camera (str): Camera name (e.g., 'Cam1')
            timestamp_str (str): Timestamp in HH:MM:SS format
            side (str): Side value from CSV ('left', 'right', or 'N/A')
            placement: Placement/clip number
            clip_width (int): Width of the video clip
            clip_height (int): Height of the video clip
            
        Returns:
            list: FFmpeg filter parameters for text overlay
        """
        # Escape all colons in the text content for FFmpeg drawtext filter
        # FFmpeg uses : as parameter separator, so colons in text must be escaped
        timestamp_escaped = timestamp_str.replace(':', '\\:')
        camera_escaped = str(camera).replace(':', '\\:')
        side_escaped = str(side).replace(':', '\\:')
        
        # Create debug text with escaped colons
        debug_text = f"Cam\\: {camera_escaped} | Time\\: {timestamp_escaped} | Side\\: {side_escaped} | #{placement}"
        
        # Position text in bottom right corner with padding
        x_pos = "w-tw-20"  # 20 pixels from right edge
        y_pos = "h-th-20"  # 20 pixels from bottom edge
        
        # Build drawtext filter
        drawtext_filter = (
            f"drawtext=text='{debug_text}'"
            f":fontfile=C\\\\:/Windows/Fonts/arial.ttf"
            f":fontsize=18"
            f":fontcolor=white"
            f":borderw=2"
            f":bordercolor=black@0.5"
            f":x={x_pos}"
            f":y={y_pos}"
        )
        
        return ['-vf', drawtext_filter]
    
    def find_video_file(self, camera_name):
        """
        Find a video file in the video folder that contains the camera name.
        
        Args:
            camera_name (str): Camera identifier (e.g., 'Cam1')
            
        Returns:
            str: Path to the video file, or None if not found
        """
        video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv']
        
        try:
            for filename in os.listdir(self.video_folder):
                file_path = os.path.join(self.video_folder, filename)
                
                # Check if it's a file with a video extension
                if os.path.isfile(file_path):
                    file_ext = os.path.splitext(filename)[1].lower()
                    if file_ext in video_extensions:
                        # Check if camera name is in the filename
                        if str(camera_name).lower() in filename.lower():
                            return file_path
        except Exception as e:
            print(f"✗ Error searching for video: {e}")
        
        return None
    
    def get_video(self, camera_name):
        """
        Get or load a video file for the specified camera.
        Uses caching to avoid reloading the same video multiple times.
        
        Args:
            camera_name (str): Camera identifier
            
        Returns:
            tuple: (VideoFileClip, video_path) or (None, None) if not found
        """
        # Check cache first
        if camera_name in self.video_cache:
            return self.video_cache[camera_name]
        
        # Find video file
        video_path = self.find_video_file(camera_name)
        if not video_path:
            print(f"✗ No video file found for camera: {camera_name}")
            return None, None
        
        # Load video
        try:
            video = VideoFileClip(video_path)
            self.video_cache[camera_name] = (video, video_path)
            print(f"✓ Loaded video for {camera_name}: {os.path.basename(video_path)}")
            print(f"  Duration: {video.duration:.2f} seconds")
            return video, video_path
        except Exception as e:
            print(f"✗ Error loading video for {camera_name}: {e}")
            return None, None
    
    def parse_timestamp(self, timestamp):
        """
        Convert timestamp string to seconds.
        Supports formats: HH:MM:SS, MM:SS, or just seconds
        
        Args:
            timestamp: Timestamp as string or number
            
        Returns:
            float: Time in seconds
        """
        if isinstance(timestamp, (int, float)):
            return float(timestamp)
        
        timestamp = str(timestamp).strip()
        parts = timestamp.split(':')
        
        if len(parts) == 3:  # HH:MM:SS
            hours, minutes, seconds = parts
            return int(hours) * 3600 + int(minutes) * 60 + float(seconds)
        elif len(parts) == 2:  # MM:SS
            minutes, seconds = parts
            return int(minutes) * 60 + float(seconds)
        else:  # Just seconds
            return float(parts[0])
    
    def seconds_to_hhmmss(self, seconds):
        """
        Convert seconds to HH_MM_SS format.
        
        Args:
            seconds (float): Time in seconds
            
        Returns:
            str: Formatted time as HH_MM_SS
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}_{minutes:02d}_{secs:02d}"
    
    def extract_clips(self):
        """
        Read CSV file and extract video clips based on timestamps.
        """
        # Read CSV file (skip first row if it contains date header)
        try:
            # Try reading normally first
            df = pd.read_csv(self.csv_path)
            
            # Check if first row might be a date header
            if 'Date' in df.columns and len(df.columns) > 3:
                # Skip first row and re-read
                df = pd.read_csv(self.csv_path, skiprows=1)
            
            print(f"✓ Loaded CSV file: {self.csv_path}")
            print(f"  Found {len(df)} timestamps to process")
        except Exception as e:
            print(f"✗ Error reading CSV file: {e}")
            return
        
        # Check if timestamp column exists
        timestamp_col = None
        for col in ['timestamp', 'time', 'Time', 'Timestamp']:
            if col in df.columns:
                timestamp_col = col
                break
        
        if timestamp_col is None:
            print(f"✗ Error: No timestamp column found in CSV")
            print(f"  Available columns: {', '.join(df.columns)}")
            return
        
        # Check if Camera column exists
        if 'Camera' not in df.columns:
            print(f"✗ Error: No Camera column found in CSV")
            print(f"  Available columns: {', '.join(df.columns)}")
            return
        
        # Extract clips
        successful_clips = 0
        failed_clips = 0
        failed_clip_queue = []  # Track failed clips for retry
        
        print(f"\nProcessing clips...\n")
        
        for idx, row in df.iterrows():
            try:
                # Get camera name
                camera_name = row['Camera']
                
                # Get or load the video for this camera
                video, video_path = self.get_video(camera_name)
                if video is None:
                    print(f"⚠ Skipping clip {idx + 1}: No video found for {camera_name}")
                    failed_clips += 1
                    continue
                
                video_duration = video.duration
                
                # Get timestamp and convert to seconds
                timestamp = self.parse_timestamp(row[timestamp_col])
                
                # Calculate start and end times (timestamp - 3s, timestamp + 3s)
                start_time = max(0, timestamp - 3)
                end_time = min(video_duration, timestamp + 3)
                
                # Skip if the clip would be too short
                if end_time - start_time < 1:
                    print(f"⚠ Skipping clip {idx + 1}: Too short ({end_time - start_time:.2f}s)")
                    failed_clips += 1
                    continue
                
                # Extract clip - use subclipped for newer moviepy versions
                try:
                    clip = video.subclipped(start_time, end_time)
                except AttributeError:
                    clip = video.subclip(start_time, end_time)
                
                # Generate output filename with new naming convention
                # Format: Cam2-02112026_clip01_HH_MM_SS.mp4
                video_name = Path(video_path).stem
                
                # Get placement/clip number
                clip_number = ""
                placement_num = idx + 1
                if 'Placement' in df.columns:
                    placement = row['Placement']
                    placement_num = int(placement) if isinstance(placement, (int, float)) else idx + 1
                    clip_number = f"clip{placement_num:02d}"
                else:
                    clip_number = f"clip{placement_num:02d}"
                
                # Get Side information for debug overlay
                side = 'N/A'
                if 'Side' in df.columns:
                    side = str(row['Side']).strip() if pd.notna(row['Side']) else 'N/A'
                
                # Convert timestamp to HH_MM_SS format
                time_str = self.seconds_to_hhmmss(timestamp)
                
                clip_name = f"{video_name}_{clip_number}_{time_str}.mp4"
                output_path = os.path.join(self.output_dir, clip_name)
                
                # Skip if file already exists and is > 1MB
                if os.path.exists(output_path):
                    file_size = os.path.getsize(output_path)
                    if file_size > 1024 * 1024:  # > 1MB
                        print(f"⊘ Skipping clip {idx + 1}/{len(df)}: {clip_name} (already exists, {file_size / (1024*1024):.2f} MB)")
                        successful_clips += 1
                        clip.close()
                        continue
                    else:
                        print(f"  ⚠ Replacing incomplete file: {clip_name} ({file_size / 1024:.2f} KB)")
                
                # Clean up temp files and force garbage collection before writing
                temp_pattern = os.path.join(self.output_dir, "*TEMP_MPY*")
                for temp_file in glob.glob(temp_pattern):
                    try:
                        os.remove(temp_file)
                    except:
                        pass
                gc.collect()
                
                # Get overlay parameters for GPU-accelerated text rendering
                overlay_params = self.get_overlay_ffmpeg_params(
                    camera_name, 
                    time_str.replace('_', ':'), 
                    side, 
                    placement_num,
                    int(clip.w),
                    int(clip.h)
                )
                
                # Write clip to file with GPU/CPU selection
                write_success = False
                try:
                    if self.gpu_available:
                        # GPU encoding with NVENC + GPU-accelerated overlay
                        base_params = [
                            '-c:v', 'h264_nvenc',
                            '-preset', 'p4',
                            '-rc', 'vbr',
                            '-cq', '28',
                            '-b:v', '0',
                            '-bufsize', '10M',
                            '-maxrate', '50M',
                            '-bf', '3',
                            '-g', '250',
                            '-movflags', '+faststart'
                        ]
                        # Merge overlay params with encoding params
                        all_params = overlay_params + base_params
                        
                        clip.write_videofile(
                            output_path,
                            fps=clip.fps,
                            preset='medium',
                            audio_codec='aac',
                            ffmpeg_params=all_params
                        )
                    else:
                        # CPU encoding with overlay
                        base_params = ['-crf', '23']
                        all_params = overlay_params + base_params
                        
                        clip.write_videofile(
                            output_path,
                            codec='libx264',
                            audio_codec='aac',
                            threads=4,
                            preset='veryfast',
                            write_logfile=False,
                            ffmpeg_params=all_params
                        )
                    write_success = True
                except Exception as e:
                    # Fallback to CPU if GPU fails
                    print(f"  ⚠ First attempt failed: {e}")
                    print(f"  ⟳ Trying CPU encoding fallback...")
                    gc.collect()
                    try:
                        # Fallback without overlay if needed
                        clip.write_videofile(
                            output_path,
                            codec='libx264',
                            threads=4,
                            preset='ultrafast',
                            write_logfile=False
                        )
                        write_success = True
                    except Exception as e2:
                        print(f"  ✗ Fallback also failed: {e2}")
                        raise
                
                # Close the clip and force cleanup
                clip.close()
                del clip
                gc.collect()
                
                # Clean up any remaining temp files
                temp_pattern = os.path.join(self.output_dir, "*TEMP_MPY*")
                for temp_file in glob.glob(temp_pattern):
                    try:
                        os.remove(temp_file)
                    except:
                        pass
                
                # Verify file was written successfully
                if write_success and os.path.exists(output_path):
                    file_size = os.path.getsize(output_path)
                    print(f"✓ Extracted clip {idx + 1}/{len(df)}: {clip_name} ({file_size / (1024*1024):.2f} MB)")
                    print(f"  Time range: {start_time:.2f}s - {end_time:.2f}s ({end_time - start_time:.2f}s)")
                    print(f"  Timestamp: {time_str.replace('_', ':')}\n")
                    successful_clips += 1
                else:
                    print(f"✗ Failed to verify clip {idx + 1}: {clip_name}\n")
                    failed_clips += 1
                
            except Exception as e:
                print(f"✗ Error extracting clip {idx + 1}: {e}")
                failed_clips += 1
                # Add to retry queue
                failed_clip_queue.append((idx, row.copy()))
        
        # Retry failed clips
        if failed_clip_queue:
            print(f"\n{'='*50}")
            print(f"⟳ Retrying {len(failed_clip_queue)} failed clip(s)...")
            print(f"{'='*50}\n")
            
            import random
            random.shuffle(failed_clip_queue)  # Randomize retry order
            
            retry_successful = 0
            retry_failed = 0
            
            for idx, row in failed_clip_queue:
                try:
                    print(f"⟳ Retrying clip {idx + 1}/{len(df)}...")
                    
                    # Get camera name
                    camera_name = row['Camera']
                    
                    # Get or load the video for this camera
                    video, video_path = self.get_video(camera_name)
                    if video is None:
                        print(f"⚠ Skipping retry: No video found for {camera_name}\n")
                        retry_failed += 1
                        continue
                    
                    video_duration = video.duration
                    
                    # Get timestamp and convert to seconds
                    timestamp = self.parse_timestamp(row[timestamp_col])
                    
                    # Calculate start and end times
                    start_time = max(0, timestamp - 3)
                    end_time = min(video_duration, timestamp + 3)
                    
                    # Extract clip
                    try:
                        clip = video.subclipped(start_time, end_time)
                    except AttributeError:
                        clip = video.subclip(start_time, end_time)
                    
                    # Generate filename
                    video_name = Path(video_path).stem
                    placement_num = idx + 1
                    if 'Placement' in df.columns:
                        placement = row['Placement']
                        placement_num = int(placement) if isinstance(placement, (int, float)) else idx + 1
                        clip_number = f"clip{placement_num:02d}"
                    else:
                        clip_number = f"clip{placement_num:02d}"
                    
                    # Get Side information for debug overlay
                    side = 'N/A'
                    if 'Side' in df.columns:
                        side = str(row['Side']).strip() if pd.notna(row['Side']) else 'N/A'
                    
                    time_str = self.seconds_to_hhmmss(timestamp)
                    clip_name = f"{video_name}_{clip_number}_{time_str}.mp4"
                    output_path = os.path.join(self.output_dir, clip_name)
                    
                    # Clean up and wait
                    temp_pattern = os.path.join(self.output_dir, "*TEMP_MPY*")
                    for temp_file in glob.glob(temp_pattern):
                        try:
                            os.remove(temp_file)
                        except:
                            pass
                    gc.collect()

                    
                    # Get overlay parameters for GPU-accelerated text rendering
                    overlay_params = self.get_overlay_ffmpeg_params(
                        camera_name, 
                        time_str.replace('_', ':'), 
                        side, 
                        placement_num,
                        int(clip.w),
                        int(clip.h)
                    )
                    
                    # Try to write (retry attempt)
                    write_success = False
                    try:
                        if self.gpu_available:
                            # GPU encoding with overlay
                            base_params = [
                                '-c:v', 'h264_nvenc',
                                '-preset', 'p4',
                                '-rc', 'vbr',
                                '-cq', '28',
                                '-b:v', '0',
                                '-bufsize', '10M',
                                '-maxrate', '50M',
                                '-bf', '3',
                                '-g', '250',
                                '-movflags', '+faststart'
                            ]
                            all_params = overlay_params + base_params
                            
                            clip.write_videofile(
                                output_path,
                                fps=clip.fps,
                                preset='medium',
                                audio_codec='aac',
                                ffmpeg_params=all_params
                            )
                        else:
                            # CPU encoding with overlay
                            base_params = ['-crf', '23']
                            all_params = overlay_params + base_params
                            
                            clip.write_videofile(
                                output_path,
                                codec='libx264',
                                audio_codec='aac',
                                threads=4,
                                preset='veryfast',
                                write_logfile=False,
                                ffmpeg_params=all_params
                            )
                        write_success = True
                    except Exception as e:
                        print(f"  ⚠ Retry attempt failed: {e}")
                    
                    # Cleanup
                    clip.close()
                    del clip
                    gc.collect()
                    
                    for temp_file in glob.glob(temp_pattern):
                        try:
                            os.remove(temp_file)
                        except:
                            pass
                    
                    # Verify
                    if write_success and os.path.exists(output_path):
                        file_size = os.path.getsize(output_path)
                        if file_size > 1024 * 1024:
                            print(f"✓ Retry successful: {clip_name} ({file_size / (1024*1024):.2f} MB)\n")
                            retry_successful += 1
                            successful_clips += 1
                            failed_clips -= 1
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
        
        # Close all cached videos
        for camera_name, (video, _) in self.video_cache.items():
            video.close()
            print(f"✓ Closed video for {camera_name}")
        
        # Final cleanup - remove all TEMP_MPY files from output directory and root
        print(f"\nCleaning up temporary files...")
        cleanup_count = 0
        
        # Clean output directory
        for temp_file in glob.glob(os.path.join(self.output_dir, "*TEMP_MPY*")):
            try:
                os.remove(temp_file)
                cleanup_count += 1
            except:
                pass
        
        # Clean root/current directory
        for temp_file in glob.glob("*TEMP_MPY*"):
            try:
                os.remove(temp_file)
                cleanup_count += 1
            except:
                pass
        
        if cleanup_count > 0:
            print(f"✓ Removed {cleanup_count} temporary file(s)")
        
        # Summary
        print(f"\n{'='*50}")
        print(f"Extraction complete!")
        print(f"  Successful: {successful_clips}")
        print(f"  Failed: {failed_clips}")
        print(f"  Output directory: {self.output_dir}")
        print(f"{'='*50}")


def main():
    """Main function to run the video clip extractor."""
    print("Video Clip Extractor")
    print("=" * 50)
    
    # Example usage - modify these paths as needed
    csv_file = "csv_files/timestamps.csv"
    video_folder = r"C:\Videos\February 11 2026 - Fray Juan Clemente"  # Folder containing video files
    output_folder = "output"
    
    # Check if files/folders exist
    if not os.path.exists(csv_file):
        print(f"✗ CSV file not found: {csv_file}")
        print(f"  Please place your CSV file in the 'csv_files' folder")
        return
    
    if not os.path.exists(video_folder):
        print(f"✗ Video folder not found: {video_folder}")
        print(f"  Please create the 'video_files' folder and add your videos")
        return
    
    if not os.path.isdir(video_folder):
        print(f"✗ Video path is not a folder: {video_folder}")
        print(f"  Please provide a folder path containing video files")
        return
    
    # Create extractor and process
    extractor = VideoClipExtractor(csv_file, video_folder, output_folder)
    extractor.extract_clips()
    
if __name__ == "__main__":
    main()
