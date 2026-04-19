import os
from pathlib import Path
import PIL.Image

if not hasattr(PIL.Image, 'ANTIALIAS'):
    PIL.Image.ANTIALIAS = PIL.Image.LANCZOS

os.environ["IMAGEMAGICK_BINARY"] = "/opt/homebrew/bin/magick"
from moviepy.editor import VideoFileClip, TextClip, concatenate_videoclips, CompositeVideoClip, ColorClip

from video_assembler.domain import TimelineItem, TitleSlide, TextSlide, VideoAsset
from video_assembler.transcription_service import TranscriptionService
from video_assembler.app_config import AppConfig

class VideoRenderer:
    """Service to render domain objects into an actual assembled video (SRP)."""
    
    def __init__(self, config: AppConfig, transcriber: TranscriptionService):
        self.config = config
        self.transcriber = transcriber

    def render(self, timeline: list, output_path: str):
        import concurrent.futures
        
        print("Building clips in parallel...")
        results = [None] * len(timeline)

        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = {executor.submit(self._process_item, item): i for i, item in enumerate(timeline)}
            for future in concurrent.futures.as_completed(futures):
                i = futures[future]
                try:
                    results[i] = future.result()
                except Exception as e:
                    print(f"Failed to process clip timeline item {i}: {e}")

        clips = [clip for clip in results if clip is not None]

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
            fps=self.config.get("fps"),
            codec="libx264",
            audio_codec="aac"
        )
        print(f"Done -> {output_path}")

    def _process_item(self, item: TimelineItem):
        if isinstance(item, TitleSlide):
            return self._create_title_slide(item)
        elif isinstance(item, TextSlide):
            return self._create_text_slide(item)
        elif isinstance(item, VideoAsset):
            return self._create_video_clip(item)
        return None

    def _create_title_slide(self, item: TitleSlide):
        resolution = tuple(self.config.get("resolution"))
        duration = self.config.get("title_duration")
        font_path = self.config.get("font_path")

        title_clip = TextClip(item.title, font=font_path, fontsize=70, color='white', bg_color='black', size=resolution)
        title_clip = title_clip.set_position('center').set_duration(duration)

        if item.subtitle:
            subtitle_clip = TextClip(item.subtitle, font=font_path, fontsize=40, color='white')
            subtitle_clip = subtitle_clip.set_position(('center', 450)).set_duration(duration)
            return CompositeVideoClip([title_clip, subtitle_clip], size=resolution).set_duration(duration)
            
        return title_clip

    def _create_text_slide(self, item: TextSlide):
        duration = self.config.get("text_duration")
        resolution = tuple(self.config.get("resolution"))
        font_path = self.config.get("font_path")

        txt_clip = TextClip(item.text, font=font_path, method='caption', size=(resolution[0] - 200, None), fontsize=50, color='white')
        bg_clip = ColorClip(size=resolution, color=[0, 0, 0]).set_duration(duration)
        return CompositeVideoClip([bg_clip, txt_clip.set_position('center')]).set_duration(duration)

    def _create_video_clip(self, item: VideoAsset):
        try:
            clip = VideoFileClip(item.path)
            
            if item.crop_text:
                times = self.transcriber.crop_video_to_text(item.path, item.crop_text)
                if times:
                    start_t = times[0]
                    end_t = min(times[1], clip.duration) if clip.duration else times[1]
                    clip = clip.subclip(start_t, end_t)
                    print(f"Cropped {item.path} to {start_t:.2f}s - {end_t:.2f}s")
            
            w, h = clip.size
            target_w, target_h = self.config.get("resolution")
            # object-fit: cover logic
            if w / h > target_w / target_h:
                clip = clip.resize(height=target_h)
                clip = clip.crop(x_center=clip.size[0]/2, y_center=clip.size[1]/2, width=target_w, height=target_h)
            else:
                clip = clip.resize(width=target_w)
                clip = clip.crop(x_center=clip.size[0]/2, y_center=clip.size[1]/2, width=target_w, height=target_h)
            
            return clip
        except Exception as e:
            print(f"Error loading {item.path}: {e}")
            return None
