import os
import json
import subprocess
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv
from pydantic import BaseModel
from pydantic_ai import Agent
from openai import OpenAI
from playwright.sync_api import sync_playwright

load_dotenv()
tts_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class Slide(BaseModel):
    slide_number: int
    headline: str       # short on-screen text, 3-8 words, the ACTUAL words shown on the slide
    description: str    # creative brief: what's on screen and visuals (for grading docs)
    narration: str


class SlidePlan(BaseModel):
    slides: list[Slide]


class Critique(BaseModel):
    strengths: str
    weaknesses: str
    suggestions: str


class RevisedSlide(BaseModel):
    headline: str
    description: str
    narration: str


agent = Agent(
    "openai:gpt-5.6-luna",
    output_type=SlidePlan,
    system_prompt=(
        "You are a video reel planner. Given a project proposal, create a plan "
        "for 4 to 6 slides that pitch the project. For each slide, provide: "
        "(1) a headline, which is the SHORT actual on-screen text, 3 to 8 words "
        "maximum, punchy and readable in one glance, written as real copy a "
        "viewer would read, never a camera direction or shot description; "
        "(2) a description, a creative brief of what's on screen and visuals, "
        "for internal planning notes; (3) narration text to be spoken aloud, "
        "short enough to read in about 15 seconds or less."
    ),
)

critique_agent = Agent(
    "openai:gpt-5.6-luna",
    output_type=Critique,
    system_prompt=(
        "You are a critical creative director reviewing one slide from a short "
        "promotional video reel. Given the slide's headline, description, and "
        "narration, identify what's strong, what's weak or confusing, and give "
        "specific suggestions. Be especially critical if the headline is too "
        "long, generic, or reads like a shot description instead of punchy "
        "on-screen copy."
    ),
)

revision_agent = Agent(
    "openai:gpt-5.6-luna",
    output_type=RevisedSlide,
    system_prompt=(
        "You revise a video reel slide based on critique feedback. Given the "
        "original headline, description, and narration, plus the critique and "
        "suggestions, produce an improved version. The headline MUST be short "
        "on-screen text, 3 to 8 words maximum, punchy, never a shot description. "
        "Keep the narration short enough to read aloud in about 15 seconds or less."
    ),
)


