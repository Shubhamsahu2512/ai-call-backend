# # main.py
# import os
# import uuid
# import asyncio
# import json
# import base64

# from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
# from fastapi.responses import PlainTextResponse, FileResponse, JSONResponse
# from pydantic import BaseModel
# from twilio.rest import Client as TwilioClient
# from twilio.twiml.voice_response import VoiceResponse
# from dotenv import load_dotenv

# from openai_utils import transcribe_audio_bytes, llm_chat_reply
# from tts_utils import synthesize_to_mp3
# from save_utils import append_conversation_and_save_excel
# from pydantic import BaseModel
# from typing import Optional
# from fastapi.responses import Response
# from fastapi import WebSocket

# load_dotenv()

# app = FastAPI()

# # Environment variables
# TWILIO_SID = os.getenv("TWILIO_ACCOUNT_SID")
# TWILIO_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
# TWILIO_FROM = os.getenv("TWILIO_NUMBER")
# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# RENDER_BASE_URL = os.getenv("RENDER_BASE_URL")  # required for serving mp3s

# if not (TWILIO_SID and TWILIO_TOKEN and TWILIO_FROM and OPENAI_API_KEY and RENDER_BASE_URL):
#     print("WARNING: One or more env vars missing. Make sure to set them on Render.")

# client = TwilioClient(TWILIO_SID, TWILIO_TOKEN)

# # In-memory store {call_sid: [(speaker, text), ...]}
# CONVERSATIONS = {}


# class StartCallPayload(BaseModel):
#     company: Optional[str] = None
#     agent_type: Optional[str] = None
#     candidate_name: Optional[str] = None
#     candidate_number: Optional[str] = None
#     topic: Optional[str] = None


# @app.get("/")
# def root():
#     return {"status": "ok"}

# @app.post("/start_call")
# async def start_call(payload: StartCallPayload):
#     """
#     Trigger an outbound call using Twilio.
#     """
#     to_number = payload.candidate_number
#     try:
#         call = client.calls.create(
#             to=to_number,
#             from_=TWILIO_FROM,
#             url=f"{RENDER_BASE_URL}/twilio/voice"
#         )

#         CONVERSATIONS[call.sid] = []
#         return JSONResponse({"status": "ok", "call_sid": call.sid})

#     except Exception as e:
#         return JSONResponse(
#             {"status": "error", "message": str(e)},
#             status_code=500
#         )


# # @app.post("/twilio/voice")
# # async def twilio_voice(request: Request):
# #     """
# #     Twilio hits this endpoint when the call is answered.
# #     We reply with TwiML that begins a Media Stream + greeting.
# #     """
# #     vr = VoiceResponse()

# #     # Convert https:// → wss://
# #     stream_url = RENDER_BASE_URL.replace("https://", "wss://") + "/media"

# #     vr.start().stream(url=stream_url)
# #     vr.say("Hello. This is an automated interviewer. I will ask a few questions.")
# #     vr.pause(length=1)
# #     vr.say("Please say your name after the beep.")

# #     return PlainTextResponse(str(vr), media_type="application/xml")

# # @app.post("/twilio/voice")
# # async def twilio_voice():
# #     """
# #     Twilio will POST here when the call is answered.
# #     We respond with TwiML that starts a Media Stream to our /media websocket.
# #     """
# #     # Build the wss stream URL Twilio should connect to
# #     # If RENDER_BASE_URL = "https://ai-call-backend-waxe.onrender.com"
# #     # we replace https:// with wss:// and append /media
# #     stream_url = RENDER_BASE_URL.replace("https://", "wss://").rstrip("/") + "/media"

# #     vr = VoiceResponse()
# #     # start streaming audio to our websocket
# #     vr.start().stream(url=stream_url)
# #     # Optional initial speech to candidate
# #     vr.say("Hello. This is an automated interviewer. Please wait while I connect.")
# #     return PlainTextResponse(str(vr), media_type="application/xml")


# # @app.post("/twilio/voice")
# # async def twilio_voice():
# #     twiml = """
# #         <?xml version="1.0" encoding="UTF-8"?>
# #         <Response>
# #             <Start>
# #                 <Stream url="wss://ai-call-backend-waxe.onrender.com/media" />
# #             </Start>
# #             <Say>Hello. This is an automated interviewer. Please wait while I connect.</Say>
# #         </Response>
# #     """
# #     return Response(content=twiml, media_type="application/xml")

# @app.post("/twilio/voice")
# async def twilio_voice():
#     stream_url = RENDER_BASE_URL.replace("https://", "wss://").rstrip("/") + "/media"

#     vr = VoiceResponse()
#     vr.start().stream(url=stream_url)
#     vr.say("Hello. This is an automated interviewer. Please wait while I connect.")
    
#     return PlainTextResponse(str(vr), media_type="application/xml")

# # @app.websocket("/media")
# # async def media_ws(websocket: WebSocket):
# #     """
# #     Receive Twilio Media Stream websocket events.
# #     """
# #     await websocket.accept()
# #     print("Websocket connected: Twilio Media Stream")

# #     call_sid = str(uuid.uuid4())
# #     audio_buffer = bytearray()

# #     try:
# #         while True:
# #             msg = await websocket.receive_text()
# #             data = json.loads(msg)
# #             event = data.get("event")

# #             # ---- CONNECTED ----
# #             if event == "connected":
# #                 print("Connected:", data)
# #                 call_sid = data.get("start", {}).get("callSid", call_sid)
# #                 CONVERSATIONS.setdefault(call_sid, [])

# #             # ---- AUDIO MEDIA ----
# #             elif event == "media":
# #                 media = data.get("media", {})
# #                 payload_b64 = media.get("payload")

# #                 if payload_b64:
# #                     chunk = base64.b64decode(payload_b64)
# #                     audio_buffer.extend(chunk)

# #                 # Flush after ~4 seconds of audio
# #                 if len(audio_buffer) > 16000 * 4:
# #                     audio_bytes = bytes(audio_buffer)
# #                     audio_buffer.clear()

# #                     # Transcribe
# #                     try:
# #                         transcription = await transcribe_audio_bytes(audio_bytes)
# #                     except Exception as e:
# #                         transcription = f"(transcription error: {e})"

# #                     print("Transcribed:", transcription)
# #                     CONVERSATIONS[call_sid].append(("candidate", transcription))

# #                     # LLM reply
# #                     prompt = f"You are an interviewer. Candidate said: {transcription}. Reply succinctly and ask the next question."
# #                     reply = await llm_chat_reply(prompt)
# #                     CONVERSATIONS[call_sid].append(("agent", reply))

# #                     # TTS
# #                     mp3_filename = f"{call_sid}_{uuid.uuid4().hex}.mp3"
# #                     mp3_path = await synthesize_to_mp3(reply, mp3_filename)

# #                     public_url = f"{RENDER_BASE_URL}/static/replies/{mp3_filename}"

# #                     # Try Twilio playback
# #                     try:
# #                         if call_sid.startswith("CA"):
# #                             play_twiml = f"<Response><Play>{public_url}</Play></Response>"
# #                             client.calls(call_sid).update(twiml=play_twiml)
# #                         else:
# #                             print("Unknown Twilio SID. Manual playback:", public_url)
# #                     except Exception as e:
# #                         print("Twilio playback error:", e)

# #             # ---- STOP EVENT ----
# #             elif event == "stop":
# #                 print("Stream stopped")
# #                 break

# #     except WebSocketDisconnect:
# #         print("WebSocket disconnected")

# #     finally:
# #         # Save conversation to Excel
# #         try:
# #             filename = f"call_{call_sid}.xlsx"
# #             append_conversation_and_save_excel(CONVERSATIONS.get(call_sid, []), filename)
# #             print("Saved:", filename)
# #         except Exception as e:
# #             print("Excel save error:", e)



# @app.websocket("/media")
# async def media_stream(websocket: WebSocket):
#     await websocket.accept()
#     print("🔵 Twilio connected to WebSocket!")

#     try:
#         while True:
#             data = await websocket.receive_text()
#             print("Received:", data)
#     except Exception as e:
#         print("❌ WebSocket closed:", e)


# @app.get("/static/replies/{filename}")
# async def serve_reply_file(filename: str):
#     filepath = os.path.join("static", "replies", filename)
#     if os.path.exists(filepath):
#         return FileResponse(filepath, media_type="audio/mpeg")
#     return JSONResponse({"error": "Not found"}, status_code=404)


# @app.get("/download/{call_sid}")
# async def download_conversation(call_sid: str):
#     filename = f"call_{call_sid}.xlsx"
#     if os.path.exists(filename):
#         return FileResponse(
#             filename,
#             media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
#         )
#     return JSONResponse({"error": "not found"}, status_code=404)
# main.py
import os
import uuid
import asyncio
import json
import base64
import requests

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import PlainTextResponse, FileResponse, JSONResponse, Response
from pydantic import BaseModel
from typing import Optional
from twilio.rest import Client as TwilioClient
from twilio.twiml.voice_response import VoiceResponse
from dotenv import load_dotenv

from openai import OpenAI
client = OpenAI()

load_dotenv()

app = FastAPI()

# Environment variables
TWILIO_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_FROM = os.getenv("TWILIO_NUMBER")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
RENDER_BASE_URL = os.getenv("RENDER_BASE_URL")

if not (TWILIO_SID and TWILIO_TOKEN and TWILIO_FROM and OPENAI_API_KEY and RENDER_BASE_URL):
    print("WARNING: Missing environment variables!")

twilio_client = TwilioClient(TWILIO_SID, TWILIO_TOKEN)

# In-memory store
CONVERSATIONS = {}

class StartCallPayload(BaseModel):
    company: Optional[str] = None
    agent_type: Optional[str] = None
    candidate_name: Optional[str] = None
    candidate_number: Optional[str] = None
    topic: Optional[str] = None


@app.get("/")
def root():
    return {"status": "ok"}


# -----------------------------------------------------------
# 1. START OUTBOUND CALL
# -----------------------------------------------------------
@app.post("/start_call")
async def start_call(payload: StartCallPayload):
    try:
        call = twilio_client.calls.create(
            to=payload.candidate_number,
            from_=TWILIO_FROM,
            url=f"{RENDER_BASE_URL}/twilio/voice"
        )
        CONVERSATIONS[call.sid] = []
        return {"status": "ok", "call_sid": call.sid}

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


# -----------------------------------------------------------
# 2. TWILIO CALL ANSWERED → SEND GREETING + RECORD
# -----------------------------------------------------------
@app.post("/twilio/voice")
async def twilio_voice():
    """
    Initial TwiML when call is answered — NO WebSocket (Free Plan).
    """
    twiml = f"""
    <Response>
        <Say>Hello. This is an automated interviewer. Please wait while I connect.</Say>
        <Record action="{RENDER_BASE_URL}/twilio/process"
                method="POST"
                maxLength="15"
                playBeep="true" />
    </Response>
    """
    return Response(content=twiml, media_type="application/xml")


# -----------------------------------------------------------
# 3. PROCESS RECORDED AUDIO → TRANSCRIBE → LLM → TTS → PLAY
# -----------------------------------------------------------
@app.post("/twilio/process")
async def twilio_process(request: Request):

    form = await request.form()
    recording_url = form.get("RecordingUrl")

    if not recording_url:
        return Response("<Response><Say>Error: No recording.</Say></Response>", media_type="application/xml")

    # Download audio
    audio_bytes = requests.get(recording_url + ".wav").content
    with open("input.wav", "wb") as f:
        f.write(audio_bytes)

    # Transcribe
    transcript = client.audio.transcriptions.create(
        model="gpt-4o-mini-tts",
        file=open("input.wav", "rb")
    )
    user_text = transcript.text

    # LLM reply
    reply = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": user_text}]
    )
    answer = reply.choices[0].message["content"]

    # Convert reply → speech
    tts_audio = client.audio.speech.create(
        model="gpt-4o-mini-tts",
        voice="alloy",
        input=answer
    )
    with open("reply.mp3", "wb") as f:
        f.write(tts_audio)

    # Build URL for Twilio to fetch the audio
    audio_url = f"{RENDER_BASE_URL}/reply.mp3"

    # TwiML: Play the reply and record again
    twiml = f"""
    <Response>
        <Play>{audio_url}</Play>
        <Record action="{RENDER_BASE_URL}/twilio/process"
                method="POST"
                maxLength="15"
                playBeep="true" />
    </Response>
    """

    return Response(content=twiml, media_type="application/xml")


# -----------------------------------------------------------
# 4. STATIC ROUTE FOR reply.mp3
# -----------------------------------------------------------
@app.get("/reply.mp3")
async def serve_audio():
    return FileResponse("reply.mp3", media_type="audio/mpeg")
