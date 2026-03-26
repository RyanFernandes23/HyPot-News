
import asyncio
import os
import sys

# Add src to path if needed
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.db.supabase import supabase_service

async def verify_db_counts():
    print("Verifying database counts per category...")
    try:
        response = supabase_service.table("news_articles") \
            .select("category") \
            .execute()
        
        from collections import Counter
        counts = Counter(item["category"] for item in response.data)
        
        print("\nCounts per category in database:")
        categories = ["International", "Finance", "Hot Topics", "Good News"]
        for category in categories:
            count = counts.get(category, 0)
            status = "✅" if count <= 10 else "❌"
            print(f"{status} {category}: {count}")
        
        total = sum(counts.values())
        print(f"\nTotal articles in DB: {total}")
        
    except Exception as e:
        print(f"Error during verification: {e}")

if __name__ == "__main__":
    asyncio.run(verify_db_counts())
