#!/usr/bin/env python3
"""
Video Converter - Compress videos to smallest size while maintaining quality
Uses H.264 codec with CRF (Constant Rate Factor) for optimal compression

Author: Video Processing System
Date: February 15, 2026
"""

import os
import sys
import argparse
from datetime import datetime
from pathlib import Path

try:
    from moviepy.editor import VideoFileClip
except ImportError:
    from moviepy import VideoFileClip


class VideoConverter:
    """
    Convert and compress video files using optimal quality/size settings.
    Uses H.264 codec with CRF 23 for near-lossless compression.
    """
    
    # Compression presets for different use cases
    PRESETS = {
        'high_quality': {
            'crf': 18,          # Near lossless
            'preset': 'slow',   # Best compression
            'audio_bitrate': '192k',
            'description': 'Near lossless quality, 30-50% size reduction'
        },
        'balanced': {
            'crf': 23,          # Excellent quality (default)
            'preset': 'medium', # Good speed
            'audio_bitrate': '128k',
            'description': 'Excellent quality, 50-70% size reduction'
        },
        'small_file': {
            'crf': 28,          # Good quality
            'preset': 'slow',   # Maximum compression
            'audio_bitrate': '96k',
            'description': 'Good quality, 70-85% size reduction'
        }
    }
    
    def __init__(self, input_folder='video_files', output_folder='compressed_output', 
                 preset='balanced', custom_crf=None):
        """
        Initialize video converter.
        
        Args:
            input_folder (str): Folder containing source videos
            output_folder (str): Folder for compressed output
            preset (str): Compression preset ('high_quality', 'balanced', 'small_file')
            custom_crf (int): Manual CRF override (18-28 recommended)
        """
        self.input_folder = input_folder
        self.output_folder = output_folder
        self.preset = preset
        
        # Get preset configuration
        if preset not in self.PRESETS:
            print(f"Warning: Unknown preset '{preset}', using 'balanced'")
            preset = 'balanced'
        
        self.config = self.PRESETS[preset].copy()
        
        # Allow manual CRF override
        if custom_crf is not None:
            self.config['crf'] = custom_crf
        
        # Create output folder if it doesn't exist
        os.makedirs(output_folder, exist_ok=True)
        
        # Statistics tracking
        self.stats = {
            'files_processed': 0,
            'files_failed': 0,
            'total_size_before': 0,
            'total_size_after': 0,
            'start_time': None,
            'end_time': None
        }
    
    def get_video_files(self, pattern=None):
        """
        Get all video files from input folder.
        
        Args:
            pattern (str): Optional filename pattern to filter
            
        Returns:
            list: Video file paths
        """
        video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv']
        videos = []
        
        if not os.path.exists(self.input_folder):
            print(f"Error: Input folder '{self.input_folder}' not found")
            return videos
        
        for filename in os.listdir(self.input_folder):
            if any(filename.lower().endswith(ext) for ext in video_extensions):
                if pattern is None or pattern.lower() in filename.lower():
                    videos.append(os.path.join(self.input_folder, filename))
        
        return sorted(videos)
    
    def get_file_size_mb(self, filepath):
        """Get file size in MB."""
        return os.path.getsize(filepath) / (1024 * 1024)
    
    def compress_video(self, input_path, output_path=None):
        """
        Compress a single video file.
        
        Args:
            input_path (str): Path to input video
            output_path (str): Path for output (optional, auto-generated if None)
            
        Returns:
            tuple: (success: bool, input_size_mb: float, output_size_mb: float)
        """
        if output_path is None:
            # Generate output filename
            filename = os.path.basename(input_path)
            name, ext = os.path.splitext(filename)
            output_path = os.path.join(self.output_folder, f"{name}_compressed.mp4")
        
        try:
            print(f"\nProcessing: {os.path.basename(input_path)}")
            print(f"  Preset: {self.preset} (CRF {self.config['crf']}, {self.config['preset']})")
            
            # Get original file size
            input_size = self.get_file_size_mb(input_path)
            print(f"  Original size: {input_size:.2f} MB")
            
            # Load video
            video = VideoFileClip(input_path)
            
            # Build FFmpeg parameters for optimal compression
            ffmpeg_params = [
                '-c:v', 'libx264',                      # H.264 video codec
                '-crf', str(self.config['crf']),        # Constant Rate Factor
                '-preset', self.config['preset'],       # Encoding preset
                '-profile:v', 'high',                   # H.264 high profile
                '-pix_fmt', 'yuv420p',                  # Universal pixel format
                '-c:a', 'aac',                          # AAC audio codec
                '-b:a', self.config['audio_bitrate'],   # Audio bitrate
                '-movflags', '+faststart'               # Web optimization
            ]
            
            # Write compressed video
            print(f"  Compressing... (this may take a while)")
            
            try:
                video.write_videofile(
                    output_path,
                    codec='libx264',
                    audio_codec='aac',
                    ffmpeg_params=ffmpeg_params,
                    logger=None  # Suppress verbose output
                )
            except TypeError:
                # Fallback for older MoviePy versions
                video.write_videofile(
                    output_path,
                    codec='libx264',
                    audio_codec='aac'
                )
            
            video.close()
            
            # Get compressed file size
            output_size = self.get_file_size_mb(output_path)
            reduction = ((input_size - output_size) / input_size) * 100
            
            print(f"  Compressed size: {output_size:.2f} MB")
            print(f"  Size reduction: {reduction:.1f}%")
            print(f"  ✓ Saved to: {output_path}")
            
            return True, input_size, output_size
            
        except Exception as e:
            print(f"  ✗ Error processing video: {str(e)}")
            return False, 0, 0
    
    def compress_folder(self, pattern=None):
        """
        Compress all videos in the input folder.
        
        Args:
            pattern (str): Optional filename pattern to filter
        """
        video_files = self.get_video_files(pattern)
        
        if not video_files:
            print(f"No video files found in '{self.input_folder}'")
            return
        
        print(f"\n{'='*70}")
        print(f"VIDEO COMPRESSION - {self.preset.upper()} PRESET")
        print(f"{'='*70}")
        print(f"Preset: {self.PRESETS[self.preset]['description']}")
        print(f"Input folder: {self.input_folder}")
        print(f"Output folder: {self.output_folder}")
        print(f"Found {len(video_files)} video(s) to process")
        print(f"{'='*70}")
        
        self.stats['start_time'] = datetime.now()
        
        for i, video_path in enumerate(video_files, 1):
            print(f"\n[{i}/{len(video_files)}] Processing video...")
            
            success, input_size, output_size = self.compress_video(video_path)
            
            if success:
                self.stats['files_processed'] += 1
                self.stats['total_size_before'] += input_size
                self.stats['total_size_after'] += output_size
            else:
                self.stats['files_failed'] += 1
        
        self.stats['end_time'] = datetime.now()
        self.print_summary()
    
    def compress_single_file(self, file_path):
        """
        Compress a single video file.
        
        Args:
            file_path (str): Path to video file
        """
        if not os.path.exists(file_path):
            print(f"Error: File '{file_path}' not found")
            return
        
        print(f"\n{'='*70}")
        print(f"VIDEO COMPRESSION - {self.preset.upper()} PRESET")
        print(f"{'='*70}")
        print(f"Preset: {self.PRESETS[self.preset]['description']}")
        print(f"Output folder: {self.output_folder}")
        print(f"{'='*70}")
        
        self.stats['start_time'] = datetime.now()
        
        success, input_size, output_size = self.compress_video(file_path)
        
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
        
        if self.stats['files_processed'] > 0:
            print(f"\nTotal size before: {self.stats['total_size_before']:.2f} MB")
            print(f"Total size after: {self.stats['total_size_after']:.2f} MB")
            
            total_saved = self.stats['total_size_before'] - self.stats['total_size_after']
            total_reduction = (total_saved / self.stats['total_size_before']) * 100
            
            print(f"Total saved: {total_saved:.2f} MB ({total_reduction:.1f}% reduction)")
        
        if self.stats['start_time'] and self.stats['end_time']:
            duration = self.stats['end_time'] - self.stats['start_time']
            print(f"\nTime elapsed: {duration}")
        
        print(f"{'='*70}\n")


def main():
    """Main entry point for command-line usage."""
    parser = argparse.ArgumentParser(
        description='Compress videos to smallest size while maintaining quality'
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
        choices=['high_quality', 'balanced', 'small_file'],
        default='balanced',
        help='Compression preset (default: balanced)'
    )
    
    parser.add_argument(
        '--crf',
        type=int,
        help='Manual CRF override (18-28 recommended, lower=better quality)'
    )
    
    parser.add_argument(
        '--pattern',
        type=str,
        help='Filter files by pattern (e.g., "cam1" for Cam1 videos only)'
    )
    
    args = parser.parse_args()
    
    # Create converter instance
    converter = VideoConverter(
        input_folder=args.folder,
        output_folder=args.output,
        preset=args.preset,
        custom_crf=args.crf
    )
    
    # Process single file or entire folder
    if args.input:
        converter.compress_single_file(args.input)
    else:
        converter.compress_folder(pattern=args.pattern)


if __name__ == '__main__':
    main()
