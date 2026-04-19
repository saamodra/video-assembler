from video_assembler.domain import TimelineItem, TitleSlide, TextSlide, VideoAsset
from typing import List

class ScriptParser:
    """Service to parse script files into domain entity objects."""
    
    def parse(self, script_path: str) -> List[TimelineItem]:
        timeline: List[TimelineItem] = []
        title = None
        subtitle = None

        with open(script_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or line.startswith("//"):
                    continue

                if line.startswith("TITLE:"):
                    title = line.split(":", 1)[1].strip()
                elif line.startswith("SUBTITLE:"):
                    subtitle = line.split(":", 1)[1].strip()
                    timeline.insert(0, TitleSlide(title=title, subtitle=subtitle))
                elif line.startswith("TEXT:"):
                    text = line.split(":", 1)[1].strip()
                    timeline.append(TextSlide(text=text))
                elif line.startswith("VIDEO:"):
                    parts = [part.strip() for part in line.split(":", 1)[1].split("|")]
                    path = parts[0]
                    crop_text = None
                    for part in parts[1:]:
                        if part.startswith("CROP_TEXT:"):
                            crop_text = part.split(":", 1)[1].strip()
                    timeline.append(VideoAsset(path=path, crop_text=crop_text))

        if title and not subtitle and not any(isinstance(item, TitleSlide) for item in timeline):
             timeline.insert(0, TitleSlide(title=title, subtitle=None))

        return timeline
