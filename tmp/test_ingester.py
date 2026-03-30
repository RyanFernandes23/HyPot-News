import sys
import os

# Add the project root to sys.path
sys.path.append(os.getcwd())

from src.services.rss.ingester import map_entry_to_article

test_entries = [
    {"published_at": ""},
    {"published": ""},
    {"published_at": " ", "published": None},
    {"published_at": None, "published": ""},
]

print("Testing map_entry_to_article with empty strings...")
for i, entry in enumerate(test_entries):
    result = map_entry_to_article(entry)
    print(f"Test {i}: published_at = {result['published_at']!r}")

print("\nTesting with valid date...")
entry = {"published_at": "2024-03-29T12:00:00Z"}
result = map_entry_to_article(entry)
print(f"Valid date: {result['published_at']!r}")
