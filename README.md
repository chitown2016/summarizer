# YouTube Video Summarizer & Chat

A web application that downloads YouTube videos, transcribes them, generates summaries, and allows you to chat with the video content using AI.

## Features

- 🎥 **YouTube Video Processing**: Download and process YouTube videos
- 🎤 **Speech-to-Text**: Transcribe video audio using OpenAI Whisper
- 📝 **AI Summarization**: Generate comprehensive summaries using free AI models
- 💬 **Interactive Chat**: Ask questions about the video content using RAG (Retrieval-Augmented Generation)
- 🔍 **Vector Search**: Semantic search through video content
- 📱 **Modern Web UI**: Clean, responsive interface

## Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **yt-dlp** - YouTube video downloader
- **OpenAI Whisper** - Speech-to-text transcription
- **Transformers** - AI summarization models
- **ChromaDB** - Vector database for embeddings
- **LangChain** - RAG framework for chat

### Frontend
- **React** - Modern UI framework
- **Tailwind CSS** - Styling
- **React Dropzone** - File upload handling

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd summarizer
   ```

2. **Ensure Python 3.11 is installed**
   
   This project requires **Python 3.11** for optimal compatibility with all dependencies.
   
   **Check your Python version:**
   ```bash
   python --version
   # or
   python3 --version
   ```
   
   **Install Python 3.11 if needed:**
   - **Windows**: Download from https://www.python.org/downloads/
   - **macOS**: `brew install python@3.11`
   - **Linux**: `sudo apt install python3.11` (Ubuntu/Debian)

3. **Create and activate a virtual environment**
   
   **On Windows:**
   ```bash
   python3.11 -m venv venv
   venv\Scripts\activate
   ```
   
   **On macOS/Linux:**
   ```bash
   python3.11 -m venv venv
   source venv/bin/activate
   ```

4. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Install FFmpeg** (required for audio processing)
   - **Windows**: Download from https://ffmpeg.org/download.html
   - **macOS**: `brew install ffmpeg`
   - **Linux**: `sudo apt install ffmpeg`

6. **Set up environment variables**
   ```bash
   cp env.example .env
   # Edit .env with your configuration
   ```

## Usage

1. **Activate the virtual environment** (if not already activated)
   
   **On Windows:**
   ```bash
   venv\Scripts\activate
   ```
   
   **On macOS/Linux:**
   ```bash
   source venv/bin/activate
   ```

2. **Start the backend server**
   ```bash
   python -m uvicorn backend.main:app --reload
   ```

3. **Start the frontend** (in a new terminal)
   ```bash
   cd frontend
   npm install
   npm start
   ```

4. **Open your browser** and navigate to `http://localhost:3000`

## API Endpoints

- `POST /api/process-video` - Process YouTube video
- `POST /api/summarize` - Generate summary
- `POST /api/chat` - Chat with video content
- `GET /api/videos` - List processed videos

## Project Structure

```
summarizer/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── api/                 # API routes
│   ├── services/            # Business logic
│   ├── models/              # Data models
│   └── utils/               # Utilities
├── frontend/                # React application
├── data/                    # Processed data storage
└── requirements.txt         # Python dependencies
```

## Development

### Backend Development
- Run tests: `pytest`
- Format code: `black .`
- Lint code: `flake8`

### Frontend Development
- Install dependencies: `npm install`
- Start dev server: `npm start`
- Build for production: `npm run build`

## Virtual Environment Management

### Activating the Virtual Environment
Always activate the virtual environment before working on the project:

**On Windows:**
```bash
venv\Scripts\activate
```

**On macOS/Linux:**
```bash
source venv/bin/activate
```

### Creating a New Virtual Environment
If you need to recreate the virtual environment:

**On Windows:**
```bash
python3.11 -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

**On macOS/Linux:**
```bash
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Deactivating the Virtual Environment
When you're done working on the project:

```bash
deactivate
```

### Updating Dependencies
To update dependencies in the virtual environment:

```bash
# Activate virtual environment first
pip install --upgrade -r requirements.txt
```

### Troubleshooting
- If you see `(venv)` at the beginning of your command prompt, the virtual environment is active
- If you get import errors, make sure the virtual environment is activated
- To recreate the virtual environment: delete the `venv` folder and follow the installation steps again
- If you have multiple Python versions installed, make sure to use `python3.11` specifically
- Check your Python version with `python --version` or `python3.11 --version`
- If you encounter dependency conflicts, run `python test_dependencies.py` to diagnose issues

## Python Version Management

This project is designed to work with **Python 3.11**. Here's how to manage Python versions:

### Using pyenv (Recommended)
```bash
# Install pyenv
# macOS: brew install pyenv
# Linux: curl https://pyenv.run | bash

# Install Python 3.11
pyenv install 3.11.9

# Set local version for this project
pyenv local 3.11.9

# Create virtual environment
python -m venv venv
```

### Using conda
```bash
# Create environment with Python 3.11
conda create -n youtube-summarizer python=3.11

# Activate environment
conda activate youtube-summarizer

# Install dependencies
pip install -r requirements.txt
```

## License

MIT License - see LICENSE file for details.
