@echo off
echo 正在激活虚拟环境...
call .\.venv\Scripts\activate.bat

echo 正在启动 OpenAI to Akash Network 代理服务器...
python openai_to_akash_proxy.py

pause 