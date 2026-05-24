import os
import re

from hobune.logger import logger
from hobune.util import no_traverse


def category_slug(name):
    return re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')


def _build_categories(channels):
    categories = {}
    for ch in channels.values():
        for v in ch.videos:
            for cat in (v.get('categories') or []):
                if cat not in categories:
                    categories[cat] = []
                categories[cat].append(v)
    return categories


def create_category_pages(config, env, channels):
    categories = _build_categories(channels)
    if not categories:
        return

    category_tmpl = env.get_template("category.html")
    categories_tmpl = env.get_template("categories.html")

    categories_list = []
    for cat_name, videos in categories.items():
        slug = no_traverse(category_slug(cat_name))
        logger.debug(f"Creating category page for {cat_name!r}")
        with open(os.path.join(config.output_path, f"categories/{slug}.html"), "w") as f:
            f.write(category_tmpl.render(
                title=cat_name,
                meta={"description": f"Videos in category: {cat_name}"},
                category_name=cat_name,
                videos=sorted(videos, key=lambda v: v.get('upload_date') or 0, reverse=True),
                videos_count=len(videos),
            ))
        categories_list.append({
            "name": cat_name,
            "slug": slug,
            "videos_count": len(videos),
        })

    categories_list.sort(key=lambda c: (-c['videos_count'], c['name'].lower()))
    with open(os.path.join(config.output_path, "categories/index.html"), "w") as f:
        f.write(categories_tmpl.render(
            title="Categories",
            meta={"description": "Video categories"},
            categories=categories_list,
        ))
