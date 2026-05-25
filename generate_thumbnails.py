import json
import os
import subprocess
import sys

THUMBNAIL_EXTS = ["webp", "jpg", "png"]
VIDEO_EXTS = ["mp4", "webm", "mkv"]
SEEK_SECONDS = 5


def has_thumbnail(directory, base):
    return any(os.path.isfile(os.path.join(directory, base + "." + ext)) for ext in THUMBNAIL_EXTS)


def generate_thumbnail(video_path, thumbnail_path):
    result = subprocess.run(
        ["ffmpeg", "-ss", str(SEEK_SECONDS), "-i", video_path,
         "-vframes", "1", "-vf", "scale=640:480:force_original_aspect_ratio=decrease", "-q:v", "2", "-y", thumbnail_path],
        capture_output=True,
    )
    if result.returncode != 0:
        # Video may be shorter than SEEK_SECONDS — retry from beginning
        result = subprocess.run(
            ["ffmpeg", "-i", video_path, "-vframes", "1", "-vf", "scale=640:480:force_original_aspect_ratio=decrease", "-q:v", "2", "-y", thumbnail_path],
            capture_output=True,
        )
    return result.returncode == 0


args = sys.argv[1:]
yes_all = "-y" in args
args = [a for a in args if a != "-y"]
config_path = args[0] if args else "config.json"
with open(config_path) as f:
    config = json.load(f)

files_path = config["files_path"]

generated = 0
failed = 0

for root, _, files in os.walk(files_path):
    for file in files:
        for ext in VIDEO_EXTS:
            if file.endswith(f".{ext}"):
                base = file[:-len(f".{ext}")]
                if not has_thumbnail(root, base):
                    video_path = os.path.join(root, file)
                    thumbnail_path = os.path.join(root, base + ".jpg")
                    if not yes_all:
                        answer = input(f"Generate thumbnail for {video_path}? [y/N] ").strip().lower()
                        if answer != "y":
                            continue
                    if generate_thumbnail(video_path, thumbnail_path):
                        generated += 1
                    else:
                        print(f"  FAILED")
                        failed += 1
                break

print(f"\nDone: {generated} generated, {failed} failed.")
