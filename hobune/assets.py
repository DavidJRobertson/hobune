import os
import shutil

from jinja2 import Environment, FileSystemLoader
from markupsafe import Markup, escape

from hobune.util import quote_url


def nl2br(value):
    return Markup(str(escape(value)).replace('\n', '<br>\n'))


def url_quote_filter(value):
    return quote_url(str(value))


def init_assets(output_path):
    env = Environment(
        loader=FileSystemLoader('templates'),
        autoescape=True,
    )
    env.filters['nl2br'] = nl2br
    env.filters['url_quote'] = url_quote_filter

    for folder in ["channels", "videos", "comments"]:
        os.makedirs(os.path.join(output_path, folder), exist_ok=True)

    for asset in ["hobune.css", "hobune.js", "favicon.ico", "icons.woff"]:
        shutil.copy(f"templates/{asset}", output_path)

    return env


def update_templates(config, env, html_ext):
    custom_pages = [os.path.splitext(p)[0] for p in os.listdir('custom')]

    env.globals.update(
        web_root=config.web_root,
        site_name=config.site_name,
        html_ext=html_ext,
        custom_pages=custom_pages,
    )

    custom_tmpl = env.get_template("custom_page.html")
    for custom_page in os.listdir('custom'):
        with open(f"custom/{custom_page}", "r") as f:
            content = f.read()
        page_name = os.path.splitext(custom_page)[0]
        with open(os.path.join(config.output_path, f"{page_name}.html"), "w") as f:
            f.write(custom_tmpl.render(title=page_name, meta={}, content=content))

    with open(os.path.join(config.output_path, "index.html"), "w") as f:
        f.write(env.get_template("index.html").render(
            title="Home",
            meta={"description": f"{config.site_name} - archive"},
        ))
