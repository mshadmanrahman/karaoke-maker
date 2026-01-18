"""
Web-based lyrics timing editor for karaoke maker
Provides interactive UI for syncing lyrics with audio
"""
from flask import Flask, render_template, request, jsonify, send_file
from pathlib import Path
import json
import logging
from typing import Dict, List
from downloader import YouTubeDownloader
from separator import VocalSeparator
from lyrics_extractor import LyricsExtractor
from video_generator import KaraokeVideoGenerator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Directories
TEMP_DIR = Path('/tmp/karaoke-temp')
OUTPUT_DIR = Path.home() / 'Downloads'
TEMP_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Global state for current session
current_session = {
    'audio_path': None,
    'instrumental_path': None,
    'title': None,
    'lyrics': []
}


@app.route('/')
def index():
    """Main editor page"""
    return render_template('editor.html')


@app.route('/api/download', methods=['POST'])
def download_youtube():
    """Download audio from YouTube URL"""
    try:
        data = request.json
        youtube_url = data.get('url')

        if not youtube_url:
            return jsonify({'error': 'No URL provided'}), 400

        logger.info(f"Downloading: {youtube_url}")
        downloader = YouTubeDownloader(TEMP_DIR)
        result = downloader.download(youtube_url)

        current_session['audio_path'] = result['audio_path']
        current_session['title'] = result['title']

        return jsonify({
            'success': True,
            'title': result['title'],
            'audio_path': result['audio_path']
        })

    except Exception as e:
        logger.error(f"Download error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/separate', methods=['POST'])
def separate_vocals():
    """Separate vocals from audio"""
    try:
        if not current_session['audio_path']:
            return jsonify({'error': 'No audio loaded'}), 400

        logger.info("Separating vocals...")
        separator = VocalSeparator(TEMP_DIR)
        result = separator.separate(current_session['audio_path'])

        current_session['instrumental_path'] = result['instrumental']

        return jsonify({
            'success': True,
            'instrumental_path': result['instrumental']
        })

    except Exception as e:
        logger.error(f"Separation error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/extract-lyrics', methods=['POST'])
def extract_lyrics():
    """Extract lyrics using Whisper"""
    try:
        if not current_session['audio_path']:
            return jsonify({'error': 'No audio loaded'}), 400

        logger.info("Extracting lyrics...")
        extractor = LyricsExtractor()
        result = extractor.extract(current_session['audio_path'])

        # Convert to simpler format for frontend
        lyrics = []
        for segment in result['segments']:
            lyrics.append({
                'start': segment['start'],
                'end': segment['end'],
                'text': segment['text']
            })

        current_session['lyrics'] = lyrics

        return jsonify({
            'success': True,
            'lyrics': lyrics,
            'language': result.get('language', 'unknown')
        })

    except Exception as e:
        logger.error(f"Extraction error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/update-lyrics', methods=['POST'])
def update_lyrics():
    """Update lyrics timing and text"""
    try:
        data = request.json
        lyrics = data.get('lyrics', [])

        current_session['lyrics'] = lyrics

        return jsonify({'success': True})

    except Exception as e:
        logger.error(f"Update error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/generate', methods=['POST'])
def generate_video():
    """Generate final karaoke video"""
    try:
        if not current_session['instrumental_path']:
            return jsonify({'error': 'No instrumental track'}), 400

        if not current_session['lyrics']:
            return jsonify({'error': 'No lyrics'}), 400

        logger.info("Generating karaoke video...")

        # Convert lyrics to expected format
        lyrics_data = {
            'segments': [
                {
                    'start': lyric['start'],
                    'end': lyric['end'],
                    'text': lyric['text']
                }
                for lyric in current_session['lyrics']
            ]
        }

        generator = KaraokeVideoGenerator()
        output_path = generator.generate(
            audio_path=current_session['instrumental_path'],
            lyrics_data=lyrics_data,
            output_dir=OUTPUT_DIR,
            title=current_session['title']
        )

        return jsonify({
            'success': True,
            'output_path': str(output_path)
        })

    except Exception as e:
        logger.error(f"Generation error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/audio/<path:filename>')
def serve_audio(filename):
    """Serve audio file"""
    try:
        file_path = Path(filename)
        if file_path.exists():
            return send_file(str(file_path))
        return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        logger.error(f"Audio serve error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/session')
def get_session():
    """Get current session state"""
    return jsonify({
        'title': current_session['title'],
        'audio_path': current_session['audio_path'],
        'instrumental_path': current_session['instrumental_path'],
        'lyrics': current_session['lyrics']
    })


if __name__ == '__main__':
    print("\n" + "="*70)
    print("KARAOKE MAKER - WEB EDITOR")
    print("="*70)
    print("\nStarting web server...")
    print("Open your browser to: http://localhost:5001")
    print("\nPress Ctrl+C to stop the server")
    print("="*70 + "\n")

    app.run(debug=True, port=5001)
