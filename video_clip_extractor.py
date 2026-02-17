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
            # Check if ffmpeg supports h264_nvenc codec
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
                if 'Placement' in df.columns:
                    placement = row['Placement']
                    clip_number = f"clip{int(placement):02d}" if isinstance(placement, (int, float)) else f"clip{idx+1:02d}"
                else:
                    clip_number = f"clip{idx+1:02d}"
                
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
                time.sleep(0.5)
                
                # Write clip to file with GPU/CPU selection
                write_success = False
                try:
                    if self.gpu_available:
                        # Try GPU encoding first
                        clip.write_videofile(
                            output_path,
                            codec='h264_nvenc',
                            audio_codec='aac',
                            bitrate='15M',
                            preset='p4',
                            write_logfile=False,
                            ffmpeg_params=['-gpu', '0', '-rc', 'vbr', '-cq', '23']
                        )
                    else:
                        # Use CPU encoding
                        clip.write_videofile(
                            output_path,
                            codec='libx264',
                            audio_codec='aac',
                            threads=4,
                            preset='veryfast',
                            write_logfile=False
                        )
                    write_success = True
                except Exception as e:
                    # Fallback to CPU if GPU fails
                    print(f"  ⚠ First attempt failed: {e}")
                    print(f"  ⟳ Trying CPU encoding fallback...")
                    gc.collect()
                    time.sleep(2)
                    try:
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
                
                # Wait for complete subprocess cleanup
                time.sleep(2.0)
                
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
                    if 'Placement' in df.columns:
                        placement = row['Placement']
                        clip_number = f"clip{int(placement):02d}" if isinstance(placement, (int, float)) else f"clip{idx+1:02d}"
                    else:
                        clip_number = f"clip{idx+1:02d}"
                    
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
                    time.sleep(3.0)
                    
                    # Try to write (retry attempt)
                    write_success = False
                    try:
                        if self.gpu_available:
                            clip.write_videofile(
                                output_path,
                                codec='h264_nvenc',
                                audio_codec='aac',
                                bitrate='15M',
                                preset='p4',
                                write_logfile=False,
                                ffmpeg_params=['-gpu', '0', '-rc', 'vbr', '-cq', '23']
                            )
                        else:
                            clip.write_videofile(
                                output_path,
                                codec='libx264',
                                audio_codec='aac',
                                threads=4,
                                preset='veryfast',
                                write_logfile=False
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
                    
                    time.sleep(3.0)
                    
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
    
    # Optional: Create vertical videos after extraction
    print("\n" + "=" * 50)
    print("Clips extracted successfully!")
    print("\nNext steps:")
    print("  1. Review clips in 'output/' folder")
    print("  2. Create vertical videos: python vertical_video_generator.py")
    print("     - Weekly highlights compilation")
    print("     - Instagram/Facebook ready formats")
    print("=" * 50)


if __name__ == "__main__":
    main()
