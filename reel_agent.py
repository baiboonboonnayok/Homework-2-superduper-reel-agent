import asyncio
import json
import os
import re
import subprocess
from pathlib import Path
from typing import List, Dict, Any
from pydantic import BaseModel, Field
from openai import AsyncOpenAI
from pydantic_ai import Agent

# Initialize Async OpenAI Client for TTS
openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Ensure required directories exist
os.makedirs("slides", exist_ok=True)
os.makedirs("audio", exist_ok=True)
os.makedirs("ai_grading", exist_ok=True)
os.makedirs("video_clips", exist_ok=True)

# -----------------------------------------------------------------------------
# PYDANTIC SCHEMAS
# -----------------------------------------------------------------------------
class SlideItem(BaseModel):
    slide_number: int
    title: str
    description: str = Field(description="Visual layout description text")
    narration: str = Field(description="Spoken text for TTS, max 15s (~25 words)")

class SlidePlan(BaseModel):
    slides: List[SlideItem]

class SlideCritique(BaseModel):
    slide_number: int
    original_narration: str
    critique_narration: str
    revised_narration: str
    original_visual: str
    critique_visual: str
    revised_visual_notes: str

class CritiqueReport(BaseModel):
    critiques: List[SlideCritique]

# -----------------------------------------------------------------------------
# PYDANTIC AI AGENT SETUP
# -----------------------------------------------------------------------------
planner_agent = Agent(
    model='openai:gpt-5.6-luna',
    result_type=SlidePlan,
    system_prompt=(
        "You are an expert video reel producer for business AI solutions. "
        "Read the project proposal and produce a 4 to 5 slide plan for a 30-40 second video reel. "
        "Keep each narration concise (under 25 words) so spoken TTS takes ~8 seconds per slide."
    )
)

critique_agent = Agent(
    model='openai:gpt-5.6-luna',
    result_type=CritiqueReport,
    system_prompt=(
        "You are a rigorous video editor. Critique each slide's visual design and narration for punchiness, "
        "clarity, and engagement. Provide revised narration and slide visual recommendations."
    )
)

