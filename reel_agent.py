import os
from dotenv import load_dotenv
from pydantic import BaseModel
from pydantic_ai import Agent
import json
load_dotenv()

class Slide(BaseModel):
    slide_number: int
    description: str   # what's on screen: text and visuals
    narration: str      # what the voice says for this slide

class SlidePlan(BaseModel):
    slides: list[Slide]

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
def render_slide_html(slide):
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
  <p>{slide.description}</p>
</body>
</html>
"""
def render_visual_slide(slide):
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
os.makedirs("slides", exist_ok=True)
for slide in result.output.slides:
    if slide.slide_number == 3:
        html_content = render_visual_slide(slide)
    else:
        html_content = render_slide_html(slide)
    with open(f"slides/slide_{slide.slide_number}.html", "w") as f:
        f.write(html_content)

print("Saved HTML slides to slides/")