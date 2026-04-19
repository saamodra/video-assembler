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

def crop_video_to_text(video_path, target_text):
    """
    Uses Whisper to find the target_text in the video's audio,
    and returns the start and end timestamps.
    """
    import whisper
    import imageio_ffmpeg
    import ssl
    import urllib.request
    
    # Ensure Whisper can find imageio's ffmpeg binary executing as 'ffmpeg'
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    ffmpeg_dir = os.path.dirname(ffmpeg_exe)
    ffmpeg_symlink = os.path.join(ffmpeg_dir, 'ffmpeg')
    if not os.path.exists(ffmpeg_symlink):
        try:
            os.symlink(ffmpeg_exe, ffmpeg_symlink)
        except Exception:
            pass # Ignore if we don't have write permissions, we'll gracefully try without
            
    if ffmpeg_dir not in os.environ["PATH"]:
        os.environ["PATH"] += os.pathsep + ffmpeg_dir

    if not hasattr(crop_video_to_text, "model"):
        print("Loading Whisper model (might take a moment)...")
        # Bypass SSL verification on mac for initial model download
        try:
            _create_unverified_https_context = ssl._create_unverified_context
        except AttributeError:
            pass
        else:
            ssl._create_default_https_context = _create_unverified_https_context
            
        crop_video_to_text.model = whisper.load_model("base")
        
    print(f"Transcribing '{video_path}' to find speech matching text...")
    result = crop_video_to_text.model.transcribe(video_path)
    segments = result["segments"]
    
    # Join all segment text and map char indices to timestamps
    joined_text = ""
    char_times = []
    
    for seg in segments:
        text = seg["text"]
        start = seg["start"]
        end = seg["end"]
        # keep only non-whitespace
        clean_seg = "".join(text.split())
        if not clean_seg:
            continue
            
        time_per_char = (end - start) / len(clean_seg)
        for i, char in enumerate(clean_seg):
            joined_text += char.lower()
            char_times.append((start + i * time_per_char, start + (i + 1) * time_per_char))
            
    import fuzzysearch
    
    clean_target = "".join(target_text.split()).lower()
    
    idx = joined_text.find(clean_target)
    start_idx = None
    end_idx = None
    
    if idx != -1:
        start_idx = idx
        end_idx = min(idx + len(clean_target) - 1, len(char_times) - 1)
    else:
        # Fallback to fuzzy search allowing up to 40% error margin
        max_err = max(3, int(len(clean_target) * 0.4))
        matches = fuzzysearch.find_near_matches(clean_target, joined_text, max_l_dist=max_err)
        if matches:
            best_match = min(matches, key=lambda m: m.dist)
            start_idx = best_match.start
            end_idx = min(best_match.end - 1, len(char_times) - 1)
            print(f"Fuzzy match found! Matched with '{best_match.matched}' (error margin: {best_match.dist})")
            
    if start_idx is None:
        raw_text = "".join(seg["text"] for seg in segments)
        print(f"Warning: Exact string not found in transcription for {video_path}.")
        print(f"Target sought: '{target_text}' (cleaned: {clean_target})")
        print(f"Whisper heard: '{raw_text.strip()}'")
        return None
        
    start_time = char_times[start_idx][0]
    end_time = char_times[end_idx][1]
    
    # Pad by 0.3s
    return max(0, start_time - 0.3), end_time + 0.3

def parse_script(script_path):
    """Reads the script file and produces a timeline list."""
    timeline = []
    title = None
    name = None
    
    with open(script_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("//"):
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
                # e.g., VIDEO: assets/video.mov | CROP_TEXT: こんにちは
                parts = [part.strip() for part in line.split(":", 1)[1].split("|")]
                path = parts[0]
                crop_text = None
                for part in parts[1:]:
                    if part.startswith("CROP_TEXT:"):
                        crop_text = part.split(":", 1)[1].strip()
                timeline.append({"type": "video", "path": path, "crop_text": crop_text})
                
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
                
                # Check for speech cropping
                if item.get("crop_text"):
                    times = crop_video_to_text(item["path"], item["crop_text"])
                    if times:
                        clip = clip.subclip(times[0], times[1])
                        print(f"Cropped {item['path']} to {times[0]:.2f}s - {times[1]:.2f}s")
                
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
