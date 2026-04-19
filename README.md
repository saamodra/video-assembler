# Video Assembler CLI

A Python command-line utility for programmatically assembling sequence-based videos from a text script. Automatically generates title slides, text overlay slides, and slices video files to extract specific spoken phrases using OpenAI's Whisper model!

## Features

- **Text & Title Slides:** Auto-generates nicely formatted text and title slides. Japanese text automatically wraps to fit the screen.
- **AI Audio Cropping:** Employs Whisper to transcribe and timestamp your clips automatically, searching for target spoken text using exact and fuzzy matching. Automatically clips video precisely to the start and end of spoken target phrases.
- **Auto Layout:** Resizes and crops provided video files to match your target resolution using standard "object-fit: cover" logic regardless of portrait or landscape orientation.
- **Configurable:** Global configuration via `config.json` allows for varying resolutions, font paths, framerate, crop padding, and more.

## Prerequisites & Installation

Video Assembler requires Python 3, making use of `venv` to avoid conflicting with your system dependencies. Ensure you also have ImageMagick installed on your system (e.g. `brew install imagemagick` on macOS) and a valid TrueType font in the `config.json`.

We provide quick-start scripts that automatically configure your virtual environment, install package dependencies via `requirements.txt`, and immediately build the video.

## Usage

1. **Test the Demo:** We've included a demo video (`examples/demo_video.mp4`) and an example script. You can build it immediately to see how auto-cropping works!
2. **Create your script:** Define your own video sequence in a script file (e.g., `script.conf`). See `script.example.conf` for syntax.
3. **Configure:** (Optional) Edit your `config.json` in the root directory to define global settings.
4. **Build!** Run the CLI tool wrapper based on your platform:

**For macOS / Linux (Bash):**
```bash
./run.sh script.example.conf
```

**For Windows (CMD / PowerShell):**
```cmd
.\run.bat script.example.conf
```

### Running Manually

If you prefer to operate the tool manually without the wrapper scripts, execute:

```bash
# Provide a local virtual environment
python -m venv venv

# Activate it (macOS/Linux)
source venv/bin/activate
# Activate it (Windows)
# venv\Scripts\activate

# Install dependencies from requirements
pip install -r requirements.txt

# Run your script
python build_video.py script.conf
```

The resulting video will be saved based on the `output_path` in your configuration (`output/final_video.mp4` by default).

## Script Syntax Reference

The parser accepts a plain text file using the following command directives:

- `TITLE: <Text>` Creates the main opening title slide. (Optional)
- `NAME: <Text>` Generates an overlay name under the Title. (Optional)
- `TEXT: <Text>` Generates a black slide auto-centering the provided text.
- `VIDEO: <filepath> | CROP_TEXT: <target_speech>` Integrates the specified `.mov`/`.mp4`. If `CROP_TEXT` is provided, it intelligently subsamples the video precisely over the boundaries of that spoken phrase.
- `//` or `#` Lines starting with these are ignored (comments/disabled lines).

## Configuration (`config.json`)

```json
{
  "output_path": "output/final_video.mp4",
  "resolution": [1920, 1080],
  "fps": 30,
  "title_duration": 4,
  "text_duration": 3,
  "font_path": "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
  "crop_padding": 0.3
}
```

## Future Improvements

If you'd like to improve the tool, consider contributing the following:

- **Transcription Caching:** Whisper currently re-transcribes the entire video every time a `VIDEO:` tag targets it. Caching local transcription results (e.g. `video.mov.json`) would drastically reduce build times when pulling multiple fragments from the same source clip.
- **Subtitle Overlay:** As Whisper generates word-level timestamps anyway, an excellent feature would be hard-burning those subtitles onto the output video itself.
- **Transitions:** Incorporating smooth `crossfadein` or fade-to-black effects via MoviePy would elevate the perceived quality.
- **Parallel Processing:** Building the cache or generating slides concurrently before final assembly.
- **Dynamic Framing:** Add options like `| FIT: contain` versus `cover` to avoid aggressively cropping out subjects in vertical video logic.
