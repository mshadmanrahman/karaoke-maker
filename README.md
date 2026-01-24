# 🎤 Karaoke Maker

Transform any YouTube video into a professional karaoke video with synchronized lyrics using AI.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-Web_UI-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## ✨ Features

- **🎵 YouTube Download** - Download audio from any YouTube video using pytubefix
- **🎚️ Vocal Separation** - AI-powered vocal/instrumental separation using Demucs
- **📝 Smart Lyrics** - Auto-extract timestamped lyrics using OpenAI Whisper
- **✏️ Lyrics Editor** - Manual timing with play/pause, inline editing, and keyboard shortcuts
- **🎬 Video Generation** - Create karaoke videos with highlighted, synchronized lyrics
- **🌐 Web Interface** - Beautiful, modern web UI with progress indicators

## 🖥️ Web Interface

The app features a sleek, modern web interface with:
- Step-by-step workflow (Download → Separate → Time → Generate)
- Real-time progress bars for long operations
- Inline lyrics editing with keyboard shortcuts
- Play/pause controls for precise timing

## 📋 Requirements

- Python 3.8+
- ffmpeg (for audio processing)
- macOS/Linux (tested on macOS with Apple Silicon)

## 🚀 Quick Start

### 1. Install ffmpeg

**macOS (Homebrew):**
```bash
# Install Homebrew if not installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install ffmpeg
brew install ffmpeg
```

**Ubuntu/Debian:**
```bash
sudo apt update && sudo apt install ffmpeg
```

### 2. Clone and Setup

```bash
git clone https://github.com/mshadmanrahman/karaoke-maker.git
cd karaoke-maker

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Run the Web App

```bash
source venv/bin/activate
python app.py
```

Open your browser to **http://localhost:5001**

## 📖 Usage

### Web Interface (Recommended)

1. **Download**: Paste a YouTube URL and press Enter or click Download
2. **Separate**: Click "Separate Vocals" (takes 2-3 minutes)
3. **Time Lyrics**: 
   - Click "Auto-Extract Lyrics" for AI-generated lyrics, OR
   - Manually time lyrics using keyboard shortcuts:
     - Press `S` to mark line start
     - Type the lyric text
     - Press `E` to mark line end
   - Edit any line by clicking the ✏️ button
4. **Generate**: Click "Generate Karaoke Video" (takes 3-5 minutes)

### Command Line

```bash
source venv/bin/activate
python karaoke_maker.py "https://youtube.com/watch?v=VIDEO_ID"

# With custom output name
python karaoke_maker.py "https://youtube.com/watch?v=VIDEO_ID" --output "My Song"
```

## ⌨️ Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `S` | Set start time for current lyric |
| `E` | Set end time and save lyric |
| `Space` | Play/Pause audio |
| `←` | Skip back 3 seconds |
| `→` | Skip forward 3 seconds |
| `Enter` | Submit URL / Save edits |
| `Escape` | Cancel editing |

## 🔧 Configuration

Edit `config.py` to customize:

### Video Settings
```python
VIDEO_WIDTH = 1920      # Video width
VIDEO_HEIGHT = 1080     # Video height
VIDEO_FPS = 30          # Frames per second
```

### Lyrics Appearance
```python
FONT_SIZE = 48          # Lyrics font size
FONT_COLOR = 'white'    # Default lyrics color
HIGHLIGHT_COLOR = 'yellow'  # Active line color
```

### AI Models
```python
DEMUCS_MODEL = 'htdemucs'  # Vocal separation model
WHISPER_MODEL = 'base'      # Speech recognition (tiny/base/small/medium/large)
```

## 📁 Project Structure

```
karaoke-maker/
├── app.py              # Flask web application
├── downloader.py       # YouTube audio download (pytubefix)
├── separator.py        # Vocal separation (Demucs)
├── lyrics_extractor.py # Lyrics extraction (Whisper)
├── video_generator.py  # Karaoke video creation
├── karaoke_maker.py    # CLI interface
├── config.py           # Configuration settings
├── requirements.txt    # Python dependencies
├── templates/
│   └── app.html        # Web UI template
└── README.md           # This file
```

## 🛠️ Technical Details

### Dependencies
- **pytubefix** - YouTube audio download (replaces yt-dlp for better compatibility)
- **Demucs** - AI vocal separation (Meta Research)
- **Whisper** - AI speech recognition (OpenAI)
- **MoviePy** - Video generation
- **Flask** - Web framework
- **PyTorch** - Machine learning framework

### Models (Downloaded on First Run)
- Demucs htdemucs: ~80MB
- Whisper base: ~140MB

## ❓ Troubleshooting

### "ffmpeg not found"
```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt install ffmpeg
```

### "Out of memory" error
- Use a smaller Whisper model in `config.py`: `WHISPER_MODEL = 'tiny'`
- Close other applications

### YouTube download fails
- The app uses pytubefix which handles most YouTube restrictions
- Ensure you have the latest version: `pip install --upgrade pytubefix`

### Slow processing
- CPU processing takes 8-12 minutes per song
- For faster processing with NVIDIA GPU: set `DEMUCS_DEVICE = 'cuda'` in config.py

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

**Note:** Respect copyright laws when downloading content from YouTube. This tool is intended for personal use with content you have rights to use.

## 🙏 Acknowledgments

- [Demucs](https://github.com/facebookresearch/demucs) by Meta Research
- [Whisper](https://github.com/openai/whisper) by OpenAI
- [pytubefix](https://github.com/JuanBindez/pytubefix) for YouTube downloads

---

Made with ❤️ for karaoke enthusiasts
