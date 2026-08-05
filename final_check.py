import json
import os
import re
import subprocess

all_ok = True

def check(label, condition):
    global all_ok
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {label}")
    all_ok = all_ok and condition
    return condition

print("=== Required top-level files ===")
for f in ["README.md", "requirements.txt", ".gitignore", "project_proposal.md", "reel_agent.py"]:
    check(f"{f} exists", os.path.isfile(f))

print("\n=== slides/ folder ===")
slide_files = sorted(f for f in os.listdir("slides") if f.endswith(".html")) if os.path.isdir("slides") else []
check(f"slides/ has 4-6 HTML files (found {len(slide_files)}: {slide_files})", 4 <= len(slide_files) <= 6)

print("\n=== ai_grading/ folder ===")
ai_grading_files = set(os.listdir("ai_grading")) if os.path.isdir("ai_grading") else set()
check("ai_grading/slide_plan.json exists", "slide_plan.json" in ai_grading_files)
check("ai_grading/critique_feedback.json exists", "critique_feedback.json" in ai_grading_files)
check("ai_grading/agent_flow.svg or .png exists", "agent_flow.svg" in ai_grading_files or "agent_flow.png" in ai_grading_files)

print("\n=== slide_plan.json structure ===")
try:
    with open("ai_grading/slide_plan.json") as f:
        plan = json.load(f)
    slides = plan.get("slides", [])
    required_keys = {"slide_number", "headline", "description", "bullets", "narration"}
    keys_ok = all(required_keys.issubset(s.keys()) for s in slides)
    check(f"{len(slides)} slides, each with slide_number/headline/description/bullets/narration", keys_ok and 4 <= len(slides) <= 6)
except Exception as e:
    check(f"slide_plan.json readable and valid (error: {e})", False)

print("\n=== critique_feedback.json structure ===")
try:
    with open("ai_grading/critique_feedback.json") as f:
        records = json.load(f)
    needed = {"original_headline", "original_description", "original_bullets", "original_narration",
              "critique", "revised_headline", "revised_description", "revised_bullets", "revised_narration"}
    fb_keys_ok = all(needed.issubset(r.keys()) for r in records)
    check(f"{len(records)} entries, each with original + critique + revised fields", fb_keys_ok and len(records) == len(slide_files))
except Exception as e:
    check(f"critique_feedback.json readable and valid (error: {e})", False)

print("\n=== .gitignore ===")
try:
    gitignore = open(".gitignore").read()
    check(".gitignore includes .env", ".env" in gitignore)
    check(".gitignore includes __pycache__", "__pycache__" in gitignore)
except Exception as e:
    check(f".gitignore readable (error: {e})", False)

print("\n=== reel_agent.py required tech ===")
try:
    code = open("reel_agent.py").read()
    check("uses gpt-5.6-luna", "gpt-5.6-luna" in code)
    check("uses tts-1-hd", "tts-1-hd" in code)
    check("uses asyncio.gather (parallelization)", "asyncio.gather" in code)
    check("reads project_proposal.md", "project_proposal.md" in code)
except Exception as e:
    check(f"reel_agent.py readable (error: {e})", False)

print("\n=== requirements.txt / README.md ===")
try:
    check("requirements.txt is non-empty", len(open("requirements.txt").read().strip()) > 0)
except Exception as e:
    check(f"requirements.txt readable (error: {e})", False)
try:
    check("README.md mentions how to run reel_agent.py", "reel_agent.py" in open("README.md").read())
except Exception as e:
    check(f"README.md readable (error: {e})", False)

print("\n=== reel.mp4 ===")
if os.path.isfile("reel.mp4"):
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", "reel.mp4"],
        capture_output=True, text=True
    )
    try:
        dur = float(result.stdout.strip())
        check(f"duration is {dur:.2f}s (must be 30-60s)", 30 <= dur <= 60)
    except Exception:
        check("duration readable", False)
    mtime = subprocess.run(["stat", "-f", "%Sm", "reel.mp4"], capture_output=True, text=True).stdout.strip()
    print(f"[INFO] reel.mp4 last modified: {mtime}")
else:
    check("reel.mp4 exists locally", False)

print("\n=== git status ===")
subprocess.run(["git", "status", "--short"])

print("\n=== nothing sensitive or huge tracked by git ===")
tracked = subprocess.run(["git", "ls-files"], capture_output=True, text=True).stdout
check(".env is NOT tracked by git", ".env" not in tracked.splitlines())
bad_media = [f for f in tracked.splitlines() if re.search(r"\.(mp4|mp3|webm)$", f)]
check(f"no mp4/mp3/webm tracked (found: {bad_media})", len(bad_media) == 0)

print("\n=== local vs pushed commit ===")
local_head = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
subprocess.run(["git", "fetch"], capture_output=True, text=True)
remote_head = subprocess.run(["git", "rev-parse", "origin/main"], capture_output=True, text=True).stdout.strip()
check(f"local commit ({local_head[:7]}) matches pushed remote ({remote_head[:7]})", local_head == remote_head)

dirty = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True).stdout.strip()
tracked_dirty = [l for l in dirty.splitlines() if not l.strip().startswith("??")]
check(f"no uncommitted changes to tracked files (dirty: {tracked_dirty})", len(tracked_dirty) == 0)

print("\n" + "=" * 50)
print("ALL CHECKS PASSED" if all_ok else "SOME CHECKS FAILED — see [FAIL] lines above")
print("=" * 50)

print("\n=== description matches actual rendered HTML (mechanical cross-check) ===")
marker_by_type = {
    "hero": None, "cta": None,
    "bullets": "editorial-box",
    "pipeline": "flow-step",
    "scorecard": "metric-item",
}
try:
    with open("ai_grading/slide_plan.json") as f:
        plan = json.load(f)
    mismatch = []
    total = len(plan["slides"])
    for s in plan["slides"]:
        n = s["slide_number"]
        if n == 1:
            stype = "hero"
        elif n == total:
            stype = "cta"
        elif n == 3:
            stype = "pipeline"
        elif n == 4:
            stype = "scorecard"
        else:
            stype = "bullets"
        marker = marker_by_type[stype]
        if marker:
            html = open(f"slides/slide_{n}.html").read()
            if marker not in html:
                mismatch.append(f"slide {n} (expected {stype}, marker '{marker}' not found in HTML)")
    check(f"every slide's description matches its actual rendered HTML (mismatches: {mismatch})", len(mismatch) == 0)
except Exception as e:
    check(f"description/HTML cross-check ran (error: {e})", False)
