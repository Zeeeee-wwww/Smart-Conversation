from openai import OpenAI

# 初始化客户端，指向 MiMo API
client = OpenAI(
    api_key="sk-cizcdtjraq5e321bpu8c14s07ypntlfoclb8z8439v2hjx5z", 
    base_url="https://api.xiaomimimo.com/v1"  # MiMo 服务端点[citation:6]
)

def voice_chat(audio_file_path):
    """模拟语音对话：ASR 识别 -> LLM 回复"""
    
    # --- 步骤1：语音识别 (ASR) ---
    # 假设 MiMo 有语音识别端点，具体请查阅官方文档
    # with open(audio_file_path, "rb") as f:
    #     transcript = client.audio.transcriptions.create(
    #         model="mimo-v2-asr", 
    #         file=f
    #     )
    # user_text = transcript.text
    
    # 这里先用文本模拟用户输入
    user_text = "你好，今天天气怎么样？"
    print(f"用户说: {user_text}")

    # --- 步骤2：调用大模型生成回复 ---
    completion = client.chat.completions.create(
        model="mimo-v2-flash",  # 轻量快速版，适合对话[citation:6]
        messages=[
            {"role": "system", "content": "你是一个友好的语音助手，请用简洁的口语回复。"},
            {"role": "user", "content": user_text}
        ],
        max_tokens=512,
        temperature=0.7
    )
    
    reply_text = completion.choices[0].message.content
    print(f"助手回复: {reply_text}")
    return reply_text

# 测试运行
if __name__ == "__main__":
    voice_chat("test.wav")
