import json
import sys

catalog_path = sys.argv[1] if len(sys.argv) > 1 else "html/catalog.json"

with open(catalog_path) as f:
    state = json.load(f)

for entry in state.values():
    url = entry.get("src_url")
    if url:
        print(url)
