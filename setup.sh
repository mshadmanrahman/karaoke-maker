#!/bin/bash
# Setup script for Karaoke Maker

echo "========================================="
echo "Karaoke Maker - Setup"
echo "========================================="
echo ""

# Check Python version
echo "Checking Python version..."
python3 --version

if [ $? -ne 0 ]; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

# Check if ffmpeg is installed
echo ""
echo "Checking for ffmpeg..."
if ! command -v ffmpeg &> /dev/null; then
    echo "Warning: ffmpeg is not installed"
    echo "Installing ffmpeg via Homebrew..."

    if ! command -v brew &> /dev/null; then
        echo "Error: Homebrew is not installed. Please install it from https://brew.sh"
        exit 1
    fi

    brew install ffmpeg
else
    echo "✓ ffmpeg is already installed"
fi

# Create virtual environment
echo ""
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo ""
echo "Installing Python dependencies..."
echo "This may take 5-10 minutes as it downloads ML models..."
pip install -r requirements.txt

# Create .env file
echo ""
echo "Creating configuration file..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✓ Created .env file"
    echo ""
    echo "Please edit .env and set your output directory:"
    echo "  OUTPUT_DIR=/path/to/your/karaoke/videos"
else
    echo "✓ .env file already exists"
fi

# Make main script executable
echo ""
echo "Making scripts executable..."
chmod +x karaoke_maker.py
chmod +x setup.sh

echo ""
echo "========================================="
echo "✓ Setup complete!"
echo "========================================="
echo ""
echo "To use Karaoke Maker:"
echo "  1. Edit .env to set your output directory"
echo "  2. Activate virtual environment: source venv/bin/activate"
echo "  3. Run: python karaoke_maker.py <youtube_url>"
echo ""
echo "Example:"
echo "  python karaoke_maker.py 'https://youtube.com/watch?v=dQw4w9WgXcQ'"
echo ""
