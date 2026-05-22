import json

"""
This script will look for a VIDEOID.jsonl file in comments_path and generate a HTML page based on it.
The comments format used is a modified version of the YouTube API, if you put the YT API comment responses into a jsonl file it *should* work.

This script assumes good-faith data, as the HTML used is what YouTube API provides.
Malicious actors could use this to achieve XSS, so please make sure your data is coming from a trusted source.

This script purposefully avoids config.json as I want people to understand what they're getting into before using this.
"""

comments_enabled = False
comments_path = "/var/www/html/comments/"


def _format_timestamp(published, updated):
    timestamp = published.replace("T", " ").replace("Z", " ")
    if published != updated:
        timestamp += f' (edited {updated.replace("T", " ").replace("Z", " ")})'
    return timestamp


def _format_likes(count):
    return f'{count} like' if count == 1 else f'{count} likes'


def _parse_snippet(csnip):
    return {
        "author_url": csnip["authorChannelUrl"],
        "author_name": csnip["authorDisplayName"],
        "timestamp": _format_timestamp(csnip["publishedAt"], csnip["updatedAt"]),
        "text": csnip["textDisplay"],  # intentional: YouTube API HTML content, rendered with | safe
        "likes": _format_likes(csnip["likeCount"]),
        "replies": [],
    }


def getCommentsData(video_id):
    if not comments_enabled:
        return None, 0
    raw_comments = []
    header = {}
    try:
        with open(f"{comments_path}/{video_id}.jsonl", "r") as f:
            header = json.loads(f.readline())
            if "time_fetched" not in header:
                raw_comments.append(header)
                header = {"time_fetched": "N/A"}
            for line in f:
                raw_comments.append(json.loads(line))
    except Exception:
        return None, 0

    comments = []
    top_count = 0
    total_count = 0
    for raw in raw_comments:
        top_count += 1
        total_count += 1
        comment = _parse_snippet(raw["snippet"]["topLevelComment"]["snippet"])
        if "replies" in raw:
            for reply in raw["replies"]["comments"][::-1]:
                total_count += 1
                comment["replies"].append(_parse_snippet(reply["snippet"]))
        comments.append(comment)

    return {
        "comments": comments,
        "time_fetched": header["time_fetched"][:16].replace("T", " "),
        "top_count": top_count,
        "total_count": total_count,
    }, top_count
