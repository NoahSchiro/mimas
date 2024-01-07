import json

def save_json(fp, obj):
    with open(fp, "w") as f:
        json.dump(obj, f, indent=2)

def load_json(fp):
    with open(fp, "r") as f:
        return json.load(f)

