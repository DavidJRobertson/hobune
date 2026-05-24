import json
import os

from hobune.categories import category_slug
from hobune.tags import tag_slug
from hobune.channels import is_full_channel, get_channel_name
from hobune.comments import getCommentsData
from hobune.logger import logger
from hobune.util import no_traverse


def create_video_pages(config, channels, env):
    dir_listings = {}
    tmpl = env.get_template("video.html")
    comments_tmpl = env.get_template("comments.html")
    missing_thumbnails = []
    for channel in channels:
        logger.debug(f"Creating video pages for {channels[channel].name}")
        for video_entry in channels[channel].videos:
            root = video_entry["root"]
            file = video_entry["file"]
            if root not in dir_listings:
                dir_listings[root] = os.listdir(root)
            files = dir_listings[root]
            try:
                if file is not None:
                    with open(os.path.join(root, file), "r") as f:
                        v = json.load(f)
                    base = file[:-len(".info.json")]
                else:
                    v = {"id": video_entry["id"], "title": video_entry["title"], "description": ""}
                    base = video_entry["id"]

                # Generate comments page
                comments_data, comments_count = getCommentsData(v['id'])
                if comments_data:
                    with open(os.path.join(config.output_path, f"comments/{no_traverse(v['id'])}.html"), "w") as f:
                        f.write(comments_tmpl.render(
                            title=v['title'] + ' - Comments',
                            meta={"description": v.get('description', '')[:256], "author": get_channel_name(v)},
                            video_id=v['id'],
                            **comments_data,
                        ))

                # Set video path
                mp4path = f"{os.path.join(config.files_web_path + root[len(config.files_path):], base)}.mp4"
                for ext in ["mp4", "webm", "mkv"]:
                    if f"{base}.{ext}" in files:
                        mp4path = f"{os.path.join(config.files_web_path + root[len(config.files_path):], base)}.{ext}"
                        break

                # Get thumbnail path
                default_thumbnail = config.web_root + "default.svg"
                thumbnail = default_thumbnail
                for ext in ["webp", "jpg", "png"]:
                    if (thumbnail_file := f"{base}.{ext}") in files:
                        thumbnail = config.files_web_path + os.path.join(root, thumbnail_file)[len(config.files_path):]

                # Build download buttons list
                download_buttons = []
                alt_formats = [(ext, f"{base}.{ext}") for ext in ["webm", "mkv"] if f"{base}.{ext}" in files]
                if alt_formats:
                    download_buttons.append({"name": "Download mp4", "url": mp4path})
                    for ext, alt_file in alt_formats:
                        alt_url = config.files_web_path + os.path.join(root, alt_file)[len(config.files_path):]
                        download_buttons.append({"name": f"Download {ext}", "url": alt_url})
                else:
                    download_buttons.append({"name": "Download video", "url": mp4path})

                if (desc_file := f"{base}.description") in files:
                    desc_url = config.files_web_path + os.path.join(root, desc_file)[len(config.files_path):]
                    download_buttons.append({"name": "Description", "url": desc_url})

                if thumbnail != default_thumbnail:
                    download_buttons.append({"name": "Thumbnail", "url": thumbnail})
                else:
                    missing_thumbnails.append(v.get('webpage_url') or v['id'])

                for vtt in (vtt for vtt in files if vtt.endswith(".vtt")):
                    if vtt.startswith(base):
                        vtt_url = os.path.join(config.files_web_path + root[len(config.files_path):], vtt)
                        vtt_tag = vtt[len(base) + 1:-len('.vtt')]
                        download_buttons.append({"name": f"Subtitles ({vtt_tag})", "url": vtt_url})

                # Format upload date
                upload_date_raw = v.get('upload_date')
                upload_date = None
                if upload_date_raw:
                    upload_date = f"{upload_date_raw[:4]}-{upload_date_raw[4:6]}-{upload_date_raw[6:]}"

                full_channel = is_full_channel(root)
                channel_id = v.get('channel_id', v.get('uploader_id', ''))

                with open(os.path.join(config.output_path, f"videos/{no_traverse(v['id'])}.html"), "w") as f:
                    f.write(tmpl.render(
                        title=v['title'],
                        meta={"description": v.get('description', '')[:256], "author": get_channel_name(v)},
                        video_id=v['id'],
                        thumbnail=thumbnail,
                        video=mp4path,
                        comments_count=comments_count,
                        description=v.get('description', "N/A"),
                        webpage_url=v.get('webpage_url'),
                        views=v.get('view_count'),
                        date=upload_date,
                        uploader_id=channel_id,
                        uploader=get_channel_name(v),
                        is_full_channel=full_channel,
                        download_buttons=download_buttons,
                        tags=[{"name": t, "slug": no_traverse(tag_slug(t))} for t in (v.get('tags') or [])],
                        categories=[{"name": c, "slug": no_traverse(category_slug(c))} for c in (v.get('categories') or [])],
                    ))
            except Exception as e:
                logger.error(f"Error processing {file}")
                print(e)
    return missing_thumbnails
