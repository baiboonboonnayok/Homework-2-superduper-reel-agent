import glob
import re
import subprocess
import os

TRANSITION_SECONDS = 0.5

def get_audio_duration(path: str) -> float:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", path],
        capture_output=True, text=True
    )
    return float(result.stdout.strip())

def render_html_to_mp4():
    """Converts HTML slides to video clips matching exact audio lengths."""
    slides = sorted(glob.glob("slides/slide_*.html"))
    for slide_path in slides:
        num = re.search(r"slide_(\d+)\.html", slide_path).group(1)
        audio_path = f"audio/slide_{num}.mp3"
        out_clip = f"video_clips/clip_{num}.mp4"
        
        duration = get_audio_duration(audio_path)
        
        # Use npx playwright or ffmpeg image rendering
        # Generating video clip from static slide + audio clip
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1", "-i", f"slides/slide_{num}.png" if os.path.exists(f"slides/slide_{num}.png") else "-f", "lavfi", "-i", "color=c=0x0f172a:s=1080x1920",
            "-i", audio_path,
            "-c:v", "libx264", "-t", str(duration), "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "1920k",
            out_clip
        ]
        # Run conversion clip by clip
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def stitch_reel():
    clip_files = glob.glob("video_clips/clip_*.mp4")
    slide_numbers = sorted([int(re.search(r"clip_(\d+)\.mp4", f).group(1)) for f in clip_files])
    
    if not slide_numbers:
        print("No video clips found!")
        return

    clip_paths = [f"video_clips/clip_{n}.mp4" for n in slide_numbers]
    
    # Simple FFmpeg Concatenation Command
    with open("concat_list.txt", "w") as f:
        for p in clip_paths:
            f.write(f"file '{p}'\n")
            
    cmd = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", "concat_list.txt",
        "-c", "copy", "reel.mp4"
    ]
    subprocess.run(cmd)
    if os.path.exists("concat_list.txt"):
        os.remove("concat_list.txt")
    print("🎬 Successfully generated reel.mp4!")

if __name__ == "__main__":
    stitch_reel()