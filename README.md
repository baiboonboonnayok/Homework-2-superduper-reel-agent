# Fine Dining Reel Agent

An AI agent that reads `project_proposal.md` and produces a short narrated
video reel pitching the project, with slide planning, critique-and-revision,
narration, and video assembly all handled automatically.

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

Create a `.env` file in this folder with:
## Run

```bash
python reel_agent.py
```

This generates:
- `ai_grading/slide_plan.json` — the planned slides
- `ai_grading/critique_feedback.json` — critique and revision history per slide
- `slides/` — the HTML source for each slide
- `audio/` — narration audio per slide
- `reel.mp4` — the final assembled video
