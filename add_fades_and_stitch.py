import glob
import re
import subprocess
import os

FADE_SECONDS = 0.3


def get_audio_duration(path):
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", path],
        capture_output=True, text=True
    )
    return float(result.stdout.strip())


audio_files = glob.glob("audio/slide_*.mp3")
slide_numbers = sorted(int(re.search(r"slide_(\d+)\.mp3", f).group(1)) for f in audio_files)

if not slide_numbers:
    raise SystemExit("No audio files found in audio/. Run reel_agent.py first.")

print(f"Found {len(slide_numbers)} slides: {slide_numbers}")

os.makedirs("video_clips_faded", exist_ok=True)

for n in slide_numbers:
    image_path = f"slides/slide_{n}.png"
    audio_path = f"audio/slide_{n}.mp3"
    clip_path = f"video_clips_faded/clip_{n}.mp4"
    duration = get_audio_duration(audio_path)
    fade_out_start = max(duration - FADE_SECONDS, 0)

    subprocess.run([
        "ffmpeg", "-y",
        "-loop", "1", "-i", image_path,
        "-i", audio_path,
        "-vf", f"fade=t=in:st=0:d={FADE_SECONDS},fade=t=out:st={fade_out_start:.3f}:d={FADE_SECONDS}",
        "-af", f"afade=t=in:st=0:d={FADE_SECONDS},afade=t=out:st={fade_out_start:.3f}:d={FADE_SECONDS}",
        "-c:v", "libx264", "-tune", "stillimage",
        "-c:a", "aac", "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-t", str(duration),
        clip_path
    ], check=True)

with open("video_clips_faded/concat_list.txt", "w") as f:
    for n in slide_numbers:
        f.write(f"file 'clip_{n}.mp4'\n")

subprocess.run([
    "ffmpeg", "-y",
    "-f", "concat", "-safe", "0",
    "-i", "video_clips_faded/concat_list.txt",
    "-c", "copy",
    "reel.mp4"
], check=True)

print("Saved final video to reel.mp4 with clean fade in/out on each slide, no audio overlap")
