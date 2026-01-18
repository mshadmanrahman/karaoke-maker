#!/usr/bin/env python3
"""
All-in-one Karaoke Maker Web App
Complete workflow: Download → Separate → Time Lyrics → Generate Video
"""
from flask import Flask, render_template, request, jsonify, send_file, send_from_directory
from pathlib import Path
import json
import logging
from datetime import datetime
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

# Session state
session = {
    'youtube_url': None,
    'audio_path': None,
    'instrumental_path': None,
    'title': None,
    'auto_lyrics': None,
    'final_lyrics': None,
    'video_path': None
}


@app.route('/')
def index():
    """Main page"""
    return render_template('app.html')


@app.route('/api/download', methods=['POST'])
def download():
    """Step 1: Download from YouTube"""
    try:
        data = request.json
        youtube_url = data.get('url')

        if not youtube_url:
            return jsonify({'error': 'No URL provided'}), 400

        logger.info(f"Downloading: {youtube_url}")
        downloader = YouTubeDownloader(TEMP_DIR)
        result = downloader.download(youtube_url)

        session['youtube_url'] = youtube_url
        session['audio_path'] = result['audio_path']
        session['title'] = result['title']

        return jsonify({
            'success': True,
            'title': result['title']
        })

    except Exception as e:
        logger.error(f"Download error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/separate', methods=['POST'])
def separate():
    """Step 2: Separate vocals"""
    try:
        if not session['audio_path']:
            return jsonify({'error': 'No audio loaded'}), 400

        logger.info("Separating vocals...")
        separator = VocalSeparator(TEMP_DIR)
        result = separator.separate(session['audio_path'])

        session['instrumental_path'] = result['instrumental']

        return jsonify({'success': True})

    except Exception as e:
        logger.error(f"Separation error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/extract-lyrics', methods=['POST'])
def extract_lyrics():
    """Step 3: Auto-extract lyrics (optional)"""
    try:
        if not session['audio_path']:
            return jsonify({'error': 'No audio loaded'}), 400

        logger.info("Extracting lyrics...")
        extractor = LyricsExtractor()
        result = extractor.extract(session['audio_path'])

        lyrics = []
        for segment in result['segments']:
            lyrics.append({
                'start': segment['start'],
                'end': segment['end'],
                'text': segment['text']
            })

        session['auto_lyrics'] = lyrics

        return jsonify({
            'success': True,
            'lyrics': lyrics,
            'language': result.get('language', 'unknown')
        })

    except Exception as e:
        logger.error(f"Extraction error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/audio/<path:filename>')
def serve_audio(filename):
    """Serve audio file for player"""
    try:
        # Serve from temp directory
        file_path = TEMP_DIR / filename
        if file_path.exists():
            return send_file(str(file_path))

        # Or from full path
        file_path = Path(filename)
        if file_path.exists():
            return send_file(str(file_path))

        return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        logger.error(f"Audio serve error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/save-lyrics', methods=['POST'])
def save_lyrics():
    """Step 4: Save finalized lyrics"""
    try:
        data = request.json
        lyrics = data.get('lyrics', [])

        session['final_lyrics'] = lyrics

        return jsonify({'success': True})

    except Exception as e:
        logger.error(f"Save error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/generate', methods=['POST'])
def generate():
    """Step 5: Generate karaoke video"""
    try:
        if not session['instrumental_path']:
            return jsonify({'error': 'No instrumental track'}), 400

        if not session['final_lyrics']:
            return jsonify({'error': 'No lyrics saved'}), 400

        logger.info("Generating karaoke video...")

        # Convert lyrics to expected format
        lyrics_data = {
            'segments': session['final_lyrics']
        }

        # Create output path
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_title = "".join(c for c in session['title'] if c.isalnum() or c in (' ', '-', '_')).strip()
        output_filename = f"{safe_title}_{timestamp}_karaoke.mp4"
        output_path = OUTPUT_DIR / output_filename

        generator = KaraokeVideoGenerator()
        generator.generate(
            audio_path=session['instrumental_path'],
            lyrics_data=lyrics_data,
            output_path=str(output_path),
            title=session['title']
        )

        session['video_path'] = str(output_path)

        return jsonify({
            'success': True,
            'output_path': str(output_path)
        })

    except Exception as e:
        logger.error(f"Generation error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/status')
def status():
    """Get current session status"""
    return jsonify({
        'title': session.get('title'),
        'has_audio': session.get('audio_path') is not None,
        'has_instrumental': session.get('instrumental_path') is not None,
        'has_auto_lyrics': session.get('auto_lyrics') is not None,
        'has_final_lyrics': session.get('final_lyrics') is not None,
        'audio_filename': Path(session['audio_path']).name if session.get('audio_path') else None
    })


if __name__ == '__main__':
    print("\n" + "="*70)
    print("🎤 KARAOKE MAKER - ALL-IN-ONE")
    print("="*70)
    print("\nStarting web server...")
    print("Open your browser to: http://localhost:5001")
    print("\nComplete workflow:")
    print("  1. Download from YouTube")
    print("  2. Separate vocals automatically")
    print("  3. Time your lyrics with easy editor")
    print("  4. Generate karaoke video")
    print("\nPress Ctrl+C to stop the server")
    print("="*70 + "\n")

    app.run(debug=True, port=5001)
