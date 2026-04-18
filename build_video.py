import sys
import os
import json
from pathlib import Path

# Hot-patch Pillow 10+ for moviepy
import PIL.Image
if not hasattr(PIL.Image, 'ANTIALIAS'):
    PIL.Image.ANTIALIAS = PIL.Image.LANCZOS

os.environ["IMAGEMAGICK_BINARY"] = "/opt/homebrew/bin/magick"
from moviepy.editor import VideoFileClip, TextClip, concatenate_videoclips, CompositeVideoClip

def parse_script(script_path):
    """Reads the script file and produces a timeline list."""
    timeline = []
    title = None
    name = None
    
    with open(script_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
                
            if line.startswith("TITLE:"):
                title = line.split(":", 1)[1].strip()
            elif line.startswith("NAME:"):
                name = line.split(":", 1)[1].strip()
                timeline.insert(0, {"type": "title", "text": title, "name": name})
            elif line.startswith("TEXT:"):
                text = line.split(":", 1)[1].strip()
                timeline.append({"type": "text", "text": text})
            elif line.startswith("VIDEO:"):
                path = line.split(":", 1)[1].strip()
                timeline.append({"type": "video", "path": path})
                
    if title and not name and not any(item["type"] == "title" for item in timeline):
         timeline.insert(0, {"type": "title", "text": title, "name": ""})
         
    return timeline

def create_title_slide(title, name):
    """Creates opening title slide using MoviePy."""
    # Ensure background is purely black, size 1280x720
    title_clip = TextClip(title, font='/System/Library/Fonts/Supplemental/Arial Unicode.ttf', fontsize=70, color='white', bg_color='black', size=(1280, 720))
    title_clip = title_clip.set_position('center').set_duration(4)
    
    if name:
        # Overlay name text
        name_clip = TextClip(name, font='/System/Library/Fonts/Supplemental/Arial Unicode.ttf', fontsize=40, color='white')
        name_clip = name_clip.set_position(('center', 450)).set_duration(4)
        return CompositeVideoClip([title_clip, name_clip], size=(1280, 720)).set_duration(4)
        
    return title_clip

def create_text_slide(text, duration=3):
    """Creates a text slide."""
    from moviepy.editor import ColorClip
    # Use method='caption' and width=1080 to auto-wrap Japanese text
    txt_clip = TextClip(text, font='/System/Library/Fonts/Supplemental/Arial Unicode.ttf', method='caption', size=(1080, None), fontsize=50, color='white')
    bg_clip = ColorClip(size=(1280, 720), color=[0, 0, 0]).set_duration(duration)
    return CompositeVideoClip([bg_clip, txt_clip.set_position('center')]).set_duration(duration)

def build_timeline(timeline):
    """Returns list of clips based on timeline sequence."""
    from moviepy.editor import ColorClip
    clips = []
    for item in timeline:
        if item["type"] == "title":
            clips.append(create_title_slide(item["text"], item.get("name")))
        elif item["type"] == "text":
            clips.append(create_text_slide(item["text"]))
        elif item["type"] == "video":
            try:
                clip = VideoFileClip(item["path"])
                w, h = clip.size
                # object-fit: cover logic
                if w / h > 1280 / 720:
                    clip = clip.resize(height=720)
                    clip = clip.crop(x_center=clip.size[0]/2, y_center=clip.size[1]/2, width=1280, height=720)
                else:
                    clip = clip.resize(width=1280)
                    clip = clip.crop(x_center=clip.size[0]/2, y_center=clip.size[1]/2, width=1280, height=720)
                
                clips.append(clip)
            except Exception as e:
                print(f"Error loading {item['path']}: {e}")
    return clips

def render_video(clips, output_path):
    """Writes final output."""
    if not clips:
        print("No clips to render.")
        return
        
    print("Combining clips...")
    final_video = concatenate_videoclips(clips, method="compose")
    
    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    
    print("Rendering video...")
    final_video.write_videofile(
        str(out_file),
        fps=30,
        codec="libx264",
        audio_codec="aac"
    )
    print(f"Done -> {output_path}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python build_video.py <script.txt>")
        sys.exit(1)
        
    script_path = sys.argv[1]
    
    # Load optional config
    config = {}
    if Path("config.json").exists():
        with open("config.json", "r") as f:
            config = json.load(f)
            
    output_path = config.get("output_path", "output/final_video.mp4")
    
    timeline = parse_script(script_path)
    clips = build_timeline(timeline)
    render_video(clips, output_path)

if __name__ == "__main__":
    main()
