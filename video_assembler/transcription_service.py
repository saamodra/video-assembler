import os
import json
import threading
from typing import Optional, Tuple

class TranscriptionService:
    """Service exclusively focused on handling whisper transcription (SRP) and caching."""
    
    def __init__(self, crop_padding: float):
        self._lock = threading.Lock()
        self.crop_padding = crop_padding
        self.model = None

    def crop_video_to_text(self, video_path: str, target_text: str) -> Optional[Tuple[float, float]]:
        cache_path = f"{video_path}.json"
        segments = None

        if os.path.exists(cache_path):
            print(f"Using cached transcription from {cache_path}...")
            try:
                with open(cache_path, "r", encoding="utf-8") as f:
                    segments = json.load(f)
            except json.JSONDecodeError:
                pass

        if segments is None:
            with self._lock:
                if os.path.exists(cache_path):
                    with open(cache_path, "r", encoding="utf-8") as f:
                        segments = json.load(f)
                else:
                    self._ensure_model_loaded()
                    print(f"Transcribing '{video_path}' to find speech matching text...")
                    result = self.model.transcribe(video_path, word_timestamps=True)
                    segments = result["segments"]

                    with open(cache_path, "w", encoding="utf-8") as f:
                        json.dump(segments, f, ensure_ascii=False, indent=2)

        return self._find_timestamp_in_segments(video_path, target_text, segments, char_times=[])

    def _ensure_model_loaded(self):
        if self.model is not None:
            return
            
        import whisper
        import imageio_ffmpeg
        import ssl

        # Bind ffmpeg securely
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        ffmpeg_dir = os.path.dirname(ffmpeg_exe)
        ffmpeg_symlink = os.path.join(ffmpeg_dir, 'ffmpeg')
        if not os.path.exists(ffmpeg_symlink):
            try:
                os.symlink(ffmpeg_exe, ffmpeg_symlink)
            except Exception:
                pass

        if ffmpeg_dir not in os.environ["PATH"]:
            os.environ["PATH"] += os.pathsep + ffmpeg_dir

        print("Loading Whisper model (might take a moment)...")
        try:
            ssl._create_default_https_context = ssl._create_unverified_context
        except AttributeError:
            pass

        self.model = whisper.load_model("base")

    def _find_timestamp_in_segments(self, video_path: str, target_text: str, segments: list, char_times: list) -> Optional[Tuple[float, float]]:
        joined_text = ""
        char_times.clear()

        for seg in segments:
            words = seg.get("words", [{"text": seg["text"], "start": seg["start"], "end": seg["end"]}])
            for w in words:
                text = w.get("word", w.get("text", ""))
                start = w["start"]
                end = w["end"]
                clean_word = "".join(text.split())
                if not clean_word:
                    continue

                time_per_char = (end - start) / len(clean_word)
                for i, char in enumerate(clean_word):
                    joined_text += char.lower()
                    char_times.append((start + i * time_per_char, start + (i + 1) * time_per_char))

        import fuzzysearch
        clean_target = "".join(target_text.split()).lower()

        idx = joined_text.find(clean_target)
        start_idx, end_idx = None, None

        if idx != -1:
            start_idx = idx
            end_idx = min(idx + len(clean_target) - 1, len(char_times) - 1)
        else:
            max_err = max(3, int(len(clean_target) * 0.4))
            matches = fuzzysearch.find_near_matches(clean_target, joined_text, max_l_dist=max_err)
            if matches:
                best_match = min(matches, key=lambda m: m.dist)
                start_idx = best_match.start
                end_idx = min(best_match.end - 1, len(char_times) - 1)
                print(f"Fuzzy match found! Matched with '{best_match.matched}' (error margin: {best_match.dist})")

        if start_idx is None:
            raw_text = "".join(seg["text"] for seg in segments)
            print(f"Warning: Exact string not found in transcription for {video_path}")
            print(f"Whisper heard: '{raw_text.strip()}'")
            return None

        start_time = char_times[start_idx][0]
        end_time = char_times[end_idx][1]

        return max(0, start_time - self.crop_padding), end_time + self.crop_padding
