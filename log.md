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
