"""
Video Clip Extractor
Extracts video clips based on timestamps from a CSV file.
Each clip is extracted from (timestamp - 3 seconds) to (timestamp + 2 seconds).
"""

import os
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
        
        # Create output directory if it doesn't exist
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
    
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
                
                # Calculate start and end times (timestamp - 3s, timestamp + 2s)
                start_time = max(0, timestamp - 3)
                end_time = min(video_duration, timestamp + 2)
                
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
                
                # Generate output filename with camera info
                video_name = Path(video_path).stem
                
                # Get placement info
                placement_info = ""
                if 'Placement' in df.columns:
                    placement = row['Placement']
                    placement_info = f"clip{placement:03d}_" if isinstance(placement, (int, float)) else f"{placement}_"
                
                clip_name = f"{video_name}_{camera_name}_{placement_info}{timestamp:.2f}s.mp4"
                output_path = os.path.join(self.output_dir, clip_name)
                
                # Write clip to file (parameters differ between moviepy versions)
                try:
                    clip.write_videofile(
                        output_path,
                        codec='libx264',
                        audio_codec='aac'
                    )
                except Exception as e:
                    # Try with older parameter names
                    clip.write_videofile(
                        output_path,
                        codec='libx264',
                        audio_codec='aac',
                        temp_audiofile='temp-audio.m4a',
                        remove_temp=True,
                        verbose=False,
                        logger=None
                    )
                
                print(f"✓ Extracted clip {idx + 1}/{len(df)}: {clip_name}")
                print(f"  Time range: {start_time:.2f}s - {end_time:.2f}s ({end_time - start_time:.2f}s)\n")
                
                successful_clips += 1
                
                # Close the clip to free resources
                clip.close()
                
            except Exception as e:
                print(f"✗ Error extracting clip {idx + 1}: {e}")
                failed_clips += 1
        
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