# -----------------------------------------------------------------------------
# HTML TEMPLATE GENERATOR WITH CSS/SVG ANIMATIONS
# -----------------------------------------------------------------------------
def generate_html_slide(slide_num: int, title: str, description: str) -> str:
    """Generates modern vertical 9:16 HTML slides with CSS/SVG animations."""
    
    # Custom animated SVG visual for Slide 3 (Radar / Metric Visual Requirement)
    custom_visual_code = ""
    if slide_num == 3:
        custom_visual_code = """
        <div class="visual-container">
            <svg viewBox="0 0 300 200" class="svg-chart">
                <!-- Grid background -->
                <line x1="40" y1="160" x2="280" y2="160" stroke="#334155" stroke-width="2"/>
                <line x1="40" y1="20" x2="40" y2="160" stroke="#334155" stroke-width="2"/>
                
                <!-- Animated Bars -->
                <rect x="60" y="160" width="35" height="0" fill="#38bdf8" rx="4">
                    <animate attributeName="height" from="0" to="120" dur="1s" fill="freeze" />
                    <animate attributeName="y" from="160" to="40" dur="1s" fill="freeze" />
                </rect>
                <text x="77" y="32" fill="#38bdf8" font-size="12" text-anchor="middle" font-weight="bold">92%</text>
                <text x="77" y="180" fill="#94a3b8" font-size="10" text-anchor="middle">Food</text>

                <rect x="115" y="160" width="35" height="0" fill="#f43f5e" rx="4">
                    <animate attributeName="height" from="0" to="95" dur="1s" begin="0.2s" fill="freeze" />
                    <animate attributeName="y" from="160" to="65" dur="1s" begin="0.2s" fill="freeze" />
                </rect>
                <text x="132" y="57" fill="#f43f5e" font-size="12" text-anchor="middle" font-weight="bold">78%</text>
                <text x="132" y="180" fill="#94a3b8" font-size="10" text-anchor="middle">Service</text>

                <rect x="170" y="160" width="35" height="0" fill="#a855f7" rx="4">
                    <animate attributeName="height" from="0" to="110" dur="1s" begin="0.4s" fill="freeze" />
                    <animate attributeName="y" from="160" to="50" dur="1s" begin="0.4s" fill="freeze" />
                </rect>
                <text x="187" y="42" fill="#a855f7" font-size="12" text-anchor="middle" font-weight="bold">88%</text>
                <text x="187" y="180" fill="#94a3b8" font-size="10" text-anchor="middle">Vibe</text>

                <rect x="225" y="160" width="35" height="0" fill="#10b981" rx="4">
                    <animate attributeName="height" from="0" to="70" dur="1s" begin="0.6s" fill="freeze" />
                    <animate attributeName="y" from="160" to="90" dur="1s" begin="0.6s" fill="freeze" />
                </rect>
                <text x="242" y="82" fill="#10b981" font-size="12" text-anchor="middle" font-weight="bold">64%</text>
                <text x="242" y="180" fill="#94a3b8" font-size="10" text-anchor="middle">Value</text>
            </svg>
        </div>
        """
    else:
        custom_visual_code = f"""
        <div class="card pulse-glow">
            <p class="desc-text">{description}</p>
        </div>
        """

    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            width: 1080px;
            height: 1920px;
            background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%);
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            color: #ffffff;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            padding: 80px;
            overflow: hidden;
        }}
        .badge {{
            background: linear-gradient(90deg, #ec4899, #8b5cf6);
            padding: 16px 36px;
            border-radius: 50px;
            font-size: 28px;
            font-weight: 700;
            letter-spacing: 2px;
            text-transform: uppercase;
            margin-bottom: 40px;
            box-shadow: 0 10px 25px rgba(236, 72, 153, 0.3);
        }}
        .title {{
            font-size: 64px;
            font-weight: 800;
            text-align: center;
            line-height: 1.2;
            margin-bottom: 60px;
            background: linear-gradient(180deg, #ffffff 0%, #cbd5e1 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .card {{
            width: 100%;
            background: rgba(255, 255, 255, 0.05);
            border: 2px solid rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(20px);
            border-radius: 32px;
            padding: 60px;
            box-shadow: 0 20px 50px rgba(0,0,0,0.5);
        }}
        .desc-text {{
            font-size: 38px;
            line-height: 1.5;
            color: #e2e8f0;
            text-align: center;
        }}
        .visual-container {{
            width: 100%;
            background: rgba(15, 23, 42, 0.8);
            border: 2px solid #38bdf8;
            border-radius: 32px;
            padding: 40px;
            box-shadow: 0 0 30px rgba(56, 189, 248, 0.2);
        }}
        .svg-chart {{
            width: 100%;
            height: auto;
        }}
    </style>
</head>
<body>
    <div class="badge">Bangkok AI Analytics</div>
    <h1 class="title">{title}</h1>
    {custom_visual_code}
</body>
</html>
"""
    return html_content

# -----------------------------------------------------------------------------
# PARALLEL WORKERS (TTS + SLIDE RENDERING)
# -----------------------------------------------------------------------------
async def generate_tts(slide_num: int, text: str):
    """Generates audio with tts-1-hd."""
    audio_path = f"audio/slide_{slide_num}.mp3"
    response = await openai_client.audio.speech.create(
        model="tts-1-hd",
        voice="alloy",
        input=text
    )
    response.stream_to_file(audio_path)
    return audio_path

async def process_single_slide(slide: SlideItem):
    """Processes a single slide's HTML and Audio in parallel."""
    # Write HTML file
    html_content = generate_html_slide(slide.slide_number, slide.title, slide.description)
    html_path = f"slides/slide_{slide.slide_number}.html"
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    # Generate Audio
    audio_path = await generate_tts(slide.slide_number, slide.narration)
    return slide.slide_number, html_path, audio_path

# -----------------------------------------------------------------------------
# MAIN AGENT PIPELINE
# -----------------------------------------------------------------------------
async def main():
    print("🚀 Starting Bangkok Fine Dining Video Reel Agent...")

    # Read proposal
    with open("project_proposal.md", "r", encoding="utf-8") as f:
        proposal_text = f.read()

    # 1. Generate Initial Slide Plan
    print("📋 Generating Slide Plan via PydanticAI (gpt-5.6-luna)...")
    plan_result = await planner_agent.run(f"Project Proposal:\n{proposal_text}")
    slide_plan = plan_result.data

    # Save initial plan to ai_grading/
    with open("ai_grading/slide_plan.json", "w", encoding="utf-8") as f:
        json.dump(slide_plan.model_dump(), f, indent=2)

    # 2. Perform Critique & Feedback Improvement
    print("🔍 Running Self-Critique & Enhancement Step...")
    critique_result = await critique_agent.run(f"Review this slide plan:\n{slide_plan.model_dump_json()}")
    critique_data = critique_result.data

    with open("ai_grading/critique_feedback.json", "w", encoding="utf-8") as f:
        json.dump(critique_data.model_dump(), f, indent=2)

    # Apply revised narrations from critique
    revised_slides = []
    for orig, crit in zip(slide_plan.slides, critique_data.critiques):
        orig.narration = crit.revised_narration
        revised_slides.append(orig)

    # 3. Parallel Execution for Slides HTML & TTS Audio
    print("⚡ Executing Slide Generation & TTS Synthesis in Parallel...")
    tasks = [process_single_slide(slide) for slide in revised_slides]
    results = await asyncio.gather(*tasks)

    print("✅ All slides and audio generated successfully!")
    print("📁 Saved outputs into slides/, audio/, and ai_grading/")

if __name__ == "__main__":
    asyncio.run(main())