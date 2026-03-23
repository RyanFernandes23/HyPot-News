import modal
import os
from src.core.config import settings

def test_consistency():
    print("🚀 Connecting to Modal app 'qwen3-news-batch'...")
    try:
        processor_cls = modal.Cls.from_name("qwen3-news-batch", "NewsProcessor")
        processor = processor_cls()
        
        test_items = [
            {
                "id": "test-1",
                "text": "The Federal Reserve announced a surprising interest rate hike today, impacting global markets.",
                "lang": "English"
            },
            {
                "id": "test-2",
                "text": "In other news, a rare species of butterfly was discovered in the Amazon rainforest after fifty years.",
                "lang": "English"
            },
            {
                "id": "test-3",
                "text": "Sports update: The championship game concluded with a last-minute goal, securing the victory.",
                "lang": "English"
            }
        ]
        
        print(f"📊 Running synthesis for {len(test_items)} test items...")
        results = list(processor.synthesize.map(test_items))
        
        for res in results:
            audio_len = len(res['audio'])
            print(f"✅ Received audio for {res['id']}: {audio_len} bytes")
            # Save a sample to check
            with open(f"temp_audio/test_consistency_{res['id']}.wav", "wb") as f:
                f.write(res['audio'])
        
        print("\n✨ Verification script completed. Check temp_audio/ for results.")
        
    except Exception as e:
        print(f"❌ Error during verification: {e}")

if __name__ == "__main__":
    os.makedirs("temp_audio", exist_ok=True)
    test_consistency()
