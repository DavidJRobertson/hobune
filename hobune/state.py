import json
import os

STATE_PATH = "hobune_state.json"


def _build_state(channels):
    state = {}
    for ch in channels.values():
        for v in ch.videos:
            state[v["id"]] = {
                "title": v.get("title", ""),
                "url": v.get("webpage_url"),
                "file": v.get("file"),
                "description_hash": v.get("description_hash", ""),
                "has_thumbnail": not v.get("custom_thumbnail", "").endswith("default.svg"),
                "video_size": v.get("video_size"),
            }
    return state


def load_state():
    if not os.path.exists(STATE_PATH):
        return None
    with open(STATE_PATH) as f:
        return json.load(f)


def save_state(channels):
    with open(STATE_PATH, "w") as f:
        json.dump(_build_state(channels), f, indent=2)


def compute_diff(old_state, channels):
    current = _build_state(channels)
    added = {}
    changed = {}
    removed = {}

    for vid, info in current.items():
        if vid not in old_state:
            added[vid] = info
        else:
            old = old_state[vid]
            changes = []
            if info["title"] != old.get("title"):
                changes.append("title changed")
            if info["description_hash"] != old.get("description_hash"):
                changes.append("description changed")
            if info["has_thumbnail"] != old.get("has_thumbnail"):
                changes.append("thumbnail added" if info["has_thumbnail"] else "thumbnail removed")
            if info["video_size"] != old.get("video_size"):
                changes.append("video file changed")
            if changes:
                changed[vid] = {"info": info, "changes": changes}

    for vid, info in old_state.items():
        if vid not in current:
            removed[vid] = info

    return added, changed, removed


def _fmt(info):
    suffix = f" — {info['url']}" if info.get("url") else ""
    return f"{info.get('title') or '(untitled)'}{suffix}"


def print_diff(added, changed, removed):
    if not added and not changed and not removed:
        print("\nNo changes since last run.")
        return
    print(f"\nChanges since last run:")
    if added:
        print(f"  Added ({len(added)}):")
        for info in added.values():
            print(f"    {_fmt(info)}")
    if changed:
        print(f"  Changed ({len(changed)}):")
        for entry in changed.values():
            print(f"    {_fmt(entry['info'])}: {', '.join(entry['changes'])}")
    if removed:
        print(f"  Removed ({len(removed)}):")
        for info in removed.values():
            print(f"    {_fmt(info)}")
