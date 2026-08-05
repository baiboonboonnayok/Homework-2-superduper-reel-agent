import asyncio
import json
import os
import subprocess
from pathlib import Path
from typing import List
from pydantic import BaseModel
from pydantic_ai import Agent
from openai import AsyncOpenAI
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

api_key = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_KEY")
if not api_key:
    raise ValueError("Could not find OPENAI_API_KEY in your .env file!")

openai_client = AsyncOpenAI(api_key=api_key)

FADE_SECONDS = 0.25
GAP_SECONDS = 0.2  # true silence + held frame added after each slide, before the cut

KICKER = "Bangkok Fine Dining Intelligence"

FONT_LINKS = (
    '<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:'
    'ital,wght@0,400;0,500;1,400&family=Plus+Jakarta+Sans:wght@300;400;500'
    '&display=swap" rel="stylesheet">'
)

BASE_STYLE = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  width: 1080px; height: 1920px;
  background: radial-gradient(circle at center, #141418 0%, #070709 100%);
  font-family: 'Plus Jakarta Sans', sans-serif;
  color: #ffffff; display: flex; flex-direction: column;
  justify-content: center; align-items: center; padding: 100px;
  overflow: hidden; position: relative;
}
.kicker { color: #d4af37; font-size: 20px; font-weight: 500; letter-spacing: 8px; text-transform: uppercase; margin-bottom: 25px; opacity: 0; animation: fadeInDown 0.8s ease forwards 0.2s; }
.title { font-family: 'Playfair Display', serif; font-size: 72px; font-weight: 400; text-align: center; line-height: 1.2; margin-bottom: 60px; color: #fcfcfc; opacity: 0; animation: fadeInDown 0.8s ease forwards 0.4s; }
@keyframes fadeInDown { from { opacity: 0; transform: translateY(-20px); } to { opacity: 1; transform: translateY(0); } }
@keyframes slideUp { from { opacity: 0; transform: translateY(30px); } to { opacity: 1; transform: translateY(0); } }
"""


class Slide(BaseModel):
    slide_number: int
    headline: str
    description: str     # what's on screen: text AND visual treatment, for grading notes (not rendered directly)
    bullets: List[str]   # 2-3 clean on-screen phrases, generated directly (never regex-split from prose)
    narration: str


class SlidePlan(BaseModel):
    slides: List[Slide]


class Critique(BaseModel):
    strengths: str
    weaknesses: str
    suggestions: str


class RevisedSlide(BaseModel):
    headline: str
    description: str
    bullets: List[str]
    narration: str


class PipelineSteps(BaseModel):
    steps: List[str]  # exactly 4 short pipeline stage names, in order


class ScorecardItem(BaseModel):
    label: str
    value: str


class Scorecard(BaseModel):
    items: List[ScorecardItem]  # exactly 4 items, grounded in real proposal numbers


planner_agent = Agent(
    "openai:gpt-5.6-luna",
    output_type=SlidePlan,
    system_prompt=(
        "You are an expert luxury video producer. Given a project proposal, "
        "produce a plan for 4 to 6 slides that pitch the project. For each "
        "slide, provide: (1) a headline, short punchy on-screen text a "
        "viewer would read, 3 to 8 words, never a shot description; (2) a "
        "description of what is on screen for this slide, covering both the "
        "on-screen text and the visual treatment, for example 'numbered "
        "pipeline diagram with four stages' or 'two contrasting stat cards', "
        "for internal grading notes only, this is not shown on screen "
        "itself; (3) 2 to 3 clean bullet phrases, each a complete short "
        "phrase under 12 words, plain text with no markdown, no bullet "
        "characters, and no trailing hyphens or dashes; (4) narration text "
        "to be spoken aloud, readable in about 10 seconds or less."
    ),
)

critique_agent = Agent(
    "openai:gpt-5.6-luna",
    output_type=Critique,
    system_prompt=(
        "You are an art director critiquing one slide from a luxury "
        "promotional video reel. Given its headline, description, bullets, "
        "and narration, identify what's strong, what's weak, and give "
        "specific suggestions. Be critical of generic phrasing or a "
        "headline that reads like a shot description instead of on-screen "
        "copy."
    ),
)

revision_agent = Agent(
    "openai:gpt-5.6-luna",
    output_type=RevisedSlide,
    system_prompt=(
        "You revise a luxury video reel slide based on critique feedback. "
        "Produce an improved headline (3 to 8 words), an updated "
        "description of what is on screen (text and visual treatment, for "
        "internal grading notes, not shown on screen itself), 2 to 3 clean "
        "bullet phrases (plain text, no markdown, no bullet characters, no "
        "trailing hyphens), and narration readable in about 10 seconds or "
        "less."
    ),
)

pipeline_agent = Agent(
    "openai:gpt-5.6-luna",
    output_type=PipelineSteps,
    system_prompt=(
        "Given a project proposal, produce exactly 4 short pipeline stage "
        "names (each under 4 words, for example 'Data Cleaning' or 'Aspect "
        "Sentiment Analysis') describing the project's actual technical "
        "steps in order, for a numbered flow diagram."
    ),
)

scorecard_agent = Agent(
    "openai:gpt-5.6-luna",
    output_type=Scorecard,
    system_prompt=(
        "Given a project proposal, produce exactly 4 short scope stat "
        "callouts describing the project's real planned scale, grounded "
        "strictly in actual numbers stated in the proposal itself, such as "
        "dataset size, number of restaurants, number of categories, or "
        "number of output types. Each needs a short label (2 to 4 words) "
        "and a short value (a number, range, or count, such as '30-50', "
        "'15K-30K', or '13'). Never invent outcome or performance numbers "
        "that haven't actually happened."
    ),
)


def get_slide_type(slide_number, total_slides):
    if slide_number == 1:
        return "hero"
    if slide_number == total_slides:
        return "cta"
    if slide_number == 3:
        return "pipeline"
    if slide_number == 4:
        return "scorecard"
    return "bullets"


def render_hero_slide(headline, kicker_text):
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
{FONT_LINKS}
<style>
{BASE_STYLE}
.accent-line {{ width: 120px; height: 2px; background: #d4af37; margin-top: 50px; opacity: 0; animation: slideUp 1s ease forwards 0.6s; }}
</style>
</head>
<body>
  <div class="kicker">{kicker_text}</div>
  <h1 class="title">{headline}</h1>
  <div class="accent-line"></div>
</body>
</html>
"""


def render_bullet_slide(headline, bullets):
    bullet_rows = "".join(
        f'<div class="bullet-row" style="animation-delay: {0.6 + (i * 0.15)}s;">'
        f'<div class="dot"></div><div>{b}</div></div>'
        for i, b in enumerate(bullets[:3])
    )
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
{FONT_LINKS}
<style>
{BASE_STYLE}
.editorial-box {{
  width: 100%; background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(212, 175, 55, 0.3); border-radius: 6px;
  padding: 60px 50px; box-shadow: 0 40px 80px rgba(0,0,0,0.8);
}}
.bullet-row {{ display: flex; align-items: center; margin-bottom: 35px; opacity: 0; animation: slideUp 0.8s ease forwards; font-size: 38px; font-weight: 300; color: #e2e8f0; }}
.bullet-row:last-child {{ margin-bottom: 0; }}
.dot {{ width: 8px; height: 8px; background-color: #d4af37; border-radius: 50%; margin-right: 25px; box-shadow: 0 0 10px #d4af37; flex-shrink: 0; }}
</style>
</head>
<body>
  <div class="kicker">{KICKER}</div>
  <h1 class="title">{headline}</h1>
  <div class="editorial-box">{bullet_rows}</div>
</body>
</html>
"""


def render_pipeline_slide(headline, steps):
    step_html = ""
    for i, step_text in enumerate(steps, start=1):
        step_html += f'''
    <div class="flow-step" style="animation-delay: {0.6 + (i * 0.15)}s;">
      <div class="flow-number">{i}</div>
      <div class="flow-label">{step_text}</div>
    </div>'''
        if i < len(steps):
            step_html += '<div class="flow-arrow">&#8595;</div>'
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
{FONT_LINKS}
<style>
{BASE_STYLE}
.flow {{ width: 100%; display: flex; flex-direction: column; align-items: center; gap: 8px; }}
.flow-step {{ width: 100%; display: flex; align-items: center; gap: 26px; opacity: 0; animation: slideUp 0.8s ease forwards; }}
.flow-number {{
  width: 70px; height: 70px; border-radius: 50%;
  border: 2px solid #d4af37; color: #d4af37;
  font-family: 'Playfair Display', serif; font-size: 30px;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}}
.flow-label {{
  flex-grow: 1; background: rgba(255,255,255,0.03);
  border: 1px solid rgba(212,175,55,0.25); border-radius: 6px;
  padding: 24px 32px; font-size: 30px; font-weight: 300; color: #e5e7eb;
}}
.flow-arrow {{ color: #d4af37; font-size: 34px; }}
</style>
</head>
<body>
  <div class="kicker">{KICKER}</div>
  <h1 class="title">{headline}</h1>
  <div class="flow">{step_html}
  </div>
</body>
</html>
"""


def render_scorecard_slide(headline, items):
    row_html = "".join(
        f'<div class="metric-item" style="animation-delay: {0.6 + (i * 0.15)}s;">'
        f'<span>{item.label}</span><span class="m-val">{item.value}</span></div>'
        for i, item in enumerate(items[:4])
    )
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
{FONT_LINKS}
<style>
{BASE_STYLE}
.metrics-container {{
  width: 100%; background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(212, 175, 55, 0.3); border-radius: 6px;
  padding: 60px 50px; box-shadow: 0 40px 80px rgba(0,0,0,0.8);
}}
.metric-item {{ display: flex; justify-content: space-between; align-items: center; padding: 24px 0; border-bottom: 1px solid rgba(255,255,255,0.08); font-size: 30px; font-weight: 300; color: #e5e7eb; opacity: 0; animation: slideUp 0.8s ease forwards; }}
.metric-item:last-child {{ border-bottom: none; }}
.m-val {{ font-family: 'Playfair Display', serif; font-size: 36px; color: #d4af37; }}
</style>
</head>
<body>
  <div class="kicker">{KICKER}</div>
  <h1 class="title">{headline}</h1>
  <div class="metrics-container">{row_html}</div>
</body>
</html>
"""


async def process_slide(slide, total_slides, pipeline_steps, scorecard_items):
    original_text = (
        f"Headline: {slide.headline}\n"
        f"Description: {slide.description}\n"
        f"Bullets: {slide.bullets}\n"
        f"Narration: {slide.narration}"
    )
    critique_result = await critique_agent.run(original_text)
    critique = critique_result.output

    revision_input = (
        f"Original headline: {slide.headline}\n"
        f"Original description: {slide.description}\n"
        f"Original bullets: {slide.bullets}\n"
        f"Original narration: {slide.narration}\n"
        f"Strengths: {critique.strengths}\n"
        f"Weaknesses: {critique.weaknesses}\n"
        f"Suggestions: {critique.suggestions}"
    )
    revision_result = await revision_agent.run(revision_input)
    revised = revision_result.output

    slide_type = get_slide_type(slide.slide_number, total_slides)

    if slide_type == "hero":
        html_content = render_hero_slide(revised.headline, KICKER)
    elif slide_type == "cta":
        html_content = render_hero_slide(revised.headline, "Let's Build The Scorecard")
    elif slide_type == "pipeline":
        html_content = render_pipeline_slide(revised.headline, pipeline_steps)
    elif slide_type == "scorecard":
        html_content = render_scorecard_slide(revised.headline, scorecard_items)
    else:
        html_content = render_bullet_slide(revised.headline, revised.bullets)

    with open(f"slides/slide_{slide.slide_number}.html", "w", encoding="utf-8") as f:
        f.write(html_content)

    audio_path = f"audio/slide_{slide.slide_number}.mp3"
    response = await openai_client.audio.speech.create(
        model="tts-1-hd", voice="alloy", input=revised.narration
    )
    with open(audio_path, "wb") as f:
        f.write(response.content)

    return {
        "slide_number": slide.slide_number,
        "slide_type": slide_type,
        "original_headline": slide.headline,
        "original_description": slide.description,
        "original_bullets": slide.bullets,
        "original_narration": slide.narration,
        "critique": critique.model_dump(),
        "revised_headline": revised.headline,
        "revised_description": revised.description,
        "revised_bullets": revised.bullets,
        "revised_narration": revised.narration,
    }


async def generate_slides_and_audio():
    print("Starting Luxury Reel Agent...")
    with open("project_proposal.md", "r", encoding="utf-8") as f:
        proposal_text = f.read()

    plan_result = await planner_agent.run(f"Project Proposal:\n{proposal_text}")
    slide_plan = plan_result.output

    os.makedirs("ai_grading", exist_ok=True)
    with open("ai_grading/slide_plan.json", "w", encoding="utf-8") as f:
        json.dump(slide_plan.model_dump(), f, indent=2)
    print("Saved to ai_grading/slide_plan.json")

    pipeline_result = await pipeline_agent.run(f"Project Proposal:\n{proposal_text}")
    pipeline_steps = pipeline_result.output.steps

    scorecard_result = await scorecard_agent.run(f"Project Proposal:\n{proposal_text}")
    scorecard_items = scorecard_result.output.items

    os.makedirs("slides", exist_ok=True)
    os.makedirs("audio", exist_ok=True)

    total_slides = len(slide_plan.slides)
    tasks = [
        process_slide(slide, total_slides, pipeline_steps, scorecard_items)
        for slide in slide_plan.slides
    ]
    critique_records = await asyncio.gather(*tasks)
    critique_records = sorted(critique_records, key=lambda r: r["slide_number"])

    with open("ai_grading/critique_feedback.json", "w", encoding="utf-8") as f:
        json.dump(critique_records, f, indent=2)
    print("Saved critique and feedback to ai_grading/critique_feedback.json")
    print("Saved HTML slides to slides/ and narration audio to audio/")

    return critique_records


def get_audio_duration(path):
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", path],
        capture_output=True, text=True
    )
    return float(result.stdout.strip())


def build_video(slide_numbers):
    print("Recording animated slides...")
    os.makedirs("video_clips", exist_ok=True)
    os.makedirs("video_clips/raw_webm", exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch()

        for n in slide_numbers:
            html_path = os.path.abspath(f"slides/slide_{n}.html")
            audio_path = f"audio/slide_{n}.mp3"
            dur = get_audio_duration(audio_path)

            context = browser.new_context(
                viewport={"width": 1080, "height": 1920},
                record_video_dir="video_clips/raw_webm",
                record_video_size={"width": 1080, "height": 1920},
            )
            page = context.new_page()
            page.goto(f"file://{html_path}")
            page.wait_for_timeout(int(dur * 1000))
            video = page.video
            context.close()

            video.save_as(f"video_clips/raw_webm/slide_{n}.webm")

        browser.close()

    print("Building synchronized MP4 clips with fades and a silent pause...")
    for n in slide_numbers:
        webm_path = f"video_clips/raw_webm/slide_{n}.webm"
        audio_path = f"audio/slide_{n}.mp3"
        clip_path = f"video_clips/clip_{n}.mp4"

        narration_duration = get_audio_duration(audio_path)
        fade_out_start = max(narration_duration - FADE_SECONDS, 0)
        total_duration = narration_duration + GAP_SECONDS

        subprocess.run([
            "ffmpeg", "-y",
            "-i", webm_path,
            "-i", audio_path,
            "-vf", (
                f"fade=t=in:st=0:d={FADE_SECONDS},"
                f"fade=t=out:st={fade_out_start:.3f}:d={FADE_SECONDS},"
                f"tpad=stop_mode=clone:stop_duration={GAP_SECONDS}"
            ),
            "-af", (
                f"afade=t=in:st=0:d={FADE_SECONDS},"
                f"afade=t=out:st={fade_out_start:.3f}:d={FADE_SECONDS},"
                f"apad=pad_dur={GAP_SECONDS}"
            ),
            "-c:v", "libx264",
            "-c:a", "aac", "-b:a", "192k",
            "-pix_fmt", "yuv420p",
            "-t", str(total_duration),
            clip_path
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"   -> built clip_{n}.mp4 ({total_duration:.1f}s)")

    print("Stitching final reel.mp4...")
    with open("video_clips/concat_list.txt", "w") as f:
        for n in slide_numbers:
            clip_abspath = os.path.abspath(f"video_clips/clip_{n}.mp4")
            f.write(f"file '{clip_abspath}'\n")

    subprocess.run([
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", "video_clips/concat_list.txt",
        "-c", "copy",
        "reel.mp4"
    ], check=True)

    print("Saved final animated reel.mp4 with fades and a silent pause between slides")


if __name__ == "__main__":
    records = asyncio.run(generate_slides_and_audio())
    build_video([r["slide_number"] for r in records])
