# openai_utils.py
import os
import tempfile
import asyncio
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv(override=True)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)


async def transcribe_audio_bytes(audio_bytes: bytes) -> str:
    """
    Transcribe raw audio bytes using OpenAI's speech-to-text.
    Implementation: writes bytes to a temporary WAV file
    and calls OpenAI transcription (Whisper or gpt-4o-transcribe).
    """
    import aiofiles
    import mimetypes
    from pathlib import Path
    from concurrent.futures import ThreadPoolExecutor

    # Write audio to a temporary wav file
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    tmp.write(audio_bytes)
    tmp.close()

    # Sync function for transcription
    def sync_transcribe(path):
        with open(path, "rb") as f:
            resp = client.audio.transcriptions.create(
                file=f,
                model="gpt-4o-transcribe"
            )
            return resp.text if hasattr(resp, "text") else resp["text"]

    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, sync_transcribe, tmp.name)


async def llm_chat_reply(prompt: str) -> str:
    """
    Send prompt to LLM and return the text reply.
    Uses thread executor to run synchronous OpenAI call safely.
    """
    from concurrent.futures import ThreadPoolExecutor

    def sync_chat(p):
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": p}],
            max_tokens=250
        )
        if hasattr(resp, "choices"):
            return resp.choices[0].message.content
        return resp["choices"][0]["message"]["content"]

    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, sync_chat, prompt)
