import base64
import time
import pyaudio
import dashscope
from dashscope.audio.qwen_omni import OmniRealtimeConversation, OmniRealtimeCallback, MultiModality

# === 配置 ===
dashscope.api_key = "sk-13f23215997b46c39be9b3adb641d85b"  # 北京地域API Key
URL = "wss://dashscope.aliyuncs.com/api-ws/v1/realtime"      # 北京地域端点<sup data-index='2'>3</sup>
MODEL = "qwen3.5-omni-plus-realtime"

class MyCallback(OmniRealtimeCallback):
    def __init__(self):
        self.pya = None
        self.stream_out = None

    def on_open(self):
        self.pya = pyaudio.PyAudio()
        self.stream_out = self.pya.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=24000,
            output=True
        )

    def on_event(self, response):
        # 打印用户语音识别结果
        if response.get('type') == 'conversation.item.input_audio_transcription.completed':
            print(f"\n[User] {response.get('transcript', '')}")
        # 播放模型返回的音频
        elif response.get('type') == 'response.audio.delta':
            audio_bytes = base64.b64decode(response['delta'])
            if self.stream_out and not self.stream_out.is_stopped():
                self.stream_out.write(audio_bytes)

    def on_close(self, code, reason):
        if self.stream_out:
            self.stream_out.close()
        if self.pya:
            self.pya.terminate()

# === 主流程 ===
if __name__ == "__main__":
    callback = MyCallback()
    # 注意：参数是 callback（单数），不是 callbacks
    conv = OmniRealtimeConversation(
        model=MODEL,
        url=URL,
        callback=callback  # ← 关键修正点
    )

    try:
        conv.connect()
        conv.update_session(
            output_modalities=[MultiModality.AUDIO, MultiModality.TEXT],
            voice="Ethan",
            instructions="你是阿里云Qwen助手，请简洁专业地回答。"
        )

        # 麦克风输入（16kHz, 单声道）
        p = pyaudio.PyAudio()
        mic_stream = p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=16000,
            input=True,
            frames_per_buffer=3200
        )

        print("🎙️ 对话已启动，请说话（按 Ctrl+C 退出）...")
        while True:
            data = mic_stream.read(3200, exception_on_overflow=False)
            conv.append_audio(base64.b64encode(data).decode())
            time.sleep(0.01)

    except KeyboardInterrupt:
        print("\n正在关闭...")
    finally:
        conv.close()
        mic_stream.close()
        p.terminate()
