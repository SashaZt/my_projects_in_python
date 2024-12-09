from __future__ import annotations

import asyncio
import json
import logging
import threading
import uuid
from dataclasses import asdict, dataclass
from enum import Enum
from functools import partial
from typing import Any, Dict, Literal, Optional

import whisper
from livekit import api, rtc
from livekit.agents import (
    AutoSubscribe,
    JobContext,
    WorkerOptions,
    WorkerType,
    cli,
    llm,
)
from livekit.agents.multimodal import MultimodalAgent
from livekit.api import DeleteRoomRequest, ListParticipantsRequest
from livekit.plugins import openai

logger = logging.getLogger("my-worker")
logger.setLevel(logging.INFO)

# Whisper model initialization
whisper_model = whisper.load_model(
    "base"
)  # Choose model size: "tiny", "base", "small", "medium", "large"


class ResettableTimeout:
    def __init__(self, timeout, callback, *args, **kwargs):
        self.timeout = timeout
        self.callback = partial(callback, *args, **kwargs)
        self.timer = None

    def start(self):
        logger.info("restart silence timeout")
        self.cancel()
        self.timer = threading.Timer(self.timeout, self.callback)
        self.timer.start()

    def cancel(self):
        if self.timer is not None:
            self.timer.cancel()
            self.timer = None


@dataclass
class SessionConfig:
    openai_api_key: str
    instructions: str
    voice: openai.realtime.api_proto.Voice
    temperature: float
    max_response_output_tokens: str | int
    modalities: list[openai.realtime.api_proto.Modality]
    turn_detection: openai.realtime.ServerVadOptions
    current_user: list[str]
    selected_timeslots: list

    def __post_init__(self):
        if self.modalities is None:
            self.modalities = self._modalities_from_string("text_and_audio")

    def to_dict(self):
        return {k: v for k, v in asdict(self).items() if k != "openai_api_key"}

    @staticmethod
    def _modalities_from_string(modalities: str) -> list[str]:
        modalities_map = {
            "text_and_audio": ["text", "audio"],
            "text_only": ["text"],
        }
        return modalities_map.get(modalities, ["text", "audio"])

    def __eq__(self, other: SessionConfig) -> bool:
        return self.to_dict() == other.to_dict()


async def transcribe_with_whisper(audio_chunk: bytes) -> str:
    """Transcribe audio chunk to text using Whisper."""
    with open("temp_audio.wav", "wb") as f:
        f.write(audio_chunk)
    result = whisper_model.transcribe("temp_audio.wav")
    return result.get("text", "")


async def start_recording(ctx: JobContext):
    content = ""
    with open("./gsp_credentials.json", "r") as f:
        content = f.read()

    file_encoded_output = api.EncodedFileOutput(
        filepath=f"livekit-{ctx.room.name}/",
        gcp=api.GCPUpload(
            credentials=content,
            bucket="curaay",
        ),
    )
    req = api.RoomCompositeEgressRequest(
        room_name=ctx.room.name,
        file_outputs=[file_encoded_output],
    )

    lkapi = api.LiveKitAPI()
    res = await lkapi.egress.start_room_composite_egress(req)
    logger.info(f"egress response: {res}")
    return res


async def handle_audio_stream(audio_stream):
    """Handle audio stream: Whisper -> LLM -> TTS."""
    async for audio_chunk in audio_stream:
        # Use Whisper to transcribe audio
        input_text = await transcribe_with_whisper(audio_chunk)
        if not input_text:
            logger.warning("Whisper transcription failed.")
            continue

        # Generate response with LLM
        response_text = await llm.generate(input_text)

        # Optionally handle TTS or other steps here
        # Example: yield synthesized response audio
        # async for tts_chunk in tts.synthesize(response_text):
        #     yield tts_chunk


async def entrypoint(ctx: JobContext):
    logger.info(f"connecting to room {ctx.room.name}")
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    participant = await ctx.wait_for_participant()

    egress_response = await start_recording(ctx)
    egress_id = egress_response.egress_id
    egress_file = egress_response.file.filename

    # Run multimodal agent
    run_multimodal_agent(ctx, participant, egress_id, egress_file)

    logger.info(f"agent started with egress {egress_id} {egress_file}")


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, worker_type=WorkerType.ROOM))
