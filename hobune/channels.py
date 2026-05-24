import hashlib
import json
import os
import shutil
from dataclasses import dataclass, field
from typing import Optional

from hobune.logger import logger
from hobune.util import extract_ids_from_txt, no_traverse


@dataclass
class HobuneChannel:
    id: str
    name: str
    weak_name: Optional[bool] = False
    date: Optional[int] = 0
    removed_count: Optional[int] = 0
    unlisted_count: Optional[int] = 0
    videos: list = field(default_factory=list)
    names: set = field(default_factory=set)
    handles: set = field(default_factory=set)
    username: Optional[str] = None


# If this returns false, the videos go in the "other" channel (e.g. `return "/channels/" in root`)
def is_full_channel(root):
    return True


def get_channel_details(v):
    channel_id = v.get("channel_id", v.get("uploader_id", "NA"))
    uploader_id = v.get("uploader_id")
    channel_username = uploader_id if uploader_id and uploader_id[0] != "@" and uploader_id != channel_id else None
    channel_handle = uploader_id if uploader_id and uploader_id[0] == "@" else None
    weak_name = "uploader" not in v
    channel_name = v.get("uploader", channel_username or channel_handle or channel_id)
    return [
        channel_name,
        weak_name,
        channel_id,
        uploader_id,
        channel_username,
        channel_handle,
    ]


def get_channel_name(v):
    return v.get("uploader", get_channel_details(v)[0])


def process_channel(channels, v, full):
    if full:
        channel_name, weak_name, channel_id, uploader_id, channel_username, channel_handle = get_channel_details(v)
        if not channel_id:
            raise KeyError("channel_id not found")
        if channel_id not in channels:
            channels[channel_id] = HobuneChannel(channel_id, channel_name, weak_name=weak_name)
            logger.debug(f"Added new channel {channel_name}")
        if channels[channel_id].date < int(v.get("upload_date", 1)):
            channels[channel_id].date = int(v.get("upload_date", 1))
            if not weak_name:
                channels[channel_id].name = channel_name
        if not weak_name:
            channels[channel_id].names.add(channel_name)
        if channel_handle:
            channels[channel_id].handles.add(channel_handle)
        if channel_username:
            channels[channel_id].username = channel_username
    else:
        channel_id = "other"
    return channel_id


def initialize_channels(config):
    removed_videos = extract_ids_from_txt(config.removed_videos_file)
    unlisted_videos = extract_ids_from_txt(config.unlisted_videos_file)
    processed_video_ids = set()

    channels = {
        "other": HobuneChannel("other", "Other videos")
    }
    for root, subdirs, files in os.walk(config.files_path):
        files.sort(reverse=True)
        info_json_bases = {f[:-len(".info.json")] for f in files if f.endswith(".info.json")}
        for file in (file for file in files if file.endswith(".info.json")):
            try:
                with open(os.path.join(root, file), "r") as f:
                    v = json.load(f)
                if v.get("_type") == "playlist" or (len(v["id"]) == 24 and v.get("extractor") == "youtube:tab"):
                    continue
                channel_id = process_channel(channels, v, is_full_channel(root))

                base = file[:-len(".info.json")]
                v["has_video_file"] = False
                v["video_size"] = None
                for ext in ["mp4", "webm", "mkv"]:
                    if (video_file := base + f".{ext}") in files:
                        v["has_video_file"] = True
                        v["video_size"] = os.path.getsize(os.path.join(root, video_file))
                        break

                v["custom_thumbnail"] = config.web_root + "default.svg"
                for ext in ["webp", "jpg", "png"]:
                    if base + f".{ext}" in files:
                        v["custom_thumbnail"] = config.files_web_path + (os.path.join(root, file)[
                                                                         :-len('.info.json')] + f".{ext}")[
                                                                        len(config.files_path):]

                v["root"] = root
                v["file"] = file

                if v["id"] in processed_video_ids and len(
                        old_v := [video for video in channels[channel_id].videos if video["id"] == v["id"]]):
                    old_v = old_v[0]
                    if not old_v["has_video_file"] and v["has_video_file"]:
                        old_v["has_video_file"] = v["has_video_file"]
                        old_v["root"] = v["root"]
                        old_v["file"] = v["file"]
                        old_v["custom_thumbnail"] = v["custom_thumbnail"]
                    continue

                v["removed"] = (v["id"] in removed_videos)
                if v["removed"]:
                    channels[channel_id].removed_count += 1
                v["unlisted"] = (v["id"] in unlisted_videos)
                if v["unlisted"]:
                    channels[channel_id].unlisted_count += 1

                v["description_hash"] = hashlib.md5(
                    (v.get("description") or "").encode()
                ).hexdigest()[:8]

                [v.pop(k) for k in list(v.keys()) if
                 k not in ["title", "id", "uploader", "webpage_url", "custom_thumbnail", "view_count",
                           "upload_date", "description_hash", "video_size", "removed", "unlisted", "root", "file", "has_video_file"]
                 ]
                channels[channel_id].videos.append(v)
                processed_video_ids.add(v["id"])
            except Exception as e:
                print(f"Error processing {file}", e)

        for file in files:
            for ext in ["mp4", "webm", "mkv"]:
                if file.endswith(f".{ext}"):
                    base = file[:-len(f".{ext}")]
                    if base not in info_json_bases and base not in processed_video_ids:
                        thumbnail = config.web_root + "default.svg"
                        for thumb_ext in ["webp", "jpg", "png"]:
                            if base + f".{thumb_ext}" in files:
                                thumbnail = config.files_web_path + os.path.join(root, base + f".{thumb_ext}")[len(config.files_path):]
                                break
                        channels["other"].videos.append({
                            "id": base,
                            "title": base.replace("_", " ").replace("-", " "),
                            "uploader": None,
                            "webpage_url": None,
                            "custom_thumbnail": thumbnail,
                            "view_count": None,
                            "upload_date": None,
                            "description_hash": hashlib.md5(b"").hexdigest()[:8],
                            "video_size": os.path.getsize(os.path.join(root, file)),
                            "removed": False,
                            "unlisted": False,
                            "root": root,
                            "file": None,
                            "has_video_file": True,
                        })
                        processed_video_ids.add(base)
                    break

    username_map = {}
    for _, channel in channels.items():
        if channel.username and channel.username != channel.id:
            username_map[channel.username] = channel.id
    for username, channel_id in username_map.items():
        channel = channels.pop(username, None)
        if channel:
            channels[channel_id].removed_count += channel.removed_count
            channels[channel_id].unlisted_count += channel.unlisted_count
            channels[channel_id].videos += channel.videos
            channels[channel_id].names = channels[channel_id].names | channel.names

    return channels


