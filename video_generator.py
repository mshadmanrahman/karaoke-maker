"""
Video generator module
Creates karaoke videos with synced lyrics and word-by-word highlighting
"""
import logging
from pathlib import Path
from typing import List, Dict, Optional
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import subprocess
import tempfile
import os
from moviepy import (
    AudioFileClip,
    VideoFileClip,
    CompositeVideoClip,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class KaraokeVideoGenerator:
    """Generates karaoke videos with synced lyrics and word highlighting"""

    def __init__(
        self,
        width: int = 1920,
        height: int = 1080,
        fps: int = 30,
        font_size: int = 72,
        font_color: tuple = (255, 255, 255),
        highlight_color: tuple = (255, 255, 0),
        bg_color: tuple = (0, 0, 0)
    ):
        """
        Initialize video generator

        Args:
            width: Video width in pixels
            height: Video height in pixels
            fps: Frames per second
            font_size: Font size for lyrics
            font_color: Default text color (RGB tuple)
            highlight_color: Color for highlighted/active lyrics (RGB tuple)
            bg_color: Background color (RGB tuple)
        """
        self.width = width
        self.height = height
        self.fps = fps
        self.font_size = font_size
        self.font_color = font_color
        self.highlight_color = highlight_color
        self.bg_color = bg_color

        # Try to load a good font with Unicode/Bengali support
        font_paths = [
            # User's Bengali fonts (best quality)
            str(Path.home() / "Library/Fonts/NotoSansBengali-Bold.ttf"),
            str(Path.home() / "Library/Fonts/NotoSansBengali-ExtraBold.ttf"),
            str(Path.home() / "Library/Fonts/NotoSerifBengali-Black.ttf"),
            # System Bengali fonts
            "/System/Library/Fonts/KohinoorBangla.ttc",
            "/System/Library/Fonts/Supplemental/Bangla Sangam MN.ttc",
            "/System/Library/Fonts/Supplemental/Bangla MN.ttc",
            "/System/Library/Fonts/Kohinoor.ttc",
            # Fallback to general Unicode fonts
            "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
            # Standard fonts as last resort
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
        ]

        font_loaded = False
        for font_path in font_paths:
            try:
                self.font = ImageFont.truetype(font_path, font_size)
                logger.info(f"Loaded font: {font_path}")
                font_loaded = True
                break
            except:
                continue

        if not font_loaded:
            logger.warning("Could not load any Unicode font, using default (may not support Bengali)")
            self.font = ImageFont.load_default()

        # Preview font (smaller)
        try:
            # Use same font family for preview
            for font_path in font_paths:
                try:
                    self.preview_font = ImageFont.truetype(font_path, font_size - 20)
                    break
                except:
                    continue
        except:
            self.preview_font = self.font

    def wrap_text(self, text: str, max_width: int) -> list:
        """
        Wrap text to fit within max_width pixels

        Args:
            text: Text to wrap
            max_width: Maximum width in pixels

        Returns:
            List of wrapped lines
        """
        words = text.split()
        lines = []
        current_line = []

        for word in words:
            # Try adding this word to current line
            test_line = ' '.join(current_line + [word])
            bbox = Image.new('RGB', (1, 1)).getbbox()
            draw = ImageDraw.Draw(Image.new('RGB', (1, 1)))
            bbox = draw.textbbox((0, 0), test_line, font=self.font)
            width = bbox[2] - bbox[0]

            if width <= max_width:
                current_line.append(word)
            else:
                # Line is too long, start a new line
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]

        # Add the last line
        if current_line:
            lines.append(' '.join(current_line))

        return lines if lines else [text]

    def create_frame(
        self,
        text: str,
        highlight_progress: float = 0.0,
        next_line: str = ""
    ) -> np.ndarray:
        """
        Create a single video frame with lyrics

        Args:
            text: Current lyrics line
            highlight_progress: Progress of highlighting (0.0 to 1.0)
            next_line: Next line to preview

        Returns:
            Frame as numpy array
        """
        # Create blank image
        img = Image.new('RGB', (self.width, self.height), self.bg_color)
        draw = ImageDraw.Draw(img)

        # Calculate text dimensions and position for current line (centered)
        if text:
            # Wrap text if too long (use 90% of screen width)
            max_width = int(self.width * 0.9)
            wrapped_lines = self.wrap_text(text, max_width)

            # Calculate total height for all wrapped lines
            total_height = 0
            line_heights = []
            for line in wrapped_lines:
                bbox = draw.textbbox((0, 0), line, font=self.font)
                line_height = bbox[3] - bbox[1]
                line_heights.append(line_height)
                total_height += line_height

            # Add spacing between lines
            line_spacing = 10
            total_height += line_spacing * (len(wrapped_lines) - 1)

            # Start y position (centered vertically)
            y_start = (self.height - total_height) // 2 - 50

            # Draw each wrapped line
            current_y = y_start
            chars_drawn = 0

            for i, line in enumerate(wrapped_lines):
                bbox = draw.textbbox((0, 0), line, font=self.font)
                line_width = bbox[2] - bbox[0]
                x = (self.width - line_width) // 2

                # Draw the full line in white first
                draw.text((x, current_y), line, font=self.font, fill=self.font_color)

                # Calculate highlighting for this line
                chars_in_line = len(line)
                total_chars = len(text)
                chars_to_highlight = int(total_chars * highlight_progress)

                if chars_to_highlight > chars_drawn:
                    # Some of this line should be highlighted
                    line_highlight_chars = min(chars_to_highlight - chars_drawn, chars_in_line)
                    highlighted_text = line[:line_highlight_chars]

                    # Draw highlighted portion in yellow
                    draw.text((x, current_y), highlighted_text, font=self.font, fill=self.highlight_color)

                chars_drawn += chars_in_line + 1  # +1 for space

                current_y += line_heights[i] + line_spacing

            # Draw next line preview below (smaller, dimmed)
            if next_line:
                # Wrap next line too
                next_wrapped = self.wrap_text(next_line, max_width)
                preview_y = current_y + 20

                for preview_line in next_wrapped[:2]:  # Show max 2 lines of preview
                    preview_bbox = draw.textbbox((0, 0), preview_line, font=self.preview_font)
                    preview_width = preview_bbox[2] - preview_bbox[0]
                    preview_x = (self.width - preview_width) // 2

                    # Draw preview in dimmed white (gray)
                    draw.text((preview_x, preview_y), preview_line, font=self.preview_font, fill=(180, 180, 180))

                    preview_height = preview_bbox[3] - preview_bbox[1]
                    preview_y += preview_height + 5

        return np.array(img)

    def generate(
        self,
        audio_path: str,
        lyrics_data: Dict,
        output_path: str,
        title: Optional[str] = None
    ):
        """
        Generate karaoke video

        Args:
            audio_path: Path to instrumental audio
            lyrics_data: Lyrics dictionary from LyricsExtractor
            output_path: Path to save output video
            title: Optional song title to display
        """
        logger.info("Generating karaoke video...")
        logger.info(f"Audio: {audio_path}")
        logger.info(f"Output: {output_path}")

        # Create temporary directory for segment videos
        temp_dir = tempfile.mkdtemp()

        try:
            # Load audio
            audio = AudioFileClip(audio_path)
            duration = audio.duration

            logger.info(f"Creating {len(lyrics_data['segments'])} lyrics segments...")

            segment_files = []

            # Create video segments for each lyrics line
            for i, segment in enumerate(lyrics_data['segments']):
                text = segment['text']
                start = segment['start']
                end = segment['end']
                segment_duration = end - start

                # Get next line for preview
                next_line = ""
                if i + 1 < len(lyrics_data['segments']):
                    next_line = lyrics_data['segments'][i + 1]['text']

                # Create frames for this segment
                num_frames = max(int(segment_duration * self.fps), 1)
                frames = []

                for frame_idx in range(num_frames):
                    # Calculate highlight progress (0.0 to 1.0)
                    progress = frame_idx / max(num_frames - 1, 1)
                    frame = self.create_frame(text, progress, next_line)
                    frames.append(Image.fromarray(frame.astype('uint8'), 'RGB'))

                # Save frames as a video segment using PIL and FFmpeg
                segment_file = os.path.join(temp_dir, f'segment_{i:04d}.mp4')
                frame_pattern = os.path.join(temp_dir, f'seg{i:04d}_%04d.png')

                # Save frames as images
                for fidx, frame in enumerate(frames):
                    frame.save(frame_pattern % fidx)

                # Use FFmpeg to create video segment from frames
                ffmpeg_cmd = [
                    'ffmpeg', '-y',
                    '-framerate', str(self.fps),
                    '-i', frame_pattern,
                    '-c:v', 'libx264',
                    '-pix_fmt', 'yuv420p',
                    '-preset', 'fast',
                    segment_file
                ]
                subprocess.run(ffmpeg_cmd, check=True, capture_output=True)

                # Clean up frame images
                for fidx in range(len(frames)):
                    os.remove(frame_pattern % fidx)

                segment_files.append((segment_file, start, end))

            # Create full-duration background video
            logger.info("Creating background video...")
            background_frame = self.create_frame("", 0.0, "")
            bg_image = Image.fromarray(background_frame.astype('uint8'), 'RGB')
            bg_path = os.path.join(temp_dir, 'background.png')
            bg_image.save(bg_path)

            bg_video_path = os.path.join(temp_dir, 'background.mp4')
            ffmpeg_bg_cmd = [
                'ffmpeg', '-y',
                '-loop', '1',
                '-i', bg_path,
                '-t', str(duration),
                '-c:v', 'libx264',
                '-pix_fmt', 'yuv420p',
                '-r', str(self.fps),
                bg_video_path
            ]
            subprocess.run(ffmpeg_bg_cmd, check=True, capture_output=True)

            # Load all video clips
            logger.info("Compositing video segments...")
            background_clip = VideoFileClip(bg_video_path)
            clips = [background_clip]

            for seg_file, start, end in segment_files:
                seg_clip = VideoFileClip(seg_file).with_start(start)
                clips.append(seg_clip)

            # Composite video
            final_video = CompositeVideoClip(clips, size=(self.width, self.height))
            final_video = final_video.with_audio(audio)

            # Write final video
            logger.info("Rendering final video (this may take 3-5 minutes)...")
            final_video.write_videofile(
                output_path,
                fps=self.fps,
                codec='libx264',
                audio_codec='aac',
                bitrate='5000k',
                threads=4,
                preset='medium'
            )

            # Clean up
            final_video.close()
            background_clip.close()
            audio.close()

            logger.info(f"Karaoke video created successfully: {output_path}")

        except Exception as e:
            logger.error(f"Error generating video: {e}")
            raise
        finally:
            # Clean up temporary files
            import shutil
            try:
                shutil.rmtree(temp_dir)
            except:
                pass


def generate_karaoke_video(
    audio_path: str,
    lyrics_data: Dict,
    output_path: str,
    title: Optional[str] = None
):
    """
    Convenience function to generate karaoke video

    Args:
        audio_path: Path to instrumental audio
        lyrics_data: Lyrics dictionary
        output_path: Output video path
        title: Optional song title
    """
    generator = KaraokeVideoGenerator()
    generator.generate(audio_path, lyrics_data, output_path, title)


if __name__ == '__main__':
    # Test the generator
    import sys
    import json

    if len(sys.argv) > 2:
        test_audio = sys.argv[1]
        test_lyrics_json = sys.argv[2]
        output = sys.argv[3] if len(sys.argv) > 3 else 'test_karaoke.mp4'

        with open(test_lyrics_json, 'r') as f:
            lyrics_data = json.load(f)

        generate_karaoke_video(test_audio, lyrics_data, output)
        print(f"Video generated: {output}")
    else:
        print("Usage: python video_generator.py <audio_file> <lyrics_json> [output_video]")
