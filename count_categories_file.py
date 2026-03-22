import json
from collections import Counter

try:
    with open('rss_debug_output.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    counts = Counter(item.get('descriptor_category', 'Unknown') for item in data)
    with open('counts.txt', 'w') as f:
        for category, count in counts.items():
            f.write(f"{category}: {count}\n")
        f.write(f"Total: {sum(counts.values())}\n")
except Exception as e:
    with open('counts.txt', 'w') as f:
        f.write(f"Error: {e}\n")
