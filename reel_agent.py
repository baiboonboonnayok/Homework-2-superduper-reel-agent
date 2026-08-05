import asyncio
import json
import os
import re
from pathlib import Path
from typing import List
from pydantic import BaseModel, Field
from dotenv import load_dotenv

env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

api_key = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_KEY")
if not api_key:
    raise ValueError("❌ Could not find OPENAI_API_KEY in your .env file!")

from openai import AsyncOpenAI
from pydantic_ai import Agent

openai_client = AsyncOpenAI(api_key=api_key)

os.makedirs("slides", exist_ok=True)
os.makedirs("audio", exist_ok=True)
os.makedirs("ai_grading", exist_ok=True)
os.makedirs("video_clips", exist_ok=True)

class SlideItem(BaseModel):
    slide_number: int
    title: str
    description: str
    narration: str

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

planner_agent = Agent(
    'openai:gpt-5.6-luna',
    output_type=SlidePlan,
    system_prompt=(
        "You are an expert luxury video producer. "
        "Produce a 4 to 5 slide plan for a video reel focusing on Bangkok Fine Dining Aspect-Based Sentiment Analysis (ABSA). "
        "Provide 3 clean, distinct bullet points for descriptions. Keep narrations under 25 words."
    )
)

critique_agent = Agent(
    'openai:gpt-5.6-luna',
    output_type=CritiqueReport,
    system_prompt=(
        "You are an art director. Critique each slide for elegance and clarity."
    )
)

def generate_html_slide(slide_num: int, title: str, description: str) -> str:
    raw_bullets = re.split(r'\\n|\n|<br>|\u2022|-', description)
    bullets = [b.strip() for b in raw_bullets if len(b.strip()) > 3]
    if len(bullets) < 2:
        bullets = ["15,000–30,000 Bangkok reviews", "30–50 fine dining destinations", "Intelligent guest insights"]

    if slide_num == 3:
        card_content = """
        <div class="metrics-container animate-in">
            <div class="metric-item"><span>Food Quality & Taste</span><span class="m-val">92%</span></div>
            <div class="metric-item"><span>Service & Hospitality</span><span class="m-val">78%</span></div>
            <div class="metric-item"><span>Ambience & Atmosphere</span><span class="m-val">88%</span></div>
            <div class="metric-item" style="border:none;"><span>Value Perception</span><span class="m-val">64%</span></div>
        </div>
        """
    else:
        bullets_html = "".join([f'<div class="bullet-row" style="animation-delay: {0.2 + (i*0.15)}s;"><div class="dot"></div><div>{b}</div></div>' for i, b in enumerate(bullets[:3])])
        card_content = f"""<div class="editorial-box animate-in">{bullets_html}</div>"""

    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,500;1,400&family=Plus+Jakarta+Sans:wght@300;400;500&display=swap" rel="stylesheet">
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            width: 1080px; height: 1920px;
            background: radial-gradient(circle at center, #141418 0%, #070709 100%);
            font-family: 'Plus Jakarta Sans', sans-serif;
            color: #ffffff; display: flex; flex-direction: column;
            justify-content: center; align-items: center; padding: 100px;
            overflow: hidden; position: relative;
        }}
        .kicker {{ color: #d4af37; font-size: 20px; font-weight: 500; letter-spacing: 8px; text-transform: uppercase; margin-bottom: 25px; opacity: 0; animation: fadeInDown 0.8s ease forwards 0.2s; }}
        .title {{ font-family: 'Playfair Display', serif; font-size: 72px; font-weight: 400; text-align: center; line-height: 1.2; margin-bottom: 60px; color: #fcfcfc; opacity: 0; animation: fadeInDown 0.8s ease forwards 0.4s; }}
        @keyframes fadeInDown {{ from {{ opacity: 0; transform: translateY(-20px); }} to {{ opacity: 1; transform: translateY(0); }} }}
        
        .editorial-box, .metrics-container {{
            width: 100%; background: rgba(255, 255, 255, 0.02);
            border: 1px solid rgba(212, 175, 55, 0.3); border-radius: 6px;
            padding: 60px 50px; box-shadow: 0 40px 80px rgba(0,0,0,0.8);
        }}
        .animate-in {{ opacity: 0; animation: slideUp 1s cubic-bezier(0.16, 1, 0.3, 1) 0.5s forwards; }}
        @keyframes slideUp {{ from {{ opacity: 0; transform: translateY(30px); }} to {{ opacity: 1; transform: translateY(0); }} }}
        
        .bullet-row {{ display: flex; align-items: center; margin-bottom: 35px; opacity: 0; animation: slideUp 0.8s ease forwards; font-size: 38px; font-weight: 300; color: #e2e8f0; }}
        .dot {{ width: 8px; height: 8px; background-color: #d4af37; border-radius: 50%; margin-right: 25px; box-shadow: 0 0 10px #d4af37; flex-shrink: 0; }}
        
        .metric-item {{ display: flex; justify-content: space-between; align-items: center; padding: 24px 0; border-bottom: 1px solid rgba(255, 255, 255, 0.08); font-size: 30px; font-weight: 300; color: #e5e7eb; }}
        .m-val {{ font-family: 'Playfair Display', serif; font-size: 36px; color: #d4af37; }}
    </style>
</head>
<body>
    <div class="kicker">Bangkok Fine Dining Intelligence</div>
    <h1 class="title">{title}</h1>
    {card_content}
</body>
</html>
"""

async def generate_tts(slide_num: int, text: str):
    audio_path = f"audio/slide_{slide_num}.mp3"
    response = await openai_client.audio.speech.create(model="tts-1-hd", voice="alloy", input=text)
    with open(audio_path, "wb") as f:
        f.write(response.content)
    return audio_path

async def process_single_slide(slide: SlideItem):
    html_content = generate_html_slide(slide.slide_number, slide.title, slide.description)
    html_path = f"slides/slide_{slide.slide_number}.html"
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    audio_path = await generate_tts(slide.slide_number, slide.narration)
    return slide.slide_number, html_path, audio_path

async def main():
    print("🚀 Starting Luxury Reel Agent...")
    with open("project_proposal.md", "r", encoding="utf-8") as f:
        proposal_text = f.read()

    plan_result = await planner_agent.run(f"Project Proposal:\n{proposal_text}")
    slide_plan = plan_result.output
    with open("ai_grading/slide_plan.json", "w", encoding="utf-8") as f:
        json.dump(slide_plan.model_dump(), f, indent=2)

    critique_result = await critique_agent.run(f"Review this slide plan:\n{slide_plan.model_dump_json()}")
    critique_data = critique_result.output
    with open("ai_grading/critique_feedback.json", "w", encoding="utf-8") as f:
        json.dump(critique_data.model_dump(), f, indent=2)

    revised_slides = [orig.model_copy(update={"narration": crit.revised_narration}) for orig, crit in zip(slide_plan.slides, critique_data.critiques)]
    tasks = [process_single_slide(slide) for slide in revised_slides]
    await asyncio.gather(*tasks)
    print("✅ Slides and audio generated successfully!")

if __name__ == "__main__":
    asyncio.run(main())