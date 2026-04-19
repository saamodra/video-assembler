import sys
from video_assembler.app_config import AppConfig
from video_assembler.script_parser import ScriptParser
from video_assembler.transcription_service import TranscriptionService
from video_assembler.video_renderer import VideoRenderer

def main():
    if len(sys.argv) < 2:
        print("Usage: python build_video.py <script.txt>")
        sys.exit(1)

    script_path = sys.argv[1]

    # Dependency Injection & Config Bootstrapping
    try:
        config = AppConfig("config.json")
    except RuntimeError as e:
        print(f"Error: {e}")
        sys.exit(1)

    # Initialize domain services
    parser = ScriptParser()
    transcriber = TranscriptionService(crop_padding=config.get("crop_padding", 0.3))
    
    # Render service heavily depends on external IO and config
    renderer = VideoRenderer(config=config, transcriber=transcriber)

    # Core Workflow Pipeline
    timeline = parser.parse(script_path)
    output_path = config.get("output_path")
    renderer.render(timeline, output_path)

if __name__ == "__main__":
    main()
