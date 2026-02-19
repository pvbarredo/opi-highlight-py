#!/usr/bin/env python3
"""
CUDA Video Converter - GPU-Accelerated Video Compression
Uses NVIDIA NVENC for fast, high-quality video compression with reduced file sizes

This script automatically detects videos in a folder, compresses them using GPU acceleration,
and saves them with "-converted" suffix.

Example: 25GB video → 8GB compressed video with same visual quality

Requirements:
- NVIDIA GPU with NVENC support
- FFmpeg with NVENC support

Author: Video Processing System
Date: February 19, 2026
"""

import os
import sys
import argparse
import subprocess
import re
from datetime import datetime
from pathlib import Path

try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False
    print("Note: Install 'tqdm' for progress bars: pip install tqdm")


class CUDAVideoConverter:
    """
    GPU-accelerated video converter using NVIDIA NVENC.
    Achieves 60-70% file size reduction while maintaining excellent quality.
    """
    
    # Supported video formats
    VIDEO_EXTENSIONS = ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.m4v', '.webm']
    
    # Quality presets
    PRESETS = {
        'high_quality': {
            'cq': 19,           # Constant Quality (lower=better)
            'preset': 'p7',     # Best quality preset (p1-p7)
            'audio_bitrate': '192k',
            'description': 'Near lossless quality, 40-55% size reduction'
        },
        'balanced': {
            'cq': 23,           # Excellent quality (recommended)
            'preset': 'p5',     # Good balance
            'audio_bitrate': '128k',
            'description': 'Excellent quality, 60-70% size reduction'
        },
        'maximum_compression': {
            'cq': 28,           # Good quality, smaller files
            'preset': 'p4',     # Faster encoding
            'audio_bitrate': '96k',
            'description': 'Good quality, 70-80% size reduction'
        }
    }
    
    def __init__(self, input_folder='video_files', output_folder='compressed_output', 
                 preset='balanced', custom_cq=None, suffix='converted'):
        """
        Initialize GPU video converter.
        
        Args:
            input_folder (str): Folder containing source videos
            output_folder (str): Folder for compressed output
            preset (str): Quality preset
            custom_cq (int): Manual CQ override (19-28 recommended)
            suffix (str): Suffix to add to converted files (default: 'converted')
        """
        self.input_folder = input_folder
        self.output_folder = output_folder
        self.preset = preset
        self.suffix = suffix
        
        # Get FFmpeg executable path (try bundled version first)
        self.ffmpeg_path = self._get_ffmpeg_path()
        
        # Get preset configuration
        if preset not in self.PRESETS:
            print(f"Warning: Unknown preset '{preset}', using 'balanced'")
            preset = 'balanced'
        
        self.config = self.PRESETS[preset].copy()
        
        # Allow manual CQ override
        if custom_cq is not None:
            self.config['cq'] = custom_cq
        
        # Create output folder if it doesn't exist
        os.makedirs(output_folder, exist_ok=True)
        
        # Statistics tracking
        self.stats = {
            'files_processed': 0,
            'files_failed': 0,
            'files_skipped': 0,
            'total_size_before': 0,
            'total_size_after': 0,
            'start_time': None,
            'end_time': None
        }
    
    def get_video_duration(self, video_path):
        """
        Get video duration in seconds using FFprobe or FFmpeg.
        
        Args:
            video_path (str): Path to video file
            
        Returns:
            float: Duration in seconds, or 0 if unable to determine
        """
        try:
            # Try ffprobe first (more accurate)
            ffprobe_path = self.ffmpeg_path.replace('ffmpeg', 'ffprobe')
            result = subprocess.run(
                [ffprobe_path, '-v', 'error', '-show_entries',
                 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', video_path],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0 and result.stdout.strip():
                return float(result.stdout.strip())
        except:
            pass
        
        # Fallback: use ffmpeg to get duration
        try:
            result = subprocess.run(
                [self.ffmpeg_path, '-i', video_path],
                capture_output=True,
                text=True,
                timeout=10
            )
            # Parse duration from stderr
            match = re.search(r'Duration: (\d{2}):(\d{2}):(\d{2}\.\d{2})', result.stderr)
            if match:
                hours, minutes, seconds = match.groups()
                return int(hours) * 3600 + int(minutes) * 60 + float(seconds)
        except:
            pass
        
        return 0
    
    def _get_ffmpeg_path(self):
        """
        Get FFmpeg executable path.
        Tries bundled MoviePy/imageio-ffmpeg first, then system PATH.
        
        Returns:
            str: Path to FFmpeg executable
        """
        # Try to get FFmpeg from MoviePy/imageio-ffmpeg (bundled version)
        try:
            import imageio_ffmpeg
            ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
            print(f"Using bundled FFmpeg from imageio-ffmpeg: {ffmpeg_path}")
            return ffmpeg_path
        except ImportError:
            pass
        
        # Try MoviePy config
        try:
            from moviepy.config import get_setting
            ffmpeg_path = get_setting("FFMPEG_BINARY")
            if ffmpeg_path and os.path.exists(ffmpeg_path):
                print(f"Using FFmpeg from MoviePy config: {ffmpeg_path}")
                return ffmpeg_path
        except:
            pass
        
        # Fall back to system FFmpeg
        print("Using system FFmpeg from PATH")
        return 'ffmpeg'
    
    def check_gpu_support(self):
        """Check if NVENC GPU encoding is available."""
        try:
            result = subprocess.run(
                [self.ffmpeg_path, '-hide_banner', '-encoders'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if 'h264_nvenc' in result.stdout:
                print("✓ GPU acceleration (NVENC) is available")
                return True
            else:
                print("✗ Warning: NVENC not found. GPU acceleration may not work.")
                print("  Make sure you have:")
                print("  1. NVIDIA GPU with NVENC support")
                print("  2. FFmpeg compiled with NVENC support")
                return False
                
        except FileNotFoundError:
            print("\n" + "="*70)
            print("ERROR: FFmpeg is not installed or not found")
            print("="*70)
            print("\nTo fix this, install FFmpeg-compatible packages:\n")
            print("Option 1 - Install imageio-ffmpeg (easiest):")
            print("  pip install imageio-ffmpeg\n")
            print("Option 2 - Using Chocolatey:")
            print("  choco install ffmpeg\n")
            print("Option 3 - Using winget:")
            print("  winget install ffmpeg\n")
            print("After installation, try again.")
            print("="*70 + "\n")
            sys.exit(1)
        except Exception as e:
            print(f"Warning: Could not check GPU support: {str(e)}")
            return False
    
    def get_video_files(self, pattern=None):
        """
        Get all video files from input folder.
        
        Args:
            pattern (str): Optional filename pattern to filter
            
        Returns:
            list: Video file paths
        """
        videos = []
        
        if not os.path.exists(self.input_folder):
            print(f"Error: Input folder '{self.input_folder}' not found")
            return videos
        
        for filename in os.listdir(self.input_folder):
            if any(filename.lower().endswith(ext) for ext in self.VIDEO_EXTENSIONS):
                # Skip already converted files
                if f'-{self.suffix}.' in filename.lower():
                    continue
                    
                if pattern is None or pattern.lower() in filename.lower():
                    videos.append(os.path.join(self.input_folder, filename))
        
        return sorted(videos)
    
    def get_file_size(self, filepath):
        """Get file size in bytes, GB, and MB."""
        size_bytes = os.path.getsize(filepath)
        size_mb = size_bytes / (1024 * 1024)
        size_gb = size_bytes / (1024 * 1024 * 1024)
        return size_bytes, size_gb, size_mb
    
    def format_size(self, size_bytes):
        """Format file size for display."""
        size_gb = size_bytes / (1024 * 1024 * 1024)
        if size_gb >= 1:
            return f"{size_gb:.2f} GB"
        else:
            size_mb = size_bytes / (1024 * 1024)
            return f"{size_mb:.2f} MB"
    
    def compress_video(self, input_path, output_path=None, use_gpu=True):
        """
        Compress a single video file using GPU acceleration or CPU fallback.
        
        Args:
            input_path (str): Path to input video
            output_path (str): Path for output (optional, auto-generated if None)
            use_gpu (bool): Try GPU acceleration first
            
        Returns:
            tuple: (success: bool, input_size_bytes: int, output_size_bytes: int)
        """
        if output_path is None:
            # Generate output filename with suffix
            filename = os.path.basename(input_path)
            name, ext = os.path.splitext(filename)
            
            # Use MP4 for output (best compatibility)
            output_path = os.path.join(self.output_folder, f"{name}-{self.suffix}.mp4")
        
        # Check if output already exists
        if os.path.exists(output_path):
            print(f"  ⊗ Output file already exists, skipping: {os.path.basename(output_path)}")
            self.stats['files_skipped'] += 1
            return False, 0, 0
        
        # Try GPU first, then CPU fallback
        if use_gpu:
            success, input_size, output_size = self._compress_gpu(input_path, output_path)
            if success:
                return True, input_size, output_size
            print(f"  → GPU encoding failed, falling back to CPU encoding...")
        
        # CPU fallback
        return self._compress_cpu(input_path, output_path)
    
    def _compress_gpu(self, input_path, output_path):
        """Try GPU-accelerated compression."""
    def _compress_gpu(self, input_path, output_path):
        """Try GPU-accelerated compression."""
        try:
            print(f"\nProcessing: {os.path.basename(input_path)}")
            print(f"  Mode: GPU acceleration (NVENC)")
            print(f"  Preset: {self.preset} (CQ {self.config['cq']}, {self.config['preset']})")
            
            # Get original file size
            input_size_bytes, input_size_gb, input_size_mb = self.get_file_size(input_path)
            print(f"  Original size: {self.format_size(input_size_bytes)}")
            
            # Map preset to NVENC preset (p1-p7)
            nvenc_preset_map = {
                'p7': 'p7',  # Slowest, best quality
                'p5': 'p5',  # Balanced
                'p4': 'p4'   # Faster, good quality
            }
            nvenc_preset = nvenc_preset_map.get(self.config['preset'], 'p4')
            
            # Build FFmpeg command for GPU encoding (NVENC only, no CUDA decode)
            ffmpeg_cmd = [
                self.ffmpeg_path,
                '-y',                                    # Overwrite output
                '-i', input_path,                        # Input file
                '-c:v', 'h264_nvenc',                    # NVENC H.264 encoder
                '-preset', nvenc_preset,                 # Quality preset (p1-p7)
                '-rc', 'vbr',                            # Variable bitrate
                '-cq', str(self.config['cq']),           # Constant Quality mode
                '-b:v', '0',                             # Bitrate (0 = auto with CQ)
                '-bufsize', '10M',                       # Buffer size
                '-maxrate', '100M',                      # Max bitrate
                '-bf', '3',                              # B-frames
                '-g', '250',                             # GOP size
                '-profile:v', 'high',                    # H.264 high profile
                '-pix_fmt', 'yuv420p',                   # Universal pixel format
                '-c:a', 'aac',                           # AAC audio codec
                '-b:a', self.config['audio_bitrate'],    # Audio bitrate
                '-movflags', '+faststart',               # Enable fast start for web
                output_path
            ]
            
            print(f"  Compressing with GPU (NVENC)...")
            print(f"  Output: {os.path.basename(output_path)}")
            
            # Get video duration for progress bar
            duration = self.get_video_duration(input_path)
            
            # Run FFmpeg with progress monitoring
            try:
                success = self._run_ffmpeg_with_progress(ffmpeg_cmd, duration)
                if not success:
                    return False, 0, 0
            except FileNotFoundError:
                return False, 0, 0
            
            # Get compressed file size
            output_size_bytes, output_size_gb, output_size_mb = self.get_file_size(output_path)
            reduction = ((input_size_bytes - output_size_bytes) / input_size_bytes) * 100
            
            print(f"  Compressed size: {self.format_size(output_size_bytes)}")
            print(f"  Size reduction: {reduction:.1f}%")
            print(f"  ✓ Successfully compressed using GPU")
            
            return True, input_size_bytes, output_size_bytes
            
        except Exception as e:
            return False, 0, 0
    
    def _compress_cpu(self, input_path, output_path):
        """CPU-based compression fallback using high-quality settings."""
        try:
            print(f"  Mode: CPU (High-Quality H.264)")
            
            # Get original file size
            input_size_bytes, input_size_gb, input_size_mb = self.get_file_size(input_path)
            if input_size_bytes == 0:  # Not printed yet
                print(f"\nProcessing: {os.path.basename(input_path)}")
                print(f"  Original size: {self.format_size(input_size_bytes)}")
            
            # Map CQ to CRF (similar quality levels)
            crf_value = self.config['cq'] - 4  # NVENC CQ 23 ≈ x264 CRF 19
            
            # Build FFmpeg command for CPU encoding (high quality)
            ffmpeg_cmd = [
                self.ffmpeg_path,
                '-y',                                    # Overwrite output
                '-i', input_path,                        # Input file
                '-c:v', 'libx264',                       # H.264 video codec
                '-crf', str(crf_value),                  # Constant Rate Factor
                '-preset', 'slow',                       # Slow preset for best compression
                '-profile:v', 'high',                    # H.264 high profile
                '-pix_fmt', 'yuv420p',                   # Universal pixel format
                '-c:a', 'aac',                           # AAC audio codec
                '-b:a', self.config['audio_bitrate'],    # Audio bitrate
                '-movflags', '+faststart',               # Enable fast start for web
                output_path
            ]
            
            print(f"  Compressing with CPU (CRF {crf_value}, slow preset)...")
            print(f"  Output: {os.path.basename(output_path)}")
            print(f"  Note: This will be slower than GPU but produces excellent quality")
            
            # Get video duration for progress bar
            duration = self.get_video_duration(input_path)
            
            # Run FFmpeg with progress monitoring
            try:
                success = self._run_ffmpeg_with_progress(ffmpeg_cmd, duration)
                if not success:
                    print(f"  ✗ FFmpeg encoding failed")
                    return False, 0, 0
            except FileNotFoundError:
                print(f"  ✗ Error: FFmpeg not found")
                return False, 0, 0
            
            # Get compressed file size
            output_size_bytes, output_size_gb, output_size_mb = self.get_file_size(output_path)
            reduction = ((input_size_bytes - output_size_bytes) / input_size_bytes) * 100
            
            print(f"  Compressed size: {self.format_size(output_size_bytes)}")
            print(f"  Size reduction: {reduction:.1f}%")
            print(f"  ✓ Successfully compressed using CPU")
            
            return True, input_size_bytes, output_size_bytes
            
        except subprocess.TimeoutExpired:
            print(f"  ✗ Error: Processing timeout")
            return False, 0, 0
        except Exception as e:
            print(f"  ✗ Error processing video: {str(e)}")
            return False, 0, 0
    
    def _run_ffmpeg_with_progress(self, ffmpeg_cmd, duration):
        """
        Run FFmpeg command with progress bar.
        
        Args:
            ffmpeg_cmd (list): FFmpeg command as list
            duration (float): Video duration in seconds
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Start FFmpeg process
            process = subprocess.Popen(
                ffmpeg_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            # Setup progress bar
            pbar = None
            if TQDM_AVAILABLE and duration > 0:
                pbar = tqdm(total=duration, unit='s', desc="  Progress", 
                           bar_format='{desc}: {percentage:3.0f}%|{bar}| {n:.1f}/{total:.1f}s [{elapsed}<{remaining}, {rate_fmt}]')
            
            # Monitor progress
            last_time = 0
            for line in process.stderr:
                # Parse FFmpeg progress output
                # Example: time=00:01:23.45
                time_match = re.search(r'time=(\d{2}):(\d{2}):(\d{2}\.\d{2})', line)
                if time_match and pbar:
                    hours, minutes, seconds = time_match.groups()
                    current_time = int(hours) * 3600 + int(minutes) * 60 + float(seconds)
                    
                    # Update progress bar
                    if current_time > last_time:
                        pbar.update(current_time - last_time)
                        last_time = current_time
            
            # Close progress bar
            if pbar:
                pbar.close()
            
            # Wait for process to complete
            process.wait()
            
            return process.returncode == 0
            
        except Exception as e:
            if pbar:
                pbar.close()
            return False
    
    def compress_folder(self, pattern=None):
        """
        Compress all videos in the input folder.
        
        Args:
            pattern (str): Optional filename pattern to filter
        """
        # Check GPU support first
        print("Checking GPU support...")
        self.check_gpu_support()
        print()
        
        video_files = self.get_video_files(pattern)
        
        if not video_files:
            print(f"No video files found in '{self.input_folder}'")
            if pattern:
                print(f"Pattern filter: '{pattern}'")
            return
        
        print(f"\n{'='*70}")
        print(f"VIDEO COMPRESSION - {self.preset.upper()} PRESET")
        print(f"{'='*70}")
        print(f"Preset: {self.PRESETS[self.preset]['description']}")
        print(f"Encoding: GPU (NVENC) with CPU fallback")
        print(f"Input folder: {self.input_folder}")
        print(f"Output folder: {self.output_folder}")
        print(f"Found {len(video_files)} video(s) to process")
        print(f"Output naming: original-{self.suffix}.mp4")
        print(f"{'='*70}")
        
        self.stats['start_time'] = datetime.now()
        
        for i, video_path in enumerate(video_files, 1):
            print(f"\n[{i}/{len(video_files)}] Processing video...")
            
            success, input_size, output_size = self.compress_video(video_path)
            
            if success:
                self.stats['files_processed'] += 1
                self.stats['total_size_before'] += input_size
                self.stats['total_size_after'] += output_size
            elif input_size == 0 and output_size == 0:
                # File was skipped (already exists)
                pass
            else:
                self.stats['files_failed'] += 1
        
        self.stats['end_time'] = datetime.now()
        self.print_summary()
    
    def compress_single_file(self, file_path, output_path=None):
        """
        Compress a single video file.
        
        Args:
            file_path (str): Path to video file
            output_path (str): Optional custom output path
        """
        if not os.path.exists(file_path):
            print(f"Error: File '{file_path}' not found")
            return
        
        # Check GPU support first
        print("Checking GPU support...")
        self.check_gpu_support()
        print()
        
        print(f"\n{'='*70}")
        print(f"VIDEO COMPRESSION - {self.preset.upper()} PRESET")
        print(f"{'='*70}")
        print(f"Preset: {self.PRESETS[self.preset]['description']}")
        print(f"Encoding: GPU (NVENC) with CPU fallback")
        print(f"Output folder: {self.output_folder}")
        print(f"{'='*70}")
        
        self.stats['start_time'] = datetime.now()
        
        success, input_size, output_size = self.compress_video(file_path, output_path)
        
        if success:
            self.stats['files_processed'] = 1
            self.stats['total_size_before'] = input_size
            self.stats['total_size_after'] = output_size
        else:
            self.stats['files_failed'] = 1
        
        self.stats['end_time'] = datetime.now()
        self.print_summary()
    
    def print_summary(self):
        """Print compression summary statistics."""
        print(f"\n{'='*70}")
        print("COMPRESSION SUMMARY")
        print(f"{'='*70}")
        print(f"Files processed: {self.stats['files_processed']}")
        print(f"Files failed: {self.stats['files_failed']}")
        print(f"Files skipped: {self.stats['files_skipped']}")
        
        if self.stats['files_processed'] > 0:
            print(f"\nTotal size before: {self.format_size(self.stats['total_size_before'])}")
            print(f"Total size after: {self.format_size(self.stats['total_size_after'])}")
            
            total_saved = self.stats['total_size_before'] - self.stats['total_size_after']
            total_reduction = (total_saved / self.stats['total_size_before']) * 100
            
            print(f"Total saved: {self.format_size(total_saved)} ({total_reduction:.1f}% reduction)")
        
        if self.stats['start_time'] and self.stats['end_time']:
            duration = self.stats['end_time'] - self.stats['start_time']
            print(f"\nTime elapsed: {duration}")
        
        print(f"{'='*70}\n")


def main():
    """Main entry point for command-line usage."""
    parser = argparse.ArgumentParser(
        description='GPU-accelerated video compression using NVIDIA NVENC',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Compress all videos in video_files folder
  python cuda_video_converter.py
  
  # Compress with maximum compression
  python cuda_video_converter.py --preset maximum_compression
  
  # Compress specific folder
  python cuda_video_converter.py --folder "C:/Videos" --output "C:/Compressed"
  
  # Compress single file
  python cuda_video_converter.py --input "myvideo.mp4"
  
  # Filter by pattern
  python cuda_video_converter.py --pattern "cam1"
  
  # Custom quality setting
  python cuda_video_converter.py --cq 25
        """
    )
    
    parser.add_argument(
        '--input',
        type=str,
        help='Input video file path (for single file conversion)'
    )
    
    parser.add_argument(
        '--folder',
        type=str,
        default='video_files',
        help='Input folder containing videos (default: video_files)'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        default='compressed_output',
        help='Output folder for compressed videos (default: compressed_output)'
    )
    
    parser.add_argument(
        '--preset',
        type=str,
        choices=['high_quality', 'balanced', 'maximum_compression'],
        default='balanced',
        help='Compression preset (default: balanced)'
    )
    
    parser.add_argument(
        '--cq',
        type=int,
        help='Manual CQ (Constant Quality) override (19-28 recommended, lower=better quality)'
    )
    
    parser.add_argument(
        '--pattern',
        type=str,
        help='Filter files by pattern (e.g., "cam1" for Cam1 videos only)'
    )
    
    parser.add_argument(
        '--suffix',
        type=str,
        default='converted',
        help='Suffix to add to converted files (default: converted)'
    )
    
    args = parser.parse_args()
    
    # Create converter instance
    converter = CUDAVideoConverter(
        input_folder=args.folder,
        output_folder=args.output,
        preset=args.preset,
        custom_cq=args.cq,
        suffix=args.suffix
    )
    
    # Process single file or entire folder
    if args.input:
        converter.compress_single_file(args.input)
    else:
        converter.compress_folder(pattern=args.pattern)


if __name__ == '__main__':
    main()
