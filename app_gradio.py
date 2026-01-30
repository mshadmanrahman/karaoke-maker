#!/usr/bin/env python3
"""
Karaoke Maker - Hugging Face Spaces Gradio App
===============================================

A web interface for creating karaoke videos from YouTube using Gradio.

Workflow:
    1. Download - Get audio from YouTube using yt-dlp
    2. Separate - AI vocal/instrumental separation using Demucs
    3. Extract Lyrics - Auto-extract lyrics with Whisper AI
    4. Generate - Create karaoke video with synced lyrics
"""

import gradio as gr
from pathlib import Path
import json
import logging
import tempfile
import os
from datetime import datetime

# Import our modules
from downloader import YouTubeDownloader
from separator import VocalSeparator
from lyrics_extractor import LyricsExtractor
from video_generator import KaraokeVideoGenerator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Directories
TEMP_DIR = Path(tempfile.gettempdir()) / 'karaoke-temp'
TEMP_DIR.mkdir(parents=True, exist_ok=True)

# Session state
session = {
    'youtube_url': None,
    'audio_path': None,
    'instrumental_path': None,
    'title': None,
    'auto_lyrics': None,
}


def download_from_youtube(url: str, progress=gr.Progress()):
    """Step 1: Download audio from YouTube"""
    if not url or not url.strip():
        return None, "❌ Please enter a YouTube URL", None, gr.update(visible=False)
    
    try:
        progress(0.1, desc="Starting download...")
        logger.info(f"Downloading: {url}")
        
        downloader = YouTubeDownloader(TEMP_DIR)
        progress(0.3, desc="Fetching video info...")
        result = downloader.download(url)
        
        session['youtube_url'] = url
        session['audio_path'] = result['audio_path']
        session['title'] = result['title']
        
        progress(1.0, desc="Complete!")
        
        return (
            result['audio_path'],
            f"✅ Downloaded: **{result['title']}**",
            result['title'],
            gr.update(visible=True)  # Show next section
        )
        
    except Exception as e:
        logger.error(f"Download error: {e}")
        return None, f"❌ Error: {str(e)}", None, gr.update(visible=False)


def separate_vocals(audio_path: str, progress=gr.Progress()):
    """Step 2: Separate vocals from instrumental"""
    if not audio_path or not Path(audio_path).exists():
        return None, None, "❌ No audio file available. Please download first.", gr.update(visible=False)
    
    try:
        progress(0.1, desc="Loading Demucs model...")
        separator = VocalSeparator(TEMP_DIR)
        
        progress(0.3, desc="Separating vocals (this takes 2-5 minutes)...")
        result = separator.separate(audio_path)
        
        session['instrumental_path'] = result['instrumental']
        
        progress(1.0, desc="Complete!")
        
        return (
            result['vocals'],
            result['instrumental'],
            "✅ Vocals separated successfully!",
            gr.update(visible=True)  # Show next section
        )
        
    except Exception as e:
        logger.error(f"Separation error: {e}")
        return None, None, f"❌ Error: {str(e)}", gr.update(visible=False)


def extract_lyrics(audio_path: str, progress=gr.Progress()):
    """Step 3: Auto-extract lyrics using Whisper"""
    if not audio_path or not Path(audio_path).exists():
        return "", "❌ No audio file available."
    
    try:
        progress(0.1, desc="Loading Whisper model...")
        extractor = LyricsExtractor()
        
        progress(0.3, desc="Transcribing audio (this takes 1-3 minutes)...")
        result = extractor.extract(audio_path)
        
        # Format lyrics for display and editing
        lyrics_text = ""
        lyrics_data = []
        for segment in result['segments']:
            start = segment['start']
            end = segment['end']
            text = segment['text'].strip()
            lyrics_text += f"[{start:.2f} - {end:.2f}] {text}\n"
            lyrics_data.append({
                'start': start,
                'end': end,
                'text': text
            })
        
        session['auto_lyrics'] = lyrics_data
        
        progress(1.0, desc="Complete!")
        
        detected_lang = result.get('language', 'unknown')
        return (
            lyrics_text,
            f"✅ Extracted {len(lyrics_data)} lines (detected: {detected_lang})"
        )
        
    except Exception as e:
        logger.error(f"Extraction error: {e}")
        return "", f"❌ Error: {str(e)}"


def parse_lyrics_text(lyrics_text: str):
    """Parse lyrics text back to structured format"""
    import re
    lyrics = []
    
    for line in lyrics_text.strip().split('\n'):
        if not line.strip():
            continue
        
        # Try to parse [start - end] text format
        match = re.match(r'\[(\d+\.?\d*)\s*-\s*(\d+\.?\d*)\]\s*(.*)', line)
        if match:
            lyrics.append({
                'start': float(match.group(1)),
                'end': float(match.group(2)),
                'text': match.group(3).strip()
            })
        else:
            # Just text, use auto timing
            lyrics.append({
                'start': len(lyrics) * 3.0,  # Simple 3-second intervals
                'end': len(lyrics) * 3.0 + 2.5,
                'text': line.strip()
            })
    
    return lyrics


def generate_video(instrumental_path: str, lyrics_text: str, title: str, progress=gr.Progress()):
    """Step 4: Generate karaoke video"""
    if not instrumental_path or not Path(instrumental_path).exists():
        return None, "❌ No instrumental track. Please complete separation first."
    
    if not lyrics_text or not lyrics_text.strip():
        return None, "❌ No lyrics provided. Please extract or enter lyrics."
    
    try:
        progress(0.1, desc="Parsing lyrics...")
        lyrics = parse_lyrics_text(lyrics_text)
        
        if not lyrics:
            return None, "❌ Could not parse lyrics. Please check format."
        
        lyrics_data = {'segments': lyrics}
        
        # Create output path
        progress(0.2, desc="Setting up video generation...")
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_title = "".join(c for c in (title or "karaoke") if c.isalnum() or c in (' ', '-', '_')).strip()
        output_filename = f"{safe_title}_{timestamp}_karaoke.mp4"
        output_path = TEMP_DIR / output_filename
        
        progress(0.3, desc="Generating video (this takes 3-5 minutes)...")
        generator = KaraokeVideoGenerator()
        generator.generate(
            audio_path=instrumental_path,
            lyrics_data=lyrics_data,
            output_path=str(output_path),
            title=title or "Karaoke"
        )
        
        progress(1.0, desc="Complete!")
        
        return (
            str(output_path),
            f"✅ Video generated: **{output_filename}**"
        )
        
    except Exception as e:
        logger.error(f"Generation error: {e}")
        return None, f"❌ Error: {str(e)}"


# Build Gradio Interface
with gr.Blocks(
    title="🎤 Karaoke Maker",
    theme=gr.themes.Soft(
        primary_hue="violet",
        secondary_hue="purple",
    ),
    css="""
    .gradio-container { max-width: 900px !important; }
    .title { text-align: center; margin-bottom: 1rem; }
    .subtitle { text-align: center; color: #666; margin-bottom: 2rem; }
    """
) as demo:
    
    # Header
    gr.Markdown(
        """
        # 🎤 Karaoke Maker
        ### Turn any song into karaoke magic with AI
        
        **Workflow:** Download → Separate Vocals → Extract Lyrics → Generate Video
        """,
        elem_classes=["title"]
    )
    
    # State variables
    audio_path_state = gr.State(None)
    vocals_path_state = gr.State(None)
    instrumental_path_state = gr.State(None)
    title_state = gr.State(None)
    
    # Step 1: Download
    with gr.Group():
        gr.Markdown("## 📥 Step 1: Download from YouTube")
        with gr.Row():
            url_input = gr.Textbox(
                label="YouTube URL",
                placeholder="https://www.youtube.com/watch?v=...",
                scale=4
            )
            download_btn = gr.Button("🔽 Download", variant="primary", scale=1)
        download_status = gr.Markdown("")
    
    # Step 2: Separate
    with gr.Group(visible=False) as separate_section:
        gr.Markdown("## 🎵 Step 2: Separate Vocals")
        gr.Markdown("*AI will separate vocals from instrumentals using Demucs. This takes 2-5 minutes.*")
        separate_btn = gr.Button("✨ Separate Vocals", variant="primary", size="lg")
        separate_status = gr.Markdown("")
        with gr.Row():
            vocals_audio = gr.Audio(label="Vocals", type="filepath")
            instrumental_audio = gr.Audio(label="Instrumental (Karaoke)", type="filepath")
    
    # Step 3: Lyrics
    with gr.Group(visible=False) as lyrics_section:
        gr.Markdown("## ⏱️ Step 3: Extract & Edit Lyrics")
        with gr.Row():
            extract_btn = gr.Button("🤖 Auto-Extract with AI", variant="secondary")
            extract_status = gr.Markdown("")
        lyrics_editor = gr.Textbox(
            label="Lyrics (format: [start - end] text)",
            placeholder="[0.00 - 2.50] First line of lyrics\n[3.00 - 5.50] Second line...",
            lines=15
        )
        gr.Markdown("""
        **Format:** `[start_seconds - end_seconds] lyric text`
        
        You can edit the timing and text directly. Each line should have start time, end time, and the lyric.
        """)
    
    # Step 4: Generate
    with gr.Group(visible=False) as generate_section:
        gr.Markdown("## 🎬 Step 4: Generate Karaoke Video")
        gr.Markdown("*This combines the instrumental track with your timed lyrics. Takes 3-5 minutes.*")
        generate_btn = gr.Button("🎥 Generate Karaoke Video", variant="primary", size="lg")
        generate_status = gr.Markdown("")
        output_video = gr.Video(label="Your Karaoke Video")
    
    # Wire up events
    download_btn.click(
        fn=download_from_youtube,
        inputs=[url_input],
        outputs=[audio_path_state, download_status, title_state, separate_section]
    )
    
    separate_btn.click(
        fn=separate_vocals,
        inputs=[audio_path_state],
        outputs=[vocals_audio, instrumental_audio, separate_status, lyrics_section]
    ).then(
        fn=lambda: gr.update(visible=True),
        outputs=[generate_section]
    )
    
    # Store instrumental path when separation completes
    instrumental_audio.change(
        fn=lambda x: x,
        inputs=[instrumental_audio],
        outputs=[instrumental_path_state]
    )
    
    extract_btn.click(
        fn=extract_lyrics,
        inputs=[audio_path_state],
        outputs=[lyrics_editor, extract_status]
    )
    
    generate_btn.click(
        fn=generate_video,
        inputs=[instrumental_path_state, lyrics_editor, title_state],
        outputs=[output_video, generate_status]
    )


# Launch for Hugging Face Spaces
if __name__ == "__main__":
    demo.queue()
    demo.launch()
