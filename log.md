Problem1:Computer failed to recognize the mac device.(There's no response after insert the USB).
  1>Device not visible in Device manager.

```markdown
  # solution:
    Resetting the USB Root Hub (to refresh all USB ports)
    1. Open Device Manager and expand the "Universal Serial Bus controllers" section.
    2. Right-click on every item that contains "Hub" (for example, "USB Root Hub"), and select "Uninstall device". Work from the bottom of the list upwards.
    3. Note: Your keyboard and mouse will stop working during this process, which is expected.
    4. After uninstalling all of them, force shut down your PC by pressing the power button. Turn it back on, and Windows will automatically reinstall all the USB drivers.
```
->conversation_MiMo.py

Problem2:TimeoutError: WebSocket connection could not be established within 5 seconds. Please check your network connection, firewall settings, or server status.

```markdown
  # solution process:
    1	DeepSeek	## Upgrade dashscope SDK, add model param to connect()	Failed — TypeError: unexpected keyword argument 'model'
    2	DeepSeek	## Set HTTP/HTTPS proxy via environment variables	Failed — timeout persisted
    3	DeepSeek	## Use China-site API Key + set SSL_CERT_FILE to certifi path	Failed — timeout persisted
    4	DeepSeek	## Switch from WebSocket to HTTP recording-transcription API	Not attempted (user wanted real-time dialogue)
    5	Alibaba Cloud AI	Corrected callbacks → callback parameter, upgraded model to qwen3.5-omni-plus-realtime, added audio output streaming	✅ Success — real-time voice dialogue working
```
->Mac_connected_Qwen.py

Problem3:The assistant's audio output is captures by the microphone and treated as user input,causing the dialogue to loop or break.

```markdown
# Attempt 1 (DeepSeek)

  Approach: Mute mic on first response.audio.delta, start a background thread to monitor silence duration. If no audio received for 1 second, assume the AI has finished speaking and unmute.

  Flaw: The API pauses between audio chunks during natural speech, causing premature unmute. Essentially guessing when the AI stops rather than knowing for sure.

 ## Result: ❌ Failed — mic would unmute mid-reply, still capturing assistant output as input.

# Attempt 2 (Codex)

  Approach: Still mute on response.audio.delta, but defer the unmute check to the response.done event. This event is explicitly sent by the API when a complete response turn finishes. A       _wait_silence_end() method then waits an extra SILENCE_TIMEOUT before unmuting.
  
  Key insight: Use the API's built-in end-of-turn signal instead of guessing, and also added response.audio_transcript.done for text echo debugging.

 ## Result: ✅ Success — reliable mute/unmute cycle with no feedback loop.

 ### Takeaway: The API already tells you when it's done speaking via response.done. Guessing with silence timeout on partial audio chunks is unreliable.

 #### AI key word(codex):现在我解决了这个问题，但是扬声器播放的回复会被拾取扰乱对话，修改方案也没有起到效果，帮我看看怎么改善。
  
```
