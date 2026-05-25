import json
import sys

args = sys.argv[1:]
no_category = "--no-category" in args
args = [a for a in args if not a.startswith("--")]
catalog_path = args[0] if args else "html/catalog.json"

with open(catalog_path) as f:
    state = json.load(f)

for entry in state.values():
    if no_category and entry.get("categories"):
        continue
    url = entry.get("src_url")
    if url:
        print(url)
