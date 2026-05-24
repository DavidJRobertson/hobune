import os
import re

from hobune.logger import logger
from hobune.util import no_traverse


def tag_slug(name):
    return re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')


def _build_tags(channels):
    tags = {}
    for ch in channels.values():
        for v in ch.videos:
            for tag in (v.get('tags') or []):
                if tag not in tags:
                    tags[tag] = []
                tags[tag].append(v)
    return tags


def create_tag_pages(config, env, channels):
    tags = _build_tags(channels)
    if not tags:
        return

    tag_tmpl = env.get_template("tag.html")
    tags_tmpl = env.get_template("tags.html")

    tags_list = []
    for tag_name, videos in tags.items():
        slug = no_traverse(tag_slug(tag_name))
        logger.debug(f"Creating tag page for {tag_name!r}")
        with open(os.path.join(config.output_path, f"tags/{slug}.html"), "w") as f:
            f.write(tag_tmpl.render(
                title=tag_name,
                meta={"description": f"Videos tagged: {tag_name}"},
                tag_name=tag_name,
                videos=sorted(videos, key=lambda v: v.get('upload_date') or 0, reverse=True),
                videos_count=len(videos),
            ))
        tags_list.append({
            "name": tag_name,
            "slug": slug,
            "videos_count": len(videos),
        })

    tags_list.sort(key=lambda t: (-t['videos_count'], t['name'].lower()))
    with open(os.path.join(config.output_path, "tags/index.html"), "w") as f:
        f.write(tags_tmpl.render(
            title="Tags",
            meta={"description": "Video tags"},
            tags=tags_list,
        ))
