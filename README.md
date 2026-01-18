# Karaoke Maker

Transform any YouTube video into a karaoke video with synchronized lyrics.

## Features

- Downloads audio from YouTube videos
- Removes lead vocals using Demucs (high-quality separation)
- Extracts lyrics with timestamps using Whisper AI
- Generates karaoke video with highlighted lyrics
- Line-by-line highlighting for easy singing

## Requirements

- Python 3.8+
- ffmpeg
- macOS/Linux (tested on macOS)

## Installation

### 1. Install ffmpeg (if not already installed)

```bash
brew install ffmpeg
```

### 2. Run setup script

```bash
cd karaoke-maker
./setup.sh
```

This will:
- Create a Python virtual environment
- Install all required dependencies
- Set up configuration files

### 3. Configure output directory

Edit `.env` file to set where karaoke videos should be saved:

```bash
OUTPUT_DIR=/Users/yourname/Desktop/Karaoke
TEMP_DIR=/tmp/karaoke-temp
```

## Usage

### Basic usage

```bash
source venv/bin/activate
python karaoke_maker.py "https://youtube.com/watch?v=VIDEO_ID"
```

### With custom output name

```bash
python karaoke_maker.py "https://youtube.com/watch?v=VIDEO_ID" --output "My Favorite Song"
```

### Specify output directory

```bash
python karaoke_maker.py "https://youtube.com/watch?v=VIDEO_ID" --output-dir ~/Music/Karaoke
```

## How It Works

1. **Download Audio**: Uses yt-dlp to download audio from YouTube
2. **Vocal Separation**: Uses Demucs AI to separate vocals from instrumental (2-3 minutes)
3. **Lyrics Extraction**: Uses Whisper AI to transcribe and timestamp lyrics (1-2 minutes)
4. **Video Generation**: Creates video with synced, highlighted lyrics (3-5 minutes)

Total time: ~8-12 minutes per song

## Output

The tool creates:
- `[Song Title]_[timestamp]_karaoke.mp4`: Final karaoke video
- `[Song Title]_lyrics.json`: Timestamped lyrics (saved in temp directory)

## Configuration

Edit `config.py` to customize:

### Video Settings
- `VIDEO_WIDTH`: Video width (default: 1920)
- `VIDEO_HEIGHT`: Video height (default: 1080)
- `VIDEO_FPS`: Frames per second (default: 30)

### Lyrics Appearance
- `FONT_SIZE`: Lyrics font size (default: 48)
- `FONT_COLOR`: Default lyrics color (default: white)
- `HIGHLIGHT_COLOR`: Active line color (default: yellow)

### AI Models
- `DEMUCS_MODEL`: Vocal separation model (default: htdemucs)
- `WHISPER_MODEL`: Speech recognition model (default: base)
  - Options: tiny, base, small, medium, large
  - Larger models are more accurate but slower

### Performance
- `DEMUCS_DEVICE`: Set to 'cuda' if you have NVIDIA GPU (much faster)

## Troubleshooting

### "ffmpeg not found"
Install ffmpeg: `brew install ffmpeg`

### "Out of memory" error
- Use smaller Whisper model: edit `config.py` and set `WHISPER_MODEL = 'tiny'`
- Close other applications

### Slow processing
- Default CPU processing takes 8-12 minutes per song
- For faster processing, use a GPU: set `DEMUCS_DEVICE = 'cuda'` in config.py

### Lyrics not syncing properly
- Whisper auto-detects language but may struggle with heavy music
- Try processing the original audio multiple times
- Manual adjustment of JSON timestamps is possible

## Technical Details

### Dependencies
- **yt-dlp**: YouTube audio download
- **Demucs**: AI vocal separation (Meta/Facebook)
- **Whisper**: AI speech recognition (OpenAI)
- **MoviePy**: Video generation and editing
- **PyTorch**: Machine learning framework

### Models Downloaded (automatic on first run)
- Demucs htdemucs: ~350MB
- Whisper base: ~140MB

Total disk space needed: ~500MB for models + your output videos

## License

This is a personal hobby project. Respect copyright laws when downloading content from YouTube.

## Tips

1. **Best quality**: Use songs with clear vocals and minimal background noise
2. **Language support**: Whisper supports 90+ languages automatically
3. **Processing time**: Plan for 10 minutes per song
4. **Storage**: Each karaoke video is 50-150MB depending on length

## Future Enhancements

Potential improvements:
- Word-by-word highlighting (currently line-by-line)
- Custom background images/videos
- Multiple vocal track handling
- Batch processing
- GUI interface
