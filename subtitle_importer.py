"""
Import lyrics from subtitle files (SRT, ASS)
Converts to karaoke-maker format
"""
import re
from pathlib import Path
from typing import List, Dict


def parse_srt(file_path: str) -> List[Dict]:
    """
    Parse SRT subtitle file

    Format:
    1
    00:00:20,000 --> 00:00:24,400
    Lyric text here

    Returns list of segments with start, end, text
    """
    segments = []

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Split by double newline
    blocks = content.strip().split('\n\n')

    for block in blocks:
        lines = block.strip().split('\n')
        if len(lines) < 3:
            continue

        # Parse timing line (second line)
        timing_line = lines[1]
        match = re.match(r'(\d{2}):(\d{2}):(\d{2}),(\d{3}) --> (\d{2}):(\d{2}):(\d{2}),(\d{3})', timing_line)

        if match:
            # Start time
            start_h, start_m, start_s, start_ms = map(int, match.groups()[:4])
            start = start_h * 3600 + start_m * 60 + start_s + start_ms / 1000

            # End time
            end_h, end_m, end_s, end_ms = map(int, match.groups()[4:])
            end = end_h * 3600 + end_m * 60 + end_s + end_ms / 1000

            # Text (third line onwards)
            text = '\n'.join(lines[2:])

            segments.append({
                'start': start,
                'end': end,
                'text': text
            })

    return segments


def parse_ass(file_path: str) -> List[Dict]:
    """
    Parse ASS/SSA subtitle file (Aegisub format)

    Format:
    Dialogue: 0,0:00:20.00,0:00:24.40,Default,,0,0,0,,Lyric text here

    Returns list of segments with start, end, text
    """
    segments = []

    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()

            if line.startswith('Dialogue:'):
                # Parse dialogue line
                parts = line.split(',', 9)
                if len(parts) < 10:
                    continue

                # Extract timing
                start_str = parts[1]  # 0:00:20.00
                end_str = parts[2]    # 0:00:24.40
                text = parts[9]       # Lyric text (may have formatting codes)

                # Remove ASS formatting codes like {\i1}, {\b1}, etc.
                text = re.sub(r'\{[^}]*\}', '', text)

                # Parse start time
                start = parse_ass_time(start_str)

                # Parse end time
                end = parse_ass_time(end_str)

                segments.append({
                    'start': start,
                    'end': end,
                    'text': text
                })

    return segments


def parse_ass_time(time_str: str) -> float:
    """
    Parse ASS time format: 0:00:20.00 or 1:23:45.67
    Returns seconds as float
    """
    parts = time_str.split(':')

    if len(parts) == 3:
        h, m, s = parts
    else:
        h = 0
        m, s = parts

    h = int(h)
    m = int(m)
    s = float(s)

    return h * 3600 + m * 60 + s


def import_subtitles(file_path: str) -> Dict:
    """
    Import subtitle file and convert to karaoke-maker format

    Supports:
    - .srt files
    - .ass/.ssa files (Aegisub)

    Returns:
        Dictionary with 'segments' key containing list of lyrics
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    ext = file_path.suffix.lower()

    if ext == '.srt':
        segments = parse_srt(str(file_path))
    elif ext in ['.ass', '.ssa']:
        segments = parse_ass(str(file_path))
    else:
        raise ValueError(f"Unsupported file format: {ext}. Use .srt or .ass")

    return {
        'segments': segments,
        'language': 'unknown'
    }


if __name__ == '__main__':
    import sys
    import json

    if len(sys.argv) > 1:
        file_path = sys.argv[1]

        try:
            lyrics_data = import_subtitles(file_path)
            print(json.dumps(lyrics_data, indent=2, ensure_ascii=False))
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print("Usage: python subtitle_importer.py <subtitle_file.srt|ass>")
        sys.exit(1)
