import modal
import io

# 1. Define the Environment
# We use CUDA 12.4 and Python 3.12 for 2026 compatibility
image = (
    modal.Image.debian_slim(python_version="3.12")
    .apt_install("git", "ffmpeg")
    .pip_install(
        "qwen-tts",  # Official Qwen3-TTS library
        "torch", 
        "torchaudio", 
        "soundfile",
        "huggingface_hub"
    )
)

app = modal.App("qwen3-news-batch")
# Persistent volume to store the 4GB weights
volume = modal.Volume.from_name("qwen3-weights", create_if_missing=True)

@app.cls(
    gpu="L4",                # 24GB VRAM L4 is the most cost-effective for 1.7B models
    image=image,
    volumes={"/cache": volume},
    timeout=1200             # 20 minute timeout for large batches
)
class NewsProcessor:
    @modal.enter()
    def load_model(self):
        import torch
        from qwen_tts import Qwen3TTSModel
        import os
        
        # Use the volume for the model cache
        os.environ["HF_HOME"] = "/cache"
        
        print("🚀 Loading Qwen-3 TTS 1.7B (CustomVoice)...")
        self.model = Qwen3TTSModel.from_pretrained(
            "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice",
            device_map="cuda",
            torch_dtype=torch.bfloat16,
            attn_implementation="sdpa"
        )

    @modal.method()
    def synthesize(self, item: dict):
        """Processes a single headline + 60-word summary"""
        import soundfile as sf
        
        # Using the 'Ryan' speaker profile for English/Euro languages
        # 'Vivian' is recommended for Chinese.
        speaker = "Ryan" if item['lang'] != "Chinese" else "Vivian"
        
        # Instruction for news delivery style
        instruction = "Professional news anchor tone, clear pronunciation, no background noise."
        
        wavs, sr = self.model.generate_custom_voice(
            text=item['text'],
            language=item['lang'],
            speaker=speaker,
            instruct=instruction
        )
        
        # Export as WAV bytes
        buffer = io.BytesIO()
        sf.write(buffer, wavs[0], sr, format="WAV")
        return {"id": item['id'], "audio": buffer.getvalue()}

# C:\Users\Hp\OneDrive\Desktop\SandboxClub\HyPot-News>uv run modal deploy qwen-3-tts-modal.py
# ✓ Created objects.                                                
# ├── 🔨 Created mount                                              
# │   C:\Users\Hp\OneDrive\Desktop\SandboxClub\HyPot-News\qwen-3-tts
# │   -modal.py                                                     
# └── 🔨 Created function NewsProcessor.*.                          
# ✓ App deployed in 4.859s! 🎉

# View Deployment:
# https://modal.com/apps/ryanfernandes23/main/deployed/qwen3-news-ba
# tch