import os
import asyncio
import base64
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sarvamai import AsyncSarvamAI
from dotenv import load_dotenv
import logging

# ────────────── Logging setup ──────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

load_dotenv()

app = FastAPI()
SARVAM_API_KEY = os.getenv("SARVAM_API_KEY")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TranscriptionSession:
    def __init__(self):
        self.client = AsyncSarvamAI(api_subscription_key=SARVAM_API_KEY)
        self.ws_sarvam = None
        self.ws_sarvam_cm = None
        self.websocket = None
        self.audio_task = None
        self.recv_task = None

    async def start(self, data, websocket):
        logger.info("🔗 Starting new Sarvam session...")
        self.websocket = websocket
        #self.ws_sarvam = await self.client.speech_to_text_translate_streaming.connect()
        self.ws_sarvam_cm = self.client.speech_to_text_translate_streaming.connect()
        self.ws_sarvam = await self.ws_sarvam_cm.__aenter__()

        # Open audio file in 'wb' mode to truncate/overwrite
        self.audio_file = open("audio-dump.raw", "wb")

        # Start receiving Sarvam transcripts
        self.recv_task = asyncio.create_task(self.receive_transcripts())

    async def receive_transcripts(self):
        try:
            while True:
                response = await self.ws_sarvam.recv()
                logger.info(f"🔊 response: {response}")

                if response.type == "data" and self.websocket:
                    logger.info(f"🔊 response: {response}")
                    logger.info(f"🔊 transcript type: {type(response.data.transcript)}")
                    logger.info(f"🔊 Received transcript: {response.data.transcript}")
                    await self.websocket.send_json({
                        "type": "transcriber-response",
                        "transcription": response.data.transcript,
                        "channel": "customer"
                    })
                    await self.websocket.send_json({
                        "type": "transcriber-response",
                        "transcription": "Hello",
                        "channel": "assistant"
                    })
              
        except Exception as e:
            logger.error(f"❌ Sarvam receiver error: {e}")

    async def write(self, bytes_data):
        if self.ws_sarvam:
            # Dump audio chunk to file
            if self.audio_file:
                self.audio_file.write(bytes_data)

            # Extract mono (channel 0) from stereo interleaved 16-bit PCM
            mono_bytes = bytearray()
            for i in range(0, len(bytes_data), 4):  # 4 bytes = 2 bytes L + 2 bytes R
                mono_bytes.extend(bytes_data[i:i+2])  # keep only left channel (customer)

            base64_chunk = base64.b64encode(mono_bytes).decode("utf-8")
            await self.ws_sarvam.translate(audio=base64_chunk)


    async def close(self):
        if self.audio_file:
            self.audio_file.close()
        if self.ws_sarvam_cm:
            await self.ws_sarvam_cm.__aexit__(None, None, None)
        if self.recv_task:
            await self.recv_task

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    counter = 0
    await websocket.accept()
    logger.info("🔌 WebSocket connected.")

    session = TranscriptionSession()
    try:
        while True:
            try:
                message = await websocket.receive()
            except RuntimeError:
                logger.warning("⚠️ VAPI disconnected unexpectedly.")
                break

            if "text" in message:
                data = json.loads(message["text"])
                if data.get("type") == "start":
                    await session.start(data, websocket)

            elif "json" in message:
                data = message["json"]
                if data.get("type") == "start":
                    await session.start(data, websocket)

            elif "bytes" in message:
                if counter == 0:
                    await session.websocket.send_json({
                        "type": "transcriber-response",
                        "transcription": "Hello",
                        "channel": "assistant"
                    })
                    counter += 1
                await session.write(message["bytes"])

    except WebSocketDisconnect:
        logger.info("🔌 WebSocket disconnected.")
        await session.close()
