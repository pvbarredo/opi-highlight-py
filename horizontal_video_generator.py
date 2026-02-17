"""
Horizontal Video Generator
Creates horizontal format videos (16:9) from extracted highlight clips
with smart zooming and side-based trimming for YouTube, streaming platforms
"""

import os
import sys
import time
import tempfile
import subprocess
from pathlib import Path
from datetime import datetime
import pandas as pd
import re
import json
try:
    from moviepy.editor import VideoFileClip
except ImportError:
    from moviepy import VideoFileClip


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
        self.clip_data = {}  # Maps placement number to full clip data (camera, timestamp, side)
        self.gpu_available = self._check_gpu_availability()
        self.ffmpeg_path = self._get_ffmpeg_path()
        
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
    
    def _get_ffmpeg_path(self):
        """Get the FFmpeg executable path."""
        try:
            from moviepy.config import get_setting
            return get_setting("FFMPEG_BINARY")
        except:
            try:
                import imageio_ffmpeg
                return imageio_ffmpeg.get_ffmpeg_exe()
            except:
                return 'ffmpeg'
    
    def _load_side_info(self):
        """
        Load clip information from CSV file including camera, timestamp, and side.
        Maps clip placement numbers to their data for overlay display.
        """
        try:
            # Read CSV (skip date header row)
            df = pd.read_csv(self.csv_path)
            if 'Date' in df.columns and len(df.columns) > 3:
                df = pd.read_csv(self.csv_path, skiprows=1)
            
            # Find timestamp column
            timestamp_col = None
            for col in ['timestamp', 'time', 'Time', 'Timestamp']:
                if col in df.columns:
                    timestamp_col = col
                    break
            
            # Create mappings of placement to side and full data
            if 'Placement' in df.columns and 'Camera' in df.columns and timestamp_col:
                for _, row in df.iterrows():
                    placement = row['Placement']
                    side = str(row['Side']).lower().strip() if 'Side' in df.columns and pd.notna(row['Side']) else 'center'
                    camera = str(row['Camera']).strip() if pd.notna(row['Camera']) else 'Unknown'
                    timestamp = str(row[timestamp_col]).strip() if pd.notna(row[timestamp_col]) else '00:00:00'
                    
                    self.side_mapping[placement] = side
                    self.clip_data[placement] = {
                        'camera': camera,
                        'timestamp': timestamp,
                        'side': side
                    }
                print(f"✓ Loaded clip data for {len(self.clip_data)} clips")
            else:
                print("⚠ CSV missing required columns (Placement, Camera, or timestamp)")
        except Exception as e:
            print(f"⚠ Could not load CSV clip data: {e}")
            print("  Clips will be processed without overlay data")
    
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
    
    def _get_video_info(self, video_path):
        """
        Get video dimensions and duration using FFprobe.
        
        Args:
            video_path (str): Path to video file
            
        Returns:
            dict: {'width': int, 'height': int, 'duration': float}
        """
        try:
            cmd = [
                self.ffmpeg_path.replace('ffmpeg', 'ffprobe'),
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_streams',
                video_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
            data = json.loads(result.stdout)
            
            for stream in data.get('streams', []):
                if stream.get('codec_type') == 'video':
                    return {
                        'width': int(stream.get('width', 0)),
                        'height': int(stream.get('height', 0)),
                        'duration': float(stream.get('duration', 0))
                    }
        except:
            # Fallback to MoviePy if ffprobe fails
            try:
                clip = VideoFileClip(video_path)
                info = {'width': clip.w, 'height': clip.h, 'duration': clip.duration}
                clip.close()
                return info
            except:
                pass
        return {'width': 0, 'height': 0, 'duration': 0}
    
    def _calculate_crop_params(self, original_width, original_height, side='center'):
        """
        Calculate crop and scale parameters for FFmpeg filter.
        
        Args:
            original_width (int): Original video width
            original_height (int): Original video height
            side (str): 'left', 'right', or 'center'
            
        Returns:
            dict: {'crop_x': int, 'crop_y': int, 'crop_w': int, 'crop_h': int}
        """
        zoom = self.config['zoom_factor']
        trim_percent = self.config['opposite_side_trim']
        
        # Calculate crop dimensions (zoom effect)
        crop_width = int(original_width / zoom)
        crop_height = int(original_height / zoom)
        
        # For stretched look, use full width with minimal trim
        # This creates wider field of view
        target_visible_width = int(crop_width * (1 - trim_percent * 0.5))  # Reduced trim by half for wider view
        target_visible_height = crop_height
        
        # Calculate crop position
        if side == 'left':
            crop_x = 0
            crop_y = (original_height - target_visible_height) // 2
        elif side == 'right':
            crop_x = original_width - target_visible_width
            crop_y = (original_height - target_visible_height) // 2
        else:  # center
            crop_x = (original_width - target_visible_width) // 2
            crop_y = (original_height - target_visible_height) // 2
        
        return {
            'crop_x': crop_x,
            'crop_y': crop_y,
            'crop_w': target_visible_width,
            'crop_h': target_visible_height
        }
    
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
    
    def create_weekly_highlight_gpu(self, clip_files=None, output_name=None):
        """
        Create a weekly highlight horizontal video using GPU-accelerated FFmpeg filters.
        Bypasses MoviePy processing for maximum GPU utilization.
        
        Args:
            clip_files (list): List of clip file paths. If None, uses all clips.
            output_name (str): Output filename. If None, auto-generates.
            
        Returns:
            str: Path to generated video
        """
        print("Creating Weekly Highlight Horizontal Video (GPU-Accelerated)...")
        print("=" * 50)
        
        # Get clips to process
        if clip_files is None:
            clip_files = self.get_clip_files()
        
        if not clip_files:
            print("✗ No clips found to process")
            return None
        
        print(f"✓ Found {len(clip_files)} clips to process")
        
        # Generate output filename
        if output_name is None:
            date_str = datetime.now().strftime("%Y-%m-%d")
            output_name = f"Weekly_Highlight_Horizontal_{date_str}.mp4"
        
        output_path = os.path.join(self.output_dir, output_name)
        target_width, target_height = self.config['resolution']
        
        # Build FFmpeg command with filter_complex
        cmd = [self.ffmpeg_path]
        
        # Add all input files
        for clip_path in clip_files:
            cmd.extend(['-i', clip_path])
        
        # Build filter chain
        filter_parts = []
        total_duration = 0
        
        for idx, clip_path in enumerate(clip_files):
            clip_filename = os.path.basename(clip_path)
            side = self._get_side_for_clip(clip_filename)
            
            # Get video dimensions
            video_info = self._get_video_info(clip_path)
            if video_info['width'] == 0:
                print(f"⚠ Skipping clip {idx + 1}: Could not read video info")
                continue
            
            total_duration += video_info['duration']
            
            # Calculate crop parameters
            crop_params = self._calculate_crop_params(
                video_info['width'],
                video_info['height'],
                side
            )
            
            # Extract clip number from filename to lookup CSV data
            # Format: Cam1-02112026_clip01_00_29_11.mp4
            clip_num_match = re.search(r'clip(\d+)', clip_filename, re.IGNORECASE)
            placement = int(clip_num_match.group(1)) if clip_num_match else (idx + 1)
            
            # Get camera and timestamp from CSV data
            camera = "Unknown"
            timestamp = "00:00:00"
            
            if placement in self.clip_data:
                camera = self.clip_data[placement]['camera']
                timestamp = self.clip_data[placement]['timestamp']
                
                # Convert timestamp to HH:MM:SS if needed
                if ':' not in timestamp:
                    # Assume it's in seconds
                    try:
                        secs = float(timestamp)
                        hours = int(secs // 3600)
                        minutes = int((secs % 3600) // 60)
                        seconds = int(secs % 60)
                        timestamp = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                    except:
                        pass
            
            # Escape special characters for FFmpeg drawtext
            # Single backslash for escaping colons in the filter file
            camera_escaped = camera.replace(':', '\\:')
            timestamp_escaped = timestamp.replace(':', '\\:')
            overlay_text = f"Cam\\: {camera_escaped} | Time\\: {timestamp_escaped}"
            
            print(f"Processing clip {idx + 1}/{len(clip_files)}: {clip_filename}")
            print(f"  Side: {side}, Crop: {crop_params['crop_w']}x{crop_params['crop_h']}, Overlay: {camera} @ {timestamp}")
            
            # Create filter for this clip: crop -> scale -> overlay
            # Note: Using forward slashes for Windows paths works in FFmpeg
            filter_parts.append(
                f"[{idx}:v]crop={crop_params['crop_w']}:{crop_params['crop_h']}:"
                f"{crop_params['crop_x']}:{crop_params['crop_y']},"
                f"scale={target_width}:{target_height},"
                f"drawtext=text='{overlay_text}'"
                f":fontfile=C\\\\:/Windows/Fonts/arial.ttf"
                f":fontsize=20"
                f":fontcolor=white"
                f":borderw=2"
                f":bordercolor=black@0.8"
                f":x=20"
                f":y=20[v{idx}]"
            )
        
        # Concatenate all processed clips
        concat_inputs = ''.join([f"[v{i}][{i}:a]" for i in range(len(clip_files))])
        filter_parts.append(f"{concat_inputs}concat=n={len(clip_files)}:v=1:a=1[outv][outa]")
        
        # Complete filter_complex
        filter_complex = ';'.join(filter_parts)
        
        # Write filter to temporary file to avoid command line length limits
        filter_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8')
        filter_file.write(filter_complex)
        filter_file.close()
        
        print(f"\n✓ Filter file created: {filter_file.name}")
        # Debug: Show first filter for verification
        if filter_parts:
            print(f"  Sample filter: {filter_parts[0][:150]}...")
        
        cmd.extend(['-filter_complex_script', filter_file.name])
        cmd.extend(['-map', '[outv]', '-map', '[outa]'])
        
        # Add encoding parameters
        encoder_type = "NVIDIA GPU (NVENC)" if self.gpu_available else "CPU (x264)"
        print(f"\nUsing {encoder_type} encoding...")
        
        if self.gpu_available:
            # GPU encoding - Optimized for ~150MB file size
            cmd.extend([
                '-c:v', 'h264_nvenc',
                '-preset', 'p4',
                '-rc', 'vbr',
                '-cq', '30',  # Increased from 23 for smaller file size
                '-b:v', '0',
                '-bufsize', '5M',  # Reduced buffer for smaller file
                '-maxrate', '25M',  # Reduced max rate
                '-bf', '3',
                '-g', '250',
                '-c:a', 'aac',
                '-b:a', '128k',  # Reduced audio bitrate
                '-movflags', '+faststart'
            ])
        else:
            # CPU encoding
            cmd.extend([
                '-c:v', 'libx264',
                '-preset', 'veryfast',
                '-crf', '26',  # Increased from 23 for smaller file size
                '-c:a', 'aac',
                '-b:a', '128k'
            ])
        
        cmd.extend(['-y', output_path])
        
        # Execute FFmpeg command with tqdm-style progress
        print(f"\nEncoding with {encoder_type}...")
        print(f"Total duration: {total_duration:.1f}s")
        print(f"━" * 50)
        
        try:
            # Run FFmpeg with real-time output
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            # Track progress with tqdm-style display
            start_time = time.time()
            last_time_sec = 0
            error_lines = []  # Capture error messages
            
            for line in process.stdout:
                line = line.strip()
                # Save error lines for debugging
                if 'error' in line.lower() or 'invalid' in line.lower() or 'failed' in line.lower():
                    error_lines.append(line)
                
                # Parse FFmpeg output for time
                if 'time=' in line:
                    time_match = re.search(r'time=(\d{2}):(\d{2}):(\d{2})', line)
                    fps_match = re.search(r'fps=\s*(\d+\.?\d*)', line)
                    speed_match = re.search(r'speed=\s*(\d+\.?\d*)x', line)
                    
                    if time_match:
                        hours = int(time_match.group(1))
                        minutes = int(time_match.group(2))
                        seconds = int(time_match.group(3))
                        current_sec = hours * 3600 + minutes * 60 + seconds
                        
                        if total_duration > 0 and current_sec != last_time_sec:
                            # Calculate progress
                            progress = min(current_sec / total_duration, 1.0)
                            percentage = int(progress * 100)
                            
                            # Build progress bar
                            bar_length = 50
                            filled = int(bar_length * progress)
                            bar = '█' * filled + '░' * (bar_length - filled)
                            
                            # Get metrics
                            fps = fps_match.group(1) if fps_match else '0'
                            speed = speed_match.group(1) if speed_match else '0'
                            elapsed = time.time() - start_time
                            
                            # Calculate ETA
                            if progress > 0:
                                eta = (elapsed / progress) - elapsed
                                eta_str = f"{int(eta//60):02d}:{int(eta%60):02d}"
                            else:
                                eta_str = "--:--"
                            
                            # Display tqdm-style progress
                            print(f"\rProgress: {percentage:3d}%|{bar}| {current_sec:.0f}/{total_duration:.0f}s "
                                  f"[{int(elapsed//60):02d}:{int(elapsed%60):02d}<{eta_str}, {fps}fps, {speed}x]",
                                  end='', flush=True)
                            
                            last_time_sec = current_sec
            
            process.wait()
            result_code = process.returncode
            
            # Clear progress line and show completion
            print(f"\rProgress: 100%|{'█'*50}| Completed!{' '*50}")
            print(f"━" * 50)
            
            if result_code == 0:
                file_size = os.path.getsize(output_path) / (1024 * 1024)
                print(f"✓ Video created successfully!")
                print(f"  Resolution: {target_width}x{target_height}")
                print(f"  Clips combined: {len(clip_files)}")
                print(f"  Zoom: {int((self.config['zoom_factor'] - 1) * 100)}%")
                print(f"  Trim: {int(self.config['opposite_side_trim'] * 100)}% from opposite side")
                print(f"  Encoder: {encoder_type}")
                print(f"  File size: {file_size:.2f} MB")
                print(f"  Location: {output_path}")
                return output_path
            else:
                print(f"✗ FFmpeg encoding failed with code {result_code}")
                
                # Show error messages if captured
                if error_lines:
                    print(f"\n⚠ FFmpeg errors:")
                    for err_line in error_lines[-10:]:  # Show last 10 error lines
                        print(f"  {err_line}")
                    
                    # Also print the filter file for debugging
                    print(f"\n⚠ Filter file location: {filter_file.name}")
                    print(f"  You can inspect it to debug the filter syntax")
                
                # Try CPU fallback if GPU failed
                if self.gpu_available:
                    print("\n⟳ Retrying with CPU encoding...")
                    # Update command with CPU encoding
                    cmd_cpu = cmd[:cmd.index('-c:v') if '-c:v' in cmd else len(cmd)]
                    cmd_cpu.extend([
                        '-c:v', 'libx264',
                        '-preset', 'ultrafast',
                        '-crf', '26',
                        '-c:a', 'aac',
                        '-b:a', '128k',
                        '-y', output_path
                    ])
                    
                    result = subprocess.run(cmd_cpu, capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
                    if result.returncode == 0:
                        file_size = os.path.getsize(output_path) / (1024 * 1024)
                        print(f"✓ Video created with CPU fallback ({file_size:.2f} MB)")
                        return output_path
                    else:
                        print(f"✗ CPU fallback also failed: {result.stderr}")
                
                return None
        except Exception as e:
            print(f"✗ Error running FFmpeg: {e}")
            return None
        finally:
            # Clean up temporary filter file
            try:
                if os.path.exists(filter_file.name):
                    os.unlink(filter_file.name)
            except:
                pass
    
    def create_weekly_highlight(self, clip_files=None, output_name=None):
        """
        Create a weekly highlight horizontal video.
        Uses GPU-accelerated FFmpeg processing for maximum performance.
        
        Args:
            clip_files (list): List of clip file paths. If None, uses all clips.
            output_name (str): Output filename. If None, auto-generates.
            
        Returns:
            str: Path to generated video
        """
        return self.create_weekly_highlight_gpu(clip_files, output_name)


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
