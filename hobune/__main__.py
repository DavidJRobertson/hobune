from hobune.assets import init_assets, update_templates
from hobune.categories import create_category_pages
from hobune.channels import initialize_channels, create_channel_pages, create_all_videos_page
from hobune.logger import logger
from hobune.config import load_config
from hobune.state import load_state, save_state, compute_diff, print_diff
from hobune.tags import create_tag_pages
from hobune.videos import create_video_pages


def main():
    config = load_config()
    if not config:
        exit()

    env = init_assets(config.output_path)

    html_ext = ".html" if config.add_html_ext else ""

    old_state = load_state(config.output_path)

    logger.info("Populating channels list")
    channels = initialize_channels(config)

    update_templates(config, env, html_ext)

    logger.info("Creating video pages")
    missing_thumbnails = create_video_pages(config, channels, env)

    logger.info("Creating channel pages")
    create_channel_pages(config, env, channels)

    logger.info("Creating all videos page")
    create_all_videos_page(config, env, channels)

    logger.info("Creating category pages")
    create_category_pages(config, env, channels)

    logger.info("Creating tag pages")
    create_tag_pages(config, env, channels)

    save_state(channels, config.output_path)
    logger.info("Done!")

    if old_state is not None:
        added, changed, removed = compute_diff(old_state, channels)
        print_diff(added, changed, removed)

    if missing_thumbnails:
        print(f"\nVideos missing thumbnails ({len(missing_thumbnails)}):")
        for url in missing_thumbnails:
            print(f"  {url}")


if __name__ == '__main__':
    main()