def render_slide_html(headline, tag_text="SUPERDUPER · MEN'S APPAREL OEM"):
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
  body {{
    margin: 0;
    width: 1080px;
    height: 1920px;
    background: linear-gradient(180deg, #101820 0%, #1a2531 100%);
    color: #ffffff;
    font-family: 'Helvetica Neue', Arial, sans-serif;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    text-align: center;
    padding: 100px;
    box-sizing: border-box;
  }}
  .tag {{
    letter-spacing: 4px;
    font-size: 24px;
    color: #f4c95d;
    font-weight: 600;
    margin-bottom: 60px;
    text-transform: uppercase;
  }}
  h1 {{
    font-size: 88px;
    line-height: 1.15;
    font-weight: 800;
    color: #ffffff;
    margin: 0;
  }}
  .accent-line {{
    width: 120px;
    height: 6px;
    background: #f4c95d;
    margin-top: 60px;
    border-radius: 3px;
  }}
</style>
</head>
<body>
  <div class="tag">{tag_text}</div>
  <h1>{headline}</h1>
  <div class="accent-line"></div>
</body>
</html>
"""


def render_visual_slide(headline):
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
  body {{
    margin: 0;
    width: 1080px;
    height: 1920px;
    background: linear-gradient(180deg, #101820 0%, #1a2531 100%);
    color: #ffffff;
    font-family: 'Helvetica Neue', Arial, sans-serif;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    padding: 80px;
    box-sizing: border-box;
  }}
  h1 {{
    font-size: 58px;
    color: #f4c95d;
    margin-bottom: 90px;
    text-align: center;
    font-weight: 800;
  }}
  .steps {{
    display: flex;
    flex-direction: column;
    gap: 55px;
    width: 100%;
  }}
  .step {{
    display: flex;
    align-items: center;
    gap: 30px;
  }}
  .step-number {{
    width: 90px;
    height: 90px;
    border-radius: 50%;
    background: #f4c95d;
    color: #101820;
    font-size: 40px;
    font-weight: bold;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }}
  .step-box {{
    background: #1c2733;
    border: 2px solid #f4c95d;
    border-radius: 16px;
    padding: 30px 40px;
    font-size: 34px;
    font-weight: 600;
    flex-grow: 1;
  }}
  .arrow {{
    font-size: 50px;
    color: #f4c95d;
    text-align: center;
  }}
</style>
</head>
<body>
  <h1>{headline}</h1>
  <div class="steps">
    <div class="step">
      <div class="step-number">1</div>
      <div class="step-box">Share your design idea</div>
    </div>
    <div class="arrow">&#8595;</div>
    <div class="step">
      <div class="step-number">2</div>
      <div class="step-box">We produce it in Bangkok</div>
    </div>
    <div class="arrow">&#8595;</div>
    <div class="step">
      <div class="step-number">3</div>
      <div class="step-box">You launch your collection</div>
    </div>
  </div>
</body>
</html>
"""


def process_slide(slide):
    original_text = (
        f"Headline: {slide.headline}\n"
        f"Description: {slide.description}\n"
        f"Narration: {slide.narration}"
    )
    critique_result = critique_agent.run_sync(original_text)
    critique = critique_result.output

    revision_input = (
        f"Original headline: {slide.headline}\n"
        f"Original description: {slide.description}\n"
        f"Original narration: {slide.narration}\n"
        f"Strengths: {critique.strengths}\n"
        f"Weaknesses: {critique.weaknesses}\n"
        f"Suggestions: {critique.suggestions}"
    )
    revision_result = revision_agent.run_sync(revision_input)
    revised = revision_result.output

    if slide.slide_number == 3:
        html_content = render_visual_slide(revised.headline)
    else:
        html_content = render_slide_html(revised.headline)
    with open(f"slides/slide_{slide.slide_number}.html", "w") as f:
        f.write(html_content)

    audio_path = f"audio/slide_{slide.slide_number}.mp3"
    with tts_client.audio.speech.with_streaming_response.create(
        model="tts-1-hd",
        voice="alloy",
        input=revised.narration,
    ) as response:
        response.stream_to_file(audio_path)

    return {
        "slide_number": slide.slide_number,
        "original_headline": slide.headline,
        "original_description": slide.description,
        "original_narration": slide.narration,
        "critique": critique.model_dump(),
        "revised_headline": revised.headline,
        "revised_description": revised.description,
        "revised_narration": revised.narration,
    }


# Step 1: read the proposal and plan the slides
with open("project_proposal.md", "r") as f:
    proposal_text = f.read()

result = agent.run_sync(proposal_text)

for slide in result.output.slides:
    print(f"Slide {slide.slide_number}")
    print(f"  Headline: {slide.headline}")
    print(f"  On screen: {slide.description}")
    print(f"  Narration: {slide.narration}")
    print()

os.makedirs("ai_grading", exist_ok=True)
with open("ai_grading/slide_plan.json", "w") as f:
    json.dump(result.output.model_dump(), f, indent=2)

print("Saved to ai_grading/slide_plan.json")

# Step 2: critique, revise, and build HTML + audio for every slide IN PARALLEL
os.makedirs("slides", exist_ok=True)
os.makedirs("audio", exist_ok=True)

with ThreadPoolExecutor(max_workers=5) as executor:
    critique_records = list(executor.map(process_slide, result.output.slides))

critique_records.sort(key=lambda r: r["slide_number"])

with open("ai_grading/critique_feedback.json", "w") as f:
    json.dump(critique_records, f, indent=2)

print("Saved critique and feedback to ai_grading/critique_feedback.json")
print("Saved HTML slides to slides/")
print("Saved narration audio to audio/")

# Step 3: screenshot each HTML slide, then combine with audio into a video

def get_audio_duration(path):
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", path],
        capture_output=True, text=True
    )
    return float(result.stdout.strip())


os.makedirs("video_clips", exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1080, "height": 1920})

    for record in critique_records:
        n = record["slide_number"]
        html_path = os.path.abspath(f"slides/slide_{n}.html")
        image_path = f"slides/slide_{n}.png"
        page.goto(f"file://{html_path}")
        page.screenshot(path=image_path)

    browser.close()

for record in critique_records:
    n = record["slide_number"]
    image_path = f"slides/slide_{n}.png"
    audio_path = f"audio/slide_{n}.mp3"
    clip_path = f"video_clips/clip_{n}.mp4"
    duration = get_audio_duration(audio_path)

    subprocess.run([
        "ffmpeg", "-y",
        "-loop", "1", "-i", image_path,
        "-i", audio_path,
        "-c:v", "libx264", "-tune", "stillimage",
        "-c:a", "aac", "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-t", str(duration),
        clip_path
    ], check=True)

with open("video_clips/concat_list.txt", "w") as f:
    for record in sorted(critique_records, key=lambda r: r["slide_number"]):
        n = record["slide_number"]
        f.write(f"file 'clip_{n}.mp4'\n")

subprocess.run([
    "ffmpeg", "-y",
    "-f", "concat", "-safe", "0",
    "-i", "video_clips/concat_list.txt",
    "-c", "copy",
    "reel.mp4"
], check=True)

print("Saved final video to reel.mp4")