# MenuMatch AI Reel Agent

An AI agent that reads `project_proposal.md` and produces a short narrated
video reel pitching the project, with slide planning, critique-and-revision,
narration, and video assembly all handled automatically.

## Requirements

- Python 3.10 or later
- ffmpeg and ffprobe installed and available on your PATH
  (on macOS: `brew install ffmpeg`)

## Setup

    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    playwright install chromium

Create a `.env` file in this folder with the following line, replacing the
placeholder with your real OpenAI API key:

    OPENAI_API_KEY=your-key-here

## Run

    python reel_agent.py

This generates:
- `ai_grading/slide_plan.json` — the planned slides
- `ai_grading/critique_feedback.json` — critique and revision history per slide
- `slides/` — the HTML source for each slide
- `audio/` — narration audio per slide
- `reel.mp4` — the final assembled video
