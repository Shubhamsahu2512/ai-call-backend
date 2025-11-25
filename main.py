# import os
# import uuid
# import io
# from fastapi import FastAPI, Request
# from fastapi.responses import FileResponse, JSONResponse, Response
# from pydantic import BaseModel
# from typing import Optional
# from twilio.rest import Client as TwilioClient
# from dotenv import load_dotenv
# from openai import OpenAI
# from requests.auth import HTTPBasicAuth
# import requests

# # --- Patch pydub for Python 3.13 ---
# import types
# import sys
# fake_audioop = types.SimpleNamespace()
# sys.modules['pyaudioop'] = fake_audioop

# from pydub import AudioSegment
# import imageio_ffmpeg as ffmpeg
# AudioSegment.converter = ffmpeg.get_ffmpeg_exe()

# # ---------------- App & Environment ----------------
# load_dotenv()
# app = FastAPI()

# TWILIO_SID = os.getenv("TWILIO_ACCOUNT_SID")
# TWILIO_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
# TWILIO_FROM = os.getenv("TWILIO_NUMBER")
# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# RENDER_BASE_URL = os.getenv("RENDER_BASE_URL")

# if not (TWILIO_SID and TWILIO_TOKEN and TWILIO_FROM and OPENAI_API_KEY and RENDER_BASE_URL):
#     print("⚠ WARNING: Some environment variables are missing!")

# twilio_client = TwilioClient(TWILIO_SID, TWILIO_TOKEN)
# client = OpenAI(api_key=OPENAI_API_KEY)

# # ---------------- Models ----------------
# class StartCallPayload(BaseModel):
#     company: Optional[str] = None
#     agent_type: Optional[str] = None
#     candidate_name: Optional[str] = None
#     candidate_number: Optional[str] = None
#     topic: Optional[str] = None

# # ---------------- Root ----------------
# @app.get("/")
# def root():
#     return {"status": "ok"}

# # ---------------- Start call ----------------
# @app.post("/start_call")
# async def start_call(payload: StartCallPayload):
#     try:
#         call = twilio_client.calls.create(
#             to=payload.candidate_number,
#             from_=TWILIO_FROM,
#             url=f"{RENDER_BASE_URL}/twilio/voice"
#         )
#         return {"status": "ok", "call_sid": call.sid}
#     except Exception as e:
#         return JSONResponse({"error": str(e)}, status_code=500)

# # ---------------- Twilio voice endpoint ----------------
# @app.post("/twilio/voice")
# async def twilio_voice():
#     twiml = f"""
#     <Response>
#         <Say>Hello. This is an automated interviewer. Please wait while I connect.</Say>
#         <Record action="{RENDER_BASE_URL}/twilio/process"
#                 method="POST"
#                 maxLength="15"
#                 playBeep="true" />
#     </Response>
#     """
#     return Response(content=twiml.strip(), media_type="application/xml")

# # ---------------- Twilio process endpoint ----------------
# @app.post("/twilio/process")
# async def twilio_process(request: Request):
#     form = await request.form()
#     recording_sid = form.get("RecordingSid")

#     if not recording_sid:
#         return Response("<Response><Say>No recording received.</Say></Response>", media_type="application/xml")

#     uid = uuid.uuid4().hex
#     input_file = f"input_{uid}.wav"
#     reply_file = f"reply_{uid}.mp3"

#     # --- Download Twilio recording robustly ---
#     try:
#         recording_url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_SID}/Recordings/{recording_sid}.wav"
#         resp = requests.get(recording_url, auth=HTTPBasicAuth(TWILIO_SID, TWILIO_TOKEN), timeout=10)
#         resp.raise_for_status()
#         audio_bytes = resp.content
#     except Exception as e:
#         print("Error downloading Twilio audio:", e)
#         return Response("<Response><Say>Failed to download recording.</Say></Response>", media_type="application/xml")

#     # --- Convert to standard WAV using pydub + ffmpeg ---
#     try:
#         audio = AudioSegment.from_file(io.BytesIO(audio_bytes))
#         audio.export(input_file, format="wav")
#     except Exception as e:
#         print("Error processing audio with pydub:", e)
#         return Response("<Response><Say>Failed to process audio.</Say></Response>", media_type="application/xml")

