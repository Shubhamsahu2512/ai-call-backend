# tts_utils.py
import os
from gtts import gTTS

9


STATIC_DIR = os.path.join("static", "replies") 
os.makedirs(STATIC_DIR, exist_ok=True)

async def synthesize_to_mp3(text: str, filename: str) -> str:
    """Synthesize text to MP3 using gTTS and return full path (relative)."""
    filepath = os.path.join(STATIC_DIR, filename)
    # gTTS is synchronous; run in thread to avoid blocking 
    from concurrent.futures import ThreadPoolExecutor
    def sync_tts(t, p):
        tts = gTTS(text=t, lang='en') 
        tts.save(p)
        return p
    loop = __import__('asyncio').get_running_loop()
    return await loop.run_in_executor(None, sync_tts, text, filepath)