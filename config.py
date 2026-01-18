"""
Configuration management for Karaoke Maker
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Directories
OUTPUT_DIR = Path(os.getenv('OUTPUT_DIR', str(Path.home() / 'Desktop' / 'Karaoke')))
TEMP_DIR = Path(os.getenv('TEMP_DIR', '/tmp/karaoke-temp'))

# Create directories if they don't exist
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
TEMP_DIR.mkdir(parents=True, exist_ok=True)

# Audio settings
AUDIO_FORMAT = 'mp3'
AUDIO_QUALITY = '320'  # kbps

# Video settings
VIDEO_WIDTH = 1920
VIDEO_HEIGHT = 1080
VIDEO_FPS = 30
VIDEO_CODEC = 'libx264'
VIDEO_BITRATE = '5000k'

# Lyrics settings
FONT_SIZE = 48
FONT_COLOR = 'white'
HIGHLIGHT_COLOR = 'yellow'
FONT_FAMILY = 'Arial-Bold'
TEXT_Y_POSITION = 0.8  # 80% from top (near bottom)
LINE_SPACING = 60

# Demucs settings
DEMUCS_MODEL = 'htdemucs'  # High-quality model
DEMUCS_DEVICE = 'cpu'  # Change to 'cuda' if you have GPU

# Whisper settings
WHISPER_MODEL = 'small'  # Options: tiny, base, small, medium, large (small+ recommended for Bengali/Hindi)
WHISPER_LANGUAGE = None  # Auto-detect, or specify like 'bn' (Bengali), 'hi' (Hindi), 'en' (English)