#     # --- Transcribe using OpenAI Whisper ---
#     try:
#         with open(input_file, "rb") as audio_file:
#             transcript = client.audio.transcriptions.create(
#                 model="whisper-1",
#                 file=audio_file
#             )
#         user_text = transcript.text
#         print("📝 TRANSCRIPT:", user_text)
#     except Exception as e:
#         print("OpenAI transcription error:", e)
#         user_text = "(transcription failed)"

#     # --- Generate LLM reply ---
#     try:
#         reply = client.chat.completions.create(
#             model="gpt-4o-mini",
#             messages=[
#                 {"role": "system", "content": "You are an AI interviewer."},
#                 {"role": "user", "content": user_text}
#             ]
#         )
#         answer = reply.choices[0].message["content"]
#         print("🤖 AGENT:", answer)
#     except Exception as e:
#         print("OpenAI chat error:", e)
#         answer = "Sorry, I could not generate a reply."

#     # --- Convert LLM reply to speech (TTS) ---
#     try:
#         tts_audio = client.audio.speech.create(
#             model="gpt-4o-mini-tts",
#             voice="alloy",
#             input=answer
#         )
#         with open(reply_file, "wb") as f:
#             f.write(tts_audio)
#     except Exception as e:
#         print("TTS generation error:", e)
#         return Response("<Response><Say>Failed to generate audio reply.</Say></Response>", media_type="application/xml")

#     audio_url = f"{RENDER_BASE_URL}/{reply_file}"

#     # --- Respond to Twilio with playback + next record ---
#     twiml = f"""
#     <Response>
#         <Play>{audio_url}</Play>
#         <Record action="{RENDER_BASE_URL}/twilio/process"
#                 method="POST"
#                 maxLength="15"
#                 playBeep="true" />
#     </Response>
#     """
#     return Response(content=twiml.strip(), media_type="application/xml")

# # ---------------- Serve TTS audio ----------------
# @app.get("/{filename}")
# async def serve_tts_audio(filename: str):
#     if os.path.exists(filename):
#         return FileResponse(filename, media_type="audio/mpeg")
#     return JSONResponse({"error": "file not found"}, status_code=404)


import os
import uuid
import io
import time
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse, Response
from pydantic import BaseModel
from typing import Optional
from twilio.rest import Client as TwilioClient
from dotenv import load_dotenv
from openai import OpenAI
from requests.auth import HTTPBasicAuth
import requests

# --- Patch pydub for Python 3.13 ---
import types
import sys
fake_audioop = types.SimpleNamespace()
sys.modules['pyaudioop'] = fake_audioop

from pydub import AudioSegment
import imageio_ffmpeg as ffmpeg
AudioSegment.converter = ffmpeg.get_ffmpeg_exe()

# ---------------- App & Environment ----------------
load_dotenv()
app = FastAPI()

TWILIO_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_FROM = os.getenv("TWILIO_NUMBER")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
RENDER_BASE_URL = os.getenv("RENDER_BASE_URL")

if not (TWILIO_SID and TWILIO_TOKEN and TWILIO_FROM and OPENAI_API_KEY and RENDER_BASE_URL):
    print("⚠ WARNING: Some environment variables are missing!")

twilio_client = TwilioClient(TWILIO_SID, TWILIO_TOKEN)
client = OpenAI(api_key=OPENAI_API_KEY)

# ---------------- Models ----------------
class StartCallPayload(BaseModel):
    company: Optional[str] = None
    agent_type: Optional[str] = None
    candidate_name: Optional[str] = None
    candidate_number: Optional[str] = None
    topic: Optional[str] = None

# ---------------- Root ----------------
@app.get("/")
def root():
    return {"status": "ok"}

# ---------------- Start call ----------------
@app.post("/start_call")
async def start_call(payload: StartCallPayload):
    try:
        call = twilio_client.calls.create(
            to=payload.candidate_number,
            from_=TWILIO_FROM,
            url=f"{RENDER_BASE_URL}/twilio/voice"
        )
        return {"status": "ok", "call_sid": call.sid}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

# ---------------- Twilio voice endpoint ----------------
@app.post("/twilio/voice")
async def twilio_voice():
    twiml = f"""
    <Response>
        <Say>Hello. This is an automated interviewer. Please wait while I connect.</Say>
        <Record action="{RENDER_BASE_URL}/twilio/process"
                method="POST"
                maxLength="15"
                playBeep="true" />
    </Response>
    """
    return Response(content=twiml.strip(), media_type="application/xml")

# ---------------- Recording Download Helper ----------------
def download_twilio_recording(recording_sid: str):
    """
    Attempts to download Twilio recording with retry logic.
    """
    recording_url = (
        f"https://api.twilio.com/2010-04-01/Accounts/"
        f"{TWILIO_SID}/Recordings/{recording_sid}"
    )

    for attempt in range(5):  # retry up to 5 times
        print(f"Download attempt {attempt + 1}/5 → {recording_url}")

        resp = requests.get(
            recording_url,
            auth=HTTPBasicAuth(TWILIO_SID, TWILIO_TOKEN),
            timeout=10
        )

        if resp.status_code == 200:
            print("Recording downloaded successfully.")
            return resp.content

        print(f"Recording not ready yet: HTTP {resp.status_code}")
        time.sleep(1.2)

    raise Exception(f"Recording still unavailable after retries. Last status={resp.status_code}")

# ---------------- Twilio process endpoint ----------------
@app.post("/twilio/process")
async def twilio_process(request: Request):
    form = await request.form()
    recording_sid = form.get("RecordingSid")

    if not recording_sid:
        return Response("<Response><Say>No recording received.</Say></Response>", media_type="application/xml")

    uid = uuid.uuid4().hex
    input_file = f"input_{uid}.wav"
    reply_file = f"reply_{uid}.mp3"

    # --- Download Twilio recording robustly ---
    try:
        audio_bytes = download_twilio_recording(recording_sid)
    except Exception as e:
        print("❌ Error downloading Twilio audio:", e)
        return Response("<Response><Say>Failed to download recording.</Say></Response>", media_type="application/xml")

    # --- Convert Twilio audio → WAV ---
    try:
        audio = AudioSegment.from_file(io.BytesIO(audio_bytes))
        audio.export(input_file, format="wav")
    except Exception as e:
        print("❌ Error processing audio with pydub:", e)
        return Response("<Response><Say>Failed to process audio.</Say></Response>", media_type="application/xml")

    # --- Transcribe using OpenAI Whisper ---
    try:
        with open(input_file, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
        user_text = transcript.text
        print("📝 TRANSCRIPT:", user_text)
    except Exception as e:
        print("❌ OpenAI transcription error:", e)
        user_text = "(transcription failed)"

    # --- Generate LLM reply ---
    try:
        reply = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an AI interviewer."},
                {"role": "user", "content": user_text}
            ]
        )
        answer = reply.choices[0].message["content"]
        print("🤖 AGENT:", answer)
    except Exception as e:
        print("❌ OpenAI chat error:", e)
        answer = "Sorry, I could not generate a reply."

    # --- Convert LLM reply to speech ---
    try:
        tts_audio = client.audio.speech.create(
            model="gpt-4o-mini-tts",
            voice="alloy",
            input=answer
        )
        with open(reply_file, "wb") as f:
            f.write(tts_audio)  # raw bytes
    except Exception as e:
        print("❌ TTS generation error:", e)
        return Response("<Response><Say>Failed to generate audio reply.</Say></Response>", media_type="application/xml")

    audio_url = f"{RENDER_BASE_URL}/{reply_file}"

    # --- Respond to Twilio with playback + next record ---
    twiml = f"""
    <Response>
        <Play>{audio_url}</Play>
        <Record action="{RENDER_BASE_URL}/twilio/process"
                method="POST"
                maxLength="15"
                playBeep="true" />
    </Response>
    """
    return Response(content=twiml.strip(), media_type="application/xml")

# ---------------- Serve TTS audio ----------------
@app.get("/{filename}")
async def serve_tts_audio(filename: str):
    if os.path.exists(filename):
        return FileResponse(filename, media_type="audio/mpeg")
    return JSONResponse({"error": "file not found"}, status_code=404)

