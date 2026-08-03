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