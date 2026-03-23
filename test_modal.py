import modal
import os
from dotenv import load_dotenv

load_dotenv()

try:
    print("Looking up via Function.from_name...")
    f = modal.Function.from_name("qwen3-news-batch", "NewsProcessor.synthesize")
    print(f"Function found: {f}")
    
    print("\nLooking up via Cls.from_name...")
    c = modal.Cls.from_name("qwen3-news-batch", "NewsProcessor")
    f2 = c.synthesize
    print(f"Cls method found: {f2}")
    
    print("\nSUCCESS")
except Exception as e:
    print(f"\nFAILED: {e}")
