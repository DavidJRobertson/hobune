import json
import sys

state_path = sys.argv[1] if len(sys.argv) > 1 else "hobune_state.json"

with open(state_path) as f:
    state = json.load(f)

for entry in state.values():
    url = entry.get("url")
    if url:
        print(url)
