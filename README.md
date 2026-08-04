# SuperDuper Reel Agent

An AI agent that reads a project proposal and turns it into a short, narrated vertical video reel introducing SuperDuper, a Bangkok-based wholesale OEM menswear manufacturer, to brands who don't know it exists yet.

## What it does

1. Reads project_proposal.md
2. Plans 4-6 slides (headline, description, narration) using gpt-5.6-luna
3. Critiques and revises every slide in parallel
4. Renders each slide as a real HTML/CSS visual (one slide is an illustrated step-diagram, not just text)
5. Generates narration audio for each slide using OpenAI TTS (tts-1-hd)
6. Screenshots each slide with Playwright and stitches everything into a final video (reel.mp4) using ffmpeg

## Setup

1. Install Python 3.11+ and create a virtual environment: python3 -m venv venv, then source venv/bin/activate
2. Install dependencies: pip install -r requirements.txt, then playwright install chromium
3. Install ffmpeg: brew install ffmpeg
4. Create a .env file in the project root with your OpenAI API key: OPENAI_API_KEY=your_key_here

## Running it

Run python3 reel_agent.py

This generates:
- ai_grading/slide_plan.json — the original slide plan
- ai_grading/critique_feedback.json — critique and revisions per slide
- ai_grading/agent_flow.svg — diagram of the agent pipeline
- slides/ — HTML slide files
- audio/ — narration audio clips
- reel.mp4 — the final video reel