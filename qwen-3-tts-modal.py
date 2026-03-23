import modal
import io

# 1. Define the Environment
image = (
    modal.Image.debian_slim(python_version="3.12")
    .apt_install("git", "ffmpeg", "sox", "build-essential", "ninja-build")
    .pip_install(
        "qwen-tts",
        "torch",
        "torchaudio",
        "soundfile",
        "huggingface_hub",
        "packaging"
    )
)

app = modal.App("qwen3-news-batch")
# Persistent volume to store the 4GB weights
volume = modal.Volume.from_name("qwen3-weights", create_if_missing=True)

@app.cls(
    gpu="L4",                # Native bfloat16 support, better than T4 for this model
    image=image,
    volumes={"/cache": volume},
    timeout=1200,            # 20 minute timeout for large batches
    max_containers=3         # Limit to 3 parallel GPUs
)
class NewsProcessor:
    @modal.enter()
    def load_model(self):
        import torch
        from qwen_tts import Qwen3TTSModel
        import os
        
        os.environ["HF_HOME"] = "/cache"
        
        print("🚀 Loading Qwen-3 TTS 1.7B (CustomVoice)...")
        self.model = Qwen3TTSModel.from_pretrained(
            "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice",
            device_map="cuda",
            dtype=torch.bfloat16,       # L4 handles this natively
            attn_implementation="sdpa"  # PyTorch built-in, no flash-attn needed
        )

    @modal.method()
    def synthesize(self, item: dict):
        """Processes a single headline + 60-word summary with high consistency"""
        import soundfile as sf
        
        text = item['text']
        speaker = "Ryan"
        language = "English"
        
        instruction = (
            "A professional male news anchor with a consistent, neutral American accent. "
            "Tone: authoritative, formal, and clear. Emotion: neutral. "
            "Style: standard news broadcast delivery. No vocal variety or excitement."
        )
        
        wavs, sr = self.model.generate_custom_voice(
            text=text,
            language=language,
            speaker=speaker,
            instruct=instruction
        )
        
        # Export as WAV bytes
        buffer = io.BytesIO()
        sf.write(buffer, wavs[0], sr, format="WAV")
        return {"id": item['id'], "audio": buffer.getvalue()}