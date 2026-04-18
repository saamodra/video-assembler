You are a senior Python developer.
Create a small CLI tool that **automatically generates a video from a script file**.

## Goal

Build a Python project that assembles a final video using:

* opening title
* text slides
* video clips

The video should follow a timeline like:

```
TITLE
TEXT
VIDEO
TEXT
VIDEO
TEXT
VIDEO
```

The user writes a simple script file that defines the sequence.

The program then renders the final video automatically.

---

# Tech Stack

Use:

* Python 3.10+
* MoviePy
* FFmpeg (via moviepy)

MoviePy should be used for:

* loading video clips
* creating text clips
* concatenating clips

MoviePy supports concatenating clips sequentially and adding text overlays programmatically. ([GeeksforGeeks][1])

---

# Project Structure

Generate the following project:

```
kaiwa-video-builder/
│
├─ build_video.py
├─ script.txt
├─ config.json
├─ requirements.txt
│
├─ assets/
│   ├─ video1.mp4
│   ├─ video2.mp4
│
└─ output/
    └─ final_video.mp4
```

---

# Script Format

The user writes a simple script file:

```
TITLE: Kaiwa Practice
NAME: Samodra

TEXT: こんにちは、はじめまして。
VIDEO: assets/video1.mp4

TEXT: 私の趣味はゲームです。
VIDEO: assets/video2.mp4

TEXT: 私の好きな食べ物はナシゴレンです。
VIDEO: assets/video3.mp4
```

Rules:

* `TITLE` → opening slide
* `NAME` → appears under title
* `TEXT` → text slide
* `VIDEO` → video clip

---

# Features

The tool should:

### 1. Create Opening Title

Display:

```
Kaiwa Practice
Samodra
```

Duration: 4 seconds

Centered text.

---

### 2. Text Slides

Each `TEXT:` block should generate a slide:

* black background
* white text
* centered
* duration 3 seconds

---

### 3. Video Clips

Each `VIDEO:` loads the specified video.

The clip should:

* auto resize to 1280x720
* preserve audio

---

### 4. Concatenate Timeline

All slides and videos should be combined in order using:

```
concatenate_videoclips()
```

---

### 5. Export

Output video:

```
output/final_video.mp4
```

Settings:

```
fps = 30
codec = libx264
audio_codec = aac
```

---

# CLI Usage

User runs:

```
python build_video.py script.txt
```

Output:

```
Rendering video...
Done → output/final_video.mp4
```

---

# Implementation Requirements

The code should include:

### Function

```
parse_script()
```

Reads the script file and produces a timeline list.

Example:

```
[
 {type:"title", text:"Kaiwa Practice", name:"Samodra"},
 {type:"text", text:"こんにちは、はじめまして。"},
 {type:"video", path:"assets/video1.mp4"}
]
```

---

### Function

```
create_text_slide(text, duration)
```

Uses MoviePy `TextClip`.

---

### Function

```
create_title_slide(title, name)
```

---

### Function

```
build_timeline(timeline)
```

Returns list of clips.

---

### Function

```
render_video(clips)
```

Writes final output.

---

# Bonus Features (Optional)

If possible also implement:

* fade transition between clips
* font customization
* text wrapping for Japanese text
* automatic video scaling

---

# Output

Generate:

1. complete Python code
2. requirements.txt
3. example script.txt
4. instructions to run

---

Write clean, modular, production-quality Python code with comments.

---

💡 If you want, I can also show you something **really cool**:

You could turn this into a **mini DSL like movie scripts**, for example:

```
TITLE "Kaiwa Practice"
NAME "Samodra"

SAY "こんにちは、はじめまして"
PLAY video1.mp4

SAY "私の趣味はゲームです"
PLAY video2.mp4
```
