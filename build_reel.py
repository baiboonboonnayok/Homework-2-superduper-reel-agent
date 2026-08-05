import glob
import os
import re
import subprocess
from playwright.sync_api import sync_playwright

def main():
    print("1️⃣ Rendering animated HTML slides...")
    os.makedirs("slides", exist_ok=True)
    os.makedirs("video_clips", exist_ok=True)

    def get_audio_duration(path):
        res = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", path],
            capture_output=True, text=True
        )
        return float(res.stdout.strip())

    with sync_playwright() as p:
        # Launch browser with video recording enabled to capture the entrance animations!
        browser = p.chromium.launch()
        html_files = sorted(glob.glob("slides/slide_*.html"))
        
        for html_file in html_files:
            match = re.search(r"slide_(\d+)\.html", html_file)
            if match:
                num = match.group(1)
                abs_path = os.path.abspath(html_file)
                audio_path = f"audio/slide_{num}.mp3"
                dur = get_audio_duration(audio_path) if os.path.exists(audio_path) else 5.0

                # Create context with video recording active
                context = browser.new_context(
                    viewport={"width": 1080, "height": 1920},
                    record_video_dir="video_clips/temp_webm",
                    record_video_size={"width": 1080, "height": 1920}
                )
                page = context.new_page()
                page.goto(f"file://{abs_path}")
                
                # Wait for animations to fully execute on screen
                page.wait_for_timeout(int(dur * 1000))
                
                context.close()  # This saves the webm video file automatically

        browser.close()

    print("\n2️⃣ Converting animations into synchronized MP4 clips...")
    webm_files = sorted(glob.glob("video_clips/temp_webm/*.webm"))
    
    for webm_file in webm_files:
        # Find corresponding slide number based on index order
        base_name = os.path.basename(webm_file)
        # Match webm to slide index
        clips_matched = sorted(glob.glob("slides/slide_*.html"))
        
    # More reliable mapping via filename matching
    for i, html_file in enumerate(sorted(glob.glob("slides/slide_*.html"))):
        match = re.search(r"slide_(\d+)\.html", html_file)
        if match:
            num = match.group(1)
            audio_path = f"audio/slide_{num}.mp3"
            out_clip = f"video_clips/clip_{num}.mp4"
            
            if not os.path.exists(audio_path):
                continue
                
            dur = get_audio_duration(audio_path)
            
            # Find the generated webm file for this index
            if i < len(webm_files):
                source_webm = webm_files[i]
                cmd = [
                    "ffmpeg", "-y",
                    "-i", source_webm,
                    "-i", audio_path,
                    "-c:v", "libx264", "-t", str(dur),
                    "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "192k",
                    out_clip
                ]
                subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                print(f"   -> Built animated clip_{num}.mp4 ({dur:.1f}s)")

    print("\n3️⃣ Stitching final animated reel.mp4...")
    clips = sorted(glob.glob("video_clips/clip_*.mp4"))
    with open("concat_list.txt", "w") as f:
        for c in clips:
            f.write(f"file '{c}'\n")

    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", "concat_list.txt", "-c", "copy", "reel.mp4"])
    if os.path.exists("concat_list.txt"):
        os.remove("concat_list.txt")

    print("\n🎉 SUCCESS! Fully animated reel.mp4 is ready!")

if __name__ == "__main__":
    main()