---
title: Karaoke Maker
emoji: 🎤
colorFrom: purple
colorTo: indigo
sdk: gradio
sdk_version: 4.44.0
app_file: app_gradio.py
pinned: false
license: mit
---

# 🎤 Karaoke Maker

Turn any song into karaoke magic with AI!

## Features

- **Download** audio from YouTube
- **Separate** vocals from instrumentals using Demucs AI
- **Extract** lyrics automatically using OpenAI Whisper
- **Generate** professional karaoke videos with synced lyrics

## How to Use

1. Paste a YouTube URL and click Download
2. Click "Separate Vocals" to extract the instrumental track
3. Click "Auto-Extract" to get AI-generated lyrics (or enter manually)
4. Edit the lyrics timing if needed
5. Click "Generate" to create your karaoke video!

## Technical Details

- Uses **Demucs** for state-of-the-art audio source separation
- Uses **OpenAI Whisper** for accurate speech-to-text
- Generates MP4 video with synchronized lyrics display
