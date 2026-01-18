#!/usr/bin/env python3
"""
All-in-one Karaoke Maker Web App with Progress Tracking
Complete workflow: Download → Separate → Time Lyrics → Generate Video
"""
from flask import Flask, render_template, request, jsonify, send_file
from pathlib import Path
import json
import logging
import threading
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

# Progress tracking (global since we're single-user for now)
progress = {
    'task': None,        # 'download', 'separate', 'extract', 'generate'
    'status': 'idle',    # 'idle', 'running', 'complete', 'error'
    'progress': 0,       # 0-100
    'message': '',
    'error': None,
    'result': None
}


def update_progress(task=None, status=None, progress_percent=None, message=None, error=None, result=None):
    """Update progress state"""
    global progress
    if task is not None:
        progress['task'] = task
    if status is not None:
        progress['status'] = status
    if progress_percent is not None:
        progress['progress'] = progress_percent
    if message is not None:
        progress['message'] = message
    if error is not None:
        progress['error'] = error
    if result is not None:
        progress['result'] = result


@app.route('/')
def index():
    """Main page"""
    return render_template('app.html')


@app.route('/api/progress')
def get_progress():
    """Get current progress"""
    return jsonify(progress)


@app.route('/api/download', methods=['POST'])
def download():
    """Step 1: Download from YouTube"""
    try:
        data = request.json
        youtube_url = data.get('url')

        if not youtube_url:
            return jsonify({'error': 'No URL provided'}), 400

        def download_task():
            try:
                update_progress('download', 'running', 0, 'Downloading from YouTube...')

                downloader = YouTubeDownloader(TEMP_DIR)
                result = downloader.download(youtube_url)

                session['youtube_url'] = youtube_url
                session['audio_path'] = result['audio_path']
                session['title'] = result['title']

                update_progress(
                    'download',
                    'complete',
                    100,
                    f"Downloaded: {result['title']}",
                    result={'title': result['title']}
                )

            except Exception as e:
                logger.error(f"Download error: {e}")
                update_progress('download', 'error', 0, str(e), error=str(e))

        # Start download in background
        thread = threading.Thread(target=download_task)
        thread.daemon = True
        thread.start()

        return jsonify({'success': True, 'message': 'Download started'})

    except Exception as e:
        logger.error(f"Download error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/separate', methods=['POST'])
def separate():
    """Step 2: Separate vocals"""
    try:
        if not session['audio_path']:
            return jsonify({'error': 'No audio loaded'}), 400

        def separate_task():
            try:
                update_progress('separate', 'running', 0, 'Separating vocals (2-3 minutes)...')

                separator = VocalSeparator(TEMP_DIR)
                result = separator.separate(session['audio_path'])

                session['instrumental_path'] = result['instrumental']

                update_progress('separate', 'complete', 100, 'Vocals separated successfully')

            except Exception as e:
                logger.error(f"Separation error: {e}")
                update_progress('separate', 'error', 0, str(e), error=str(e))

        # Start separation in background
        thread = threading.Thread(target=separate_task)
        thread.daemon = True
        thread.start()

        return jsonify({'success': True, 'message': 'Separation started'})

    except Exception as e:
        logger.error(f"Separation error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/extract-lyrics', methods=['POST'])
def extract_lyrics():
    """Step 3: Auto-extract lyrics (optional)"""
    try:
        if not session['audio_path']:
            return jsonify({'error': 'No audio loaded'}), 400

        def extract_task():
            try:
                update_progress('extract', 'running', 0, 'Extracting lyrics...')

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

                update_progress(
                    'extract',
                    'complete',
                    100,
                    f"Extracted {len(lyrics)} lyric lines",
                    result={
                        'lyrics': lyrics,
                        'language': result.get('language', 'unknown')
                    }
                )

            except Exception as e:
                logger.error(f"Extraction error: {e}")
                update_progress('extract', 'error', 0, str(e), error=str(e))

        # Start extraction in background
        thread = threading.Thread(target=extract_task)
        thread.daemon = True
        thread.start()

        return jsonify({'success': True, 'message': 'Extraction started'})

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

        def generate_task():
            try:
                update_progress('generate', 'running', 0, 'Preparing video generation...')

                # Convert lyrics to expected format
                lyrics_data = {
                    'segments': session['final_lyrics']
                }

                # Create output path
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                safe_title = "".join(c for c in session['title'] if c.isalnum() or c in (' ', '-', '_')).strip()
                output_filename = f"{safe_title}_{timestamp}_karaoke.mp4"
                output_path = OUTPUT_DIR / output_filename

                update_progress('generate', 'running', 10, 'Creating lyric segments...')

                generator = KaraokeVideoGenerator()

                # Note: We can't easily get progress from video_generator
                # So we'll just update at major milestones
                update_progress('generate', 'running', 30, 'Generating lyric frames...')

                generator.generate(
                    audio_path=session['instrumental_path'],
                    lyrics_data=lyrics_data,
                    output_path=str(output_path),
                    title=session['title']
                )

                session['video_path'] = str(output_path)

                update_progress(
                    'generate',
                    'complete',
                    100,
                    'Karaoke video generated successfully!',
                    result={'output_path': str(output_path)}
                )

            except Exception as e:
                logger.error(f"Generation error: {e}")
                update_progress('generate', 'error', 0, str(e), error=str(e))

        # Start generation in background
        thread = threading.Thread(target=generate_task)
        thread.daemon = True
        thread.start()

        return jsonify({'success': True, 'message': 'Video generation started'})

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
    print("🎤 KARAOKE MAKER - ALL-IN-ONE (WITH PROGRESS)")
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

    app.run(debug=True, port=5001, threaded=True)