def get_channel_note(channel):
    note_path = f"note/{channel}".replace(".", "_")
    if not os.path.isfile(note_path):
        return ""
    with open(note_path, "r") as f:
        return f.read()


def get_channel_search_string(channel: HobuneChannel):
    all_names = list(channel.names) + list(channel.handles) + ([channel.username] if channel.username else [])
    return "; ".join(all_names)


def create_all_videos_page(config, env, channels):
    all_videos = []
    for ch in channels.values():
        all_videos.extend(ch.videos)
    all_videos.sort(key=lambda v: (v.get('title') or '').lower())
    with open(os.path.join(config.output_path, "videos/index.html"), "w") as f:
        f.write(env.get_template("all_videos.html").render(
            title="Videos",
            meta={"description": "All archived videos"},
            videos=all_videos,
            total=len(all_videos),
        ))


def create_channel_pages(config, env, channels):
    channel_tmpl = env.get_template("channel.html")
    channels_tmpl = env.get_template("channels.html")

    channels_list = []
    for channel_id, ch in channels.items():
        if channel_id == "other" and len(ch.videos) == 0:
            logger.debug("Skipping channel page for 'other' because it is empty")
            continue
        logger.debug(f"Creating channel pages for {ch.name}")

        aka_names = [n for n in ch.names if n != ch.name]
        with open(channel_html_path := os.path.join(config.output_path, f"channels/{no_traverse(channel_id)}.html"),
                  "w") as f:
            f.write(channel_tmpl.render(
                title=ch.name,
                meta={"description": f"{ch.name}'s channel archive"},
                channel_id=channel_id,
                channel_name=ch.name,
                channel_username=ch.username,
                aka_handles=list(ch.handles),
                aka_names=aka_names,
                videos_count=len(ch.videos),
                removed_count=ch.removed_count,
                unlisted_count=ch.unlisted_count,
                note=get_channel_note(channel_id),
                videos=sorted(ch.videos, key=lambda x: x.get('upload_date') or 0, reverse=True),
            ))

        if ch.username:
            shutil.copy(channel_html_path,
                        os.path.join(config.output_path, f"channels/{no_traverse(ch.username)}.html"))

        channels_list.append({
            "id": channel_id,
            "name": ch.name,
            "username": ch.username,
            "search_string": get_channel_search_string(ch),
            "videos_count": len(ch.videos),
            "removed_count": ch.removed_count,
            "unlisted_count": ch.unlisted_count,
        })

    channels_list.sort(key=lambda ch: (-ch['videos_count'], ch['name'].lower()))
    with open(os.path.join(config.output_path, "channels/index.html"), "w") as f:
        f.write(channels_tmpl.render(
            title="Channels",
            meta={"description": "Archived channels"},
            channels=channels_list,
        ))
