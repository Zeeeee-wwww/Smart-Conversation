# -*- coding: utf-8 -*-

import base64
import threading
import time

import dashscope
import pyaudio
from dashscope.audio.qwen_omni import (
    AudioFormat,
    MultiModality,
    OmniRealtimeCallback,
    OmniRealtimeConversation,
)
from dashscope.audio.qwen_omni.omni_realtime import TranscriptionParams


# === 配置 ===
dashscope.api_key = "sk-13f23215997b46c39be9b3adb641d85b"
URL = "wss://dashscope.aliyuncs.com/api-ws/v1/realtime"
MODEL = "qwen3.5-omni-plus-realtime"

MIC_SAMPLE_RATE = 16000
SPEAKER_SAMPLE_RATE = 24000
MIC_CHANNELS = 1
MIC_FRAMES_PER_BUFFER = 640  # 40ms，缩短单包长度以减少回采泄漏
PLAYBACK_COOLDOWN_SEC = 0.8  # 扬声器播放完成后，额外等待一段时间再恢复上行


class DuplexGate:
    """Control when microphone audio is allowed to go upstream."""

    def __init__(self):
        self._lock = threading.Lock()
        self.block_mic_until = 0.0

    def block_for_audio_chunk(self, seconds: float) -> None:
        with self._lock:
            now = time.monotonic()
            self.block_mic_until = max(self.block_mic_until, now) + seconds

    def add_cooldown(self, seconds: float) -> None:
        with self._lock:
            self.block_mic_until = max(self.block_mic_until, time.monotonic()) + seconds

    def should_upload_mic(self) -> bool:
        with self._lock:
            return time.monotonic() >= self.block_mic_until


class MyCallback(OmniRealtimeCallback):
    def __init__(self, duplex_gate: DuplexGate):
        self.duplex_gate = duplex_gate
        self.pya = None
        self.stream_out = None
        self.last_assistant_text = ""

    def on_open(self):
        self.pya = pyaudio.PyAudio()
        self.stream_out = self.pya.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=SPEAKER_SAMPLE_RATE,
            output=True,
        )

    def on_event(self, response):
        event_type = response.get("type")

        if event_type == "input_audio_buffer.speech_started":
            print("\n[Mic] 检测到用户开始说话")

        elif event_type == "conversation.item.input_audio_transcription.completed":
            transcript = response.get("transcript", "")
            if transcript:
                print(f"\n[User] {transcript}")

        elif event_type == "response.audio_transcript.delta":
            delta = response.get("delta", "")
            if delta:
                print(delta, end="", flush=True)
                self.last_assistant_text += delta

        elif event_type == "response.audio.delta":
            audio_bytes = base64.b64decode(response["delta"])
            # 模型开始播报后，立刻阻断麦克风上行，避免扬声器回采被送回服务端。
            chunk_duration = len(audio_bytes) / (SPEAKER_SAMPLE_RATE * 2)
            self.duplex_gate.block_for_audio_chunk(chunk_duration)

            if self.stream_out and not self.stream_out.is_stopped():
                self.stream_out.write(audio_bytes)

        elif event_type == "response.done":
            # 最后一个音频块播完后，再额外保留一小段冷却时间，减少房间反射和尾音误触发。
            self.duplex_gate.add_cooldown(PLAYBACK_COOLDOWN_SEC)
            if self.last_assistant_text:
                print()
                self.last_assistant_text = ""

    def on_close(self, code, reason):
        if self.stream_out:
            self.stream_out.close()
        if self.pya:
            self.pya.terminate()


if __name__ == "__main__":
    duplex_gate = DuplexGate()
    callback = MyCallback(duplex_gate)

    conv = OmniRealtimeConversation(
        model=MODEL,
        url=URL,
        callback=callback,
    )

    mic_stream = None
    p = None

    try:
        conv.connect()
        conv.update_session(
            output_modalities=[MultiModality.AUDIO, MultiModality.TEXT],
            voice="Ethan",
            instructions="你是阿里云 Qwen 语音助手，请简洁、自然地回答。",
            input_audio_format=AudioFormat.PCM_16000HZ_MONO_16BIT,
            output_audio_format=AudioFormat.PCM_24000HZ_MONO_16BIT,
            enable_input_audio_transcription=True,
            enable_turn_detection=True,
            turn_detection_type="server_vad",
            turn_detection_threshold=0.72,
            turn_detection_silence_duration_ms=1200,
            turn_detection_param={
                "create_response": True,
                "interrupt_response": False,
            },
            transcription_params=TranscriptionParams(
                language="zh",
                sample_rate=MIC_SAMPLE_RATE,
                input_audio_format="pcm",
            ),
        )

        p = pyaudio.PyAudio()
        mic_stream = p.open(
            format=pyaudio.paInt16,
            channels=MIC_CHANNELS,
            rate=MIC_SAMPLE_RATE,
            input=True,
            frames_per_buffer=MIC_FRAMES_PER_BUFFER,
        )

        print("语音对话已启动，按 Ctrl+C 退出。")
        print("当前策略：模型播报时暂停麦克风上行，播报结束后延迟恢复。")

        while True:
            data = mic_stream.read(MIC_FRAMES_PER_BUFFER, exception_on_overflow=False)

            if not duplex_gate.should_upload_mic():
                continue

            conv.append_audio(base64.b64encode(data).decode("ascii"))

    except KeyboardInterrupt:
        print("\n正在关闭...")
    finally:
        conv.close()
        if mic_stream is not None:
            mic_stream.close()
        if p is not None:
            p.terminate()
