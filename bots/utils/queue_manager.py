import json

def update_saved_queue(items):
    with open('saved.json', 'w') as f:
        f.write(json.dumps(items, indent=4))

def update_ignored_queue(items):
    with open('ignored.json', 'w') as f:
        f.write(json.dumps(items, indent=4))

def update_skiped_queue(items):
    with open('skiped.json', 'w') as f:
        f.write(json.dumps(items, indent=4))