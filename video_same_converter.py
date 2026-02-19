"""
Video Same Converter
Converts a video to match the exact codec, resolution, and framerate of a source video.
This ensures both videos are compatible for FFmpeg concatenation.
"""

import os
import sys
import subprocess
import json
import re
import argparse
from pathlib import Path


def get_ffmpeg_path():
    """Get FFmpeg path from imageio-ffmpeg or system."""
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        return 'ffmpeg'


def get_video_specs(video_path):
    """Extract codec, resolution, and framerate from a video file.
    
    Args:
        video_path: Path to the video file
        
    Returns:
        dict with keys: codec, width, height, fps, pixel_format, audio_codec, audio_sample_rate
    """
    ffmpeg = get_ffmpeg_path()
    
    # Use ffmpeg -i to get stream info (output is in stderr)
    cmd = [
        ffmpeg,
        '-i', video_path,
        '-f', 'null',
        '-'
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        output = result.stderr  # FFmpeg puts stream info in stderr
        
        specs = {}
        
        # Parse video stream info from ffmpeg output
        # Look for lines like: "Stream #0:0: Video: h264 (High), yuv420p, 1920x1080, 30 fps"
        for line in output.split('\n'):
            if 'Video:' in line and 'Stream' in line:
                # Extract codec
                if 'h264' in line.lower():
                    specs['codec'] = 'h264'
                elif 'hevc' in line.lower() or 'h265' in line.lower():
                    specs['codec'] = 'hevc'
                elif 'vp9' in line.lower():
                    specs['codec'] = 'vp9'
                elif 'vp8' in line.lower():
                    specs['codec'] = 'vp8'
                else:
                    # Try to extract codec name
                    codec_match = re.search(r'Video:\s+(\w+)', line)
                    if codec_match:
                        specs['codec'] = codec_match.group(1)
                    else:
                        specs['codec'] = 'h264'  # Default
                
                # Extract resolution
                res_match = re.search(r'(\d{3,4})x(\d{3,4})', line)
                if res_match:
                    specs['width'] = int(res_match.group(1))
                    specs['height'] = int(res_match.group(2))
                else:
                    specs['width'] = 1920
                    specs['height'] = 1080
                
                # Extract pixel format
                pix_match = re.search(r'yuv\d+p\d*', line)
                if pix_match:
                    specs['pixel_format'] = pix_match.group(0)
                else:
                    specs['pixel_format'] = 'yuv420p'
                
                # Extract FPS
                fps_match = re.search(r'(\d+\.?\d*)\s*fps', line)
                if fps_match:
                    specs['fps'] = float(fps_match.group(1))
                else:
                    # Try alternative format
                    fps_match = re.search(r'(\d+\.?\d*)\s*tbr', line)
                    if fps_match:
                        specs['fps'] = float(fps_match.group(1))
                    else:
                        specs['fps'] = 30.0
            
            elif 'Audio:' in line and 'Stream' in line:
                # Extract audio codec
                if 'aac' in line.lower():
                    specs['audio_codec'] = 'aac'
                elif 'mp3' in line.lower():
                    specs['audio_codec'] = 'mp3'
                elif 'ac3' in line.lower():
                    specs['audio_codec'] = 'ac3'
                else:
                    # Try to extract audio codec name
                    audio_match = re.search(r'Audio:\s+(\w+)', line)
                    if audio_match:
                        specs['audio_codec'] = audio_match.group(1)
                
                # Extract sample rate
                sr_match = re.search(r'(\d+)\s*Hz', line)
                if sr_match:
                    specs['audio_sample_rate'] = sr_match.group(1)
                else:
                    specs['audio_sample_rate'] = '48000'
                
                # Extract channels
                if 'stereo' in line.lower():
                    specs['audio_channels'] = 2
                elif 'mono' in line.lower():
                    specs['audio_channels'] = 1
                elif '5.1' in line:
                    specs['audio_channels'] = 6
                else:
                    specs['audio_channels'] = 2
        
        if not specs:
            print(f"✗ Could not parse video specifications")
            return None
            
        return specs
        
    except Exception as e:
        print(f"✗ Error reading video specs: {e}")
        return None


def convert_video_to_match(source_path, target_path, output_path, use_gpu=True):
    """Convert target video to match source video specifications.
    
    Args:
        source_path: Path to source video (reference)
        target_path: Path to video to convert
        output_path: Path for output video
        use_gpu: Whether to attempt GPU encoding
    """
    ffmpeg = get_ffmpeg_path()
    
    print(f"{'='*60}")
    print(f"Video Same Converter")
    print(f"{'='*60}")
    
    # Get source video specs
    print(f"\n📹 Analyzing source video...")
    print(f"   {source_path}")
    source_specs = get_video_specs(source_path)
    
    if not source_specs:
        print(f"✗ Failed to read source video specifications")
        return False
    
    print(f"\n✓ Source video specs:")
    print(f"   Codec: {source_specs.get('codec', 'N/A')}")
    print(f"   Resolution: {source_specs.get('width', 'N/A')}x{source_specs.get('height', 'N/A')}")
    print(f"   Framerate: {source_specs.get('fps', 'N/A'):.2f} fps")
    print(f"   Pixel Format: {source_specs.get('pixel_format', 'N/A')}")
    if 'audio_codec' in source_specs:
        print(f"   Audio Codec: {source_specs.get('audio_codec', 'N/A')}")
        print(f"   Audio Sample Rate: {source_specs.get('audio_sample_rate', 'N/A')} Hz")
        print(f"   Audio Channels: {source_specs.get('audio_channels', 'N/A')}")
    
    # Get target video specs for comparison
    print(f"\n📹 Analyzing target video...")
    print(f"   {target_path}")
    target_specs = get_video_specs(target_path)
    
    if not target_specs:
        print(f"✗ Failed to read target video specifications")
        return False
    
    print(f"\n✓ Target video specs:")
    print(f"   Codec: {target_specs.get('codec', 'N/A')}")
    print(f"   Resolution: {target_specs.get('width', 'N/A')}x{target_specs.get('height', 'N/A')}")
    print(f"   Framerate: {target_specs.get('fps', 'N/A'):.2f} fps")
    print(f"   Pixel Format: {target_specs.get('pixel_format', 'N/A')}")
    
    # Check if conversion is needed
    needs_conversion = (
        source_specs.get('codec') != target_specs.get('codec') or
        source_specs.get('width') != target_specs.get('width') or
        source_specs.get('height') != target_specs.get('height') or
        abs(source_specs.get('fps', 0) - target_specs.get('fps', 0)) > 0.1 or
        source_specs.get('pixel_format') != target_specs.get('pixel_format')
    )
    
    if not needs_conversion:
        print(f"\n✓ Videos already have matching specifications!")
        print(f"  No conversion needed.")
        return True
    
    # Build FFmpeg command
    print(f"\n🔄 Converting target video to match source specs...")
    
    cmd = [ffmpeg, '-i', target_path]
    
    # Check if GPU encoding is available for the target codec
    gpu_encoder_map = {
        'h264': 'h264_nvenc',
        'hevc': 'hevc_nvenc',
        'h265': 'hevc_nvenc'
    }
    
    source_codec = source_specs.get('codec', 'h264')
    gpu_encoder = gpu_encoder_map.get(source_codec)
    
    # Try GPU encoding if requested and available
    if use_gpu and gpu_encoder:
        # Check if GPU encoder is available
        check_cmd = [ffmpeg, '-hide_banner', '-encoders']
        try:
            result = subprocess.run(check_cmd, capture_output=True, text=True)
            if gpu_encoder in result.stdout:
                print(f"   Using GPU encoder: {gpu_encoder}")
                cmd.extend(['-c:v', gpu_encoder])
                cmd.extend(['-preset', 'p4'])
                cmd.extend(['-rc', 'vbr'])
                cmd.extend(['-cq', '19'])  # High quality
                cmd.extend(['-b:v', '0'])
            else:
                print(f"   GPU encoder not available, using CPU")
                use_gpu = False
        except:
            print(f"   Error checking GPU support, using CPU")
            use_gpu = False
    
    # CPU encoding fallback
    if not use_gpu:
        cpu_encoder_map = {
            'h264': 'libx264',
            'hevc': 'libx265',
            'h265': 'libx265',
            'vp9': 'libvpx-vp9',
            'vp8': 'libvpx'
        }
        cpu_encoder = cpu_encoder_map.get(source_codec, 'libx264')
        print(f"   Using CPU encoder: {cpu_encoder}")
        cmd.extend(['-c:v', cpu_encoder])
        cmd.extend(['-crf', '18'])  # High quality
        cmd.extend(['-preset', 'medium'])
    
    # Set resolution
    width = source_specs.get('width', 1920)
    height = source_specs.get('height', 1080)
    cmd.extend(['-s', f'{width}x{height}'])
    
    # Set framerate
    fps = source_specs.get('fps', 30.0)
    cmd.extend(['-r', str(fps)])
    
    # Set pixel format
    pix_fmt = source_specs.get('pixel_format', 'yuv420p')
    cmd.extend(['-pix_fmt', pix_fmt])
    
    # Audio encoding
    if 'audio_codec' in source_specs:
        audio_codec = source_specs.get('audio_codec', 'aac')
        if audio_codec == 'aac':
            cmd.extend(['-c:a', 'aac'])
        elif audio_codec == 'mp3':
            cmd.extend(['-c:a', 'libmp3lame'])
        else:
            cmd.extend(['-c:a', 'aac'])  # Default to AAC
        
        # Set audio sample rate
        sample_rate = source_specs.get('audio_sample_rate', '48000')
        cmd.extend(['-ar', str(sample_rate)])
        
        # Set audio channels
        channels = source_specs.get('audio_channels', 2)
        cmd.extend(['-ac', str(channels)])
        
        cmd.extend(['-b:a', '192k'])
    else:
        cmd.extend(['-an'])  # No audio
    
    # Output file
    cmd.extend(['-y', output_path])
    
    print(f"\n{'─'*60}")
    print(f"Conversion command:")
    print(f"  {' '.join(cmd)}")
    print(f"{'─'*60}\n")
    
    # Execute conversion
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        )
        
        # Show FFmpeg output
        for line in process.stdout:
            line = line.strip()
            if line:
                # Show important lines
                if any(keyword in line.lower() for keyword in ['error', 'warning', 'frame=', 'time=']):
                    print(f"  {line}")
        
        process.wait()
        
        if process.returncode == 0:
            output_size = os.path.getsize(output_path) / (1024 * 1024)
            print(f"\n{'='*60}")
            print(f"✓ Conversion successful!")
            print(f"{'='*60}")
            print(f"Output: {output_path}")
            print(f"Size: {output_size:.2f} MB")
            print(f"\nVideos are now compatible for concatenation using:")
            print(f"  ffmpeg -f concat -safe 0 -i filelist.txt -c copy output.mp4")
            return True
        else:
            print(f"\n✗ Conversion failed with return code {process.returncode}")
            return False
            
    except Exception as e:
        print(f"\n✗ Error during conversion: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description='Convert a video to match the codec, resolution, and framerate of a source video.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert target.mp4 to match source.mp4
  python video_same_converter.py source.mp4 target.mp4 output.mp4
  
  # Use CPU encoding
  python video_same_converter.py source.mp4 target.mp4 output.mp4 --no-gpu
  
  # After conversion, concatenate with:
  echo file 'video1.mp4' > filelist.txt
  echo file 'video2.mp4' >> filelist.txt
  ffmpeg -f concat -safe 0 -i filelist.txt -c copy output.mp4
        """
    )
    
    parser.add_argument('source', help='Source video (reference for specs)')
    parser.add_argument('target', help='Video to convert')
    parser.add_argument('output', help='Output video path')
    parser.add_argument('--no-gpu', action='store_true', help='Disable GPU encoding')
    
    args = parser.parse_args()
    
    # Validate input files
    if not os.path.exists(args.source):
        print(f"✗ Source video not found: {args.source}")
        return 1
    
    if not os.path.exists(args.target):
        print(f"✗ Target video not found: {args.target}")
        return 1
    
    # Ensure output directory exists
    output_dir = os.path.dirname(args.output)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Convert video
    success = convert_video_to_match(
        args.source,
        args.target,
        args.output,
        use_gpu=not args.no_gpu
    )
    
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
