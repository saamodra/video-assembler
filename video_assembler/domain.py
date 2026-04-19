from dataclasses import dataclass
from typing import Optional

@dataclass
class TimelineItem:
    """Base domain entity for all timeline objects."""
    pass

@dataclass
class TitleSlide(TimelineItem):
    title: str
    subtitle: Optional[str] = None

@dataclass
class TextSlide(TimelineItem):
    text: str

@dataclass
class VideoAsset(TimelineItem):
    path: str
    crop_text: Optional[str] = None
