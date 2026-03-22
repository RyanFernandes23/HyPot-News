import json
from collections import Counter

try:
    with open('rss_debug_output.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    counts = Counter(item.get('descriptor_category', 'Unknown') for item in data)
    print("Counts per category in rss_debug_output.json:")
    for category, count in counts.items():
        print(f"- {category}: {count}")
    print(f"Total articles: {sum(counts.values())}")
except Exception as e:
    print(f"Error: {e}")
