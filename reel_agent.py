import os
import json
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv
from pydantic import BaseModel
from pydantic_ai import Agent
from openai import OpenAI

load_dotenv()
tts_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class Slide(BaseModel):
    slide_number: int
    description: str
    narration: str


class SlidePlan(BaseModel):
    slides: list[Slide]


class Critique(BaseModel):
    strengths: str
    weaknesses: str
    suggestions: str


class RevisedSlide(BaseModel):
    description: str
    narration: str


agent = Agent(
    "openai:gpt-5.6-luna",
    output_type=SlidePlan,
    system_prompt=(
        "You are a video reel planner. Given a project proposal, create a plan "
        "for 4 to 6 slides that pitch the project. Each slide needs a description "
        "of what's on screen (text and visuals) and narration text to be spoken "
        "aloud, kept short enough to read in about 15 seconds or less."
    ),
)

critique_agent = Agent(
    "openai:gpt-5.6-luna",
    output_type=Critique,
    system_prompt=(
        "You are a critical creative director reviewing one slide from a short "
        "promotional video reel. Given the slide's on-screen description and "
        "its narration, identify what's strong, what's weak or confusing, and "
        "give specific suggestions to improve both the visual and the narration."
    ),
)

revision_agent = Agent(
    "openai:gpt-5.6-luna",
    output_type=RevisedSlide,
    system_prompt=(
        "You revise a video reel slide based on critique feedback. Given the "
        "original description and narration, plus the critique and suggestions, "
        "produce an improved description and improved narration. Keep the "
        "narration short enough to read aloud in about 15 seconds or less."
    ),
)


def render_slide_html(description):
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
  body {{
    margin: 0;
    width: 1080px;
    height: 1920px;
    background: #101820;
    color: #ffffff;
    font-family: 'Helvetica Neue', Arial, sans-serif;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    text-align: center;
    padding: 80px;
    box-sizing: border-box;
  }}
  h1 {{
    font-size: 56px;
    color: #f4c95d;
    margin-bottom: 40px;
  }}
  p {{
    font-size: 32px;
    line-height: 1.5;
    max-width: 800px;
  }}
</style>
</head>
<body>
  <h1>SuperDuper</h1>
  <p>{description}</p>
</body>
</html>
"""


def render_visual_slide(description):
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
  body {{
    margin: 0;
    width: 1080px;
    height: 1920px;
    background: #101820;
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
    font-size: 52px;
    color: #f4c95d;
    margin-bottom: 100px;
    text-align: center;
  }}
  .steps {{
    display: flex;
    flex-direction: column;
    gap: 60px;
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
    font-size: 30px;
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
  <h1>How SuperDuper Works</h1>
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
    """Critique, revise, and produce final HTML + audio for one slide (runs in its own thread)."""
    original_text = f"Description: {slide.description}\nNarration: {slide.narration}"
    critique_result = critique_agent.run_sync(original_text)
    critique = critique_result.output

    revision_input = (
        f"Original description: {slide.description}\n"
        f"Original narration: {slide.narration}\n"
        f"Strengths: {critique.strengths}\n"
        f"Weaknesses: {critique.weaknesses}\n"
        f"Suggestions: {critique.suggestions}"
    )
    revision_result = revision_agent.run_sync(revision_input)
    revised = revision_result.output

    if slide.slide_number == 3:
        html_content = render_visual_slide(revised.description)
    else:
        html_content = render_slide_html(revised.description)
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
        "original_description": slide.description,
        "original_narration": slide.narration,
        "critique": critique.model_dump(),
        "revised_description": revised.description,
        "revised_narration": revised.narration,
    }


# Step 1: read the proposal and plan the slides
with open("project_proposal.md", "r") as f:
    proposal_text = f.read()

result = agent.run_sync(proposal_text)

for slide in result.output.slides:
    print(f"Slide {slide.slide_number}")
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