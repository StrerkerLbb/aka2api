import asyncio
import json
import logging
import re
import threading
import time
import uuid
from typing import Dict, List, Optional, Any, AsyncGenerator

import httpx
from fastapi import FastAPI, Request, HTTPException, Response, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

# 导入自定义模块
from cookie_updater import get_valid_cookies, update_cookies_auto
from js_parser import extract_models_from_js
from config import (
    AKASH_API_URL, DEFAULT_MODEL, HOST, PORT,
    MAX_RETRIES, RETRY_DELAY, TIMEOUT, AKASH_JS_URL,
    print_config
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("openai-akash-proxy")

# 创建FastAPI应用
app = FastAPI(title="OpenAI to Akash Network Proxy")

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Akash Network API配置 - 现在从config.py导入

# 全局cookie存储
COOKIES = {}

# Cookie更新锁，防止多线程同时更新
cookie_update_lock = threading.Lock()

# 初始化cookie
def init_cookies():
    global COOKIES
    cookies, _ = get_valid_cookies()
    COOKIES.update(cookies)
    logger.info("Cookie已初始化")

# 后台定期更新cookie
def cookie_updater_task():
    while True:
        try:
            with cookie_update_lock:
                # 首先尝试自动更新
                cookies = update_cookies_auto()
                if cookies:
                    COOKIES.update(cookies)
                    logger.info("Cookie已在后台自动更新")
                else:
                    # 如果自动更新失败，则尝试常规更新方法
                    cookies, updated = get_valid_cookies()
                    if updated:
                        COOKIES.update(cookies)
                        logger.info("Cookie已在后台更新")
        except Exception as e:
            logger.error(f"更新Cookie时出错: {e}")
        
        # 每小时检查一次
        time.sleep(3600)

# 在请求前确保cookie有效
def ensure_valid_cookies():
    with cookie_update_lock:
        if not COOKIES or "cf_clearance" not in COOKIES or "session_token" not in COOKIES:
            # 首先尝试自动更新
            cookies = update_cookies_auto()
            if cookies:
                COOKIES.update(cookies)
                logger.info("Cookie已自动更新")
            else:
                # 如果自动更新失败，则使用常规方法
                cookies, _ = get_valid_cookies()
                COOKIES.update(cookies)
                logger.info("Cookie已按需更新")
AKASH_HEADERS = {
    "accept": "*/*",
    "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
    "content-type": "application/json",
    "origin": "https://chat.akash.network",
    "priority": "u=1, i",
    "referer": "https://chat.akash.network/",
    "sec-ch-ua": '"Chromium";v="136", "Microsoft Edge";v="136", "Not.A/Brand";v="99"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36 Edg/136.0.0.0"
}

# 默认模型ID - 现在从config.py导入

# 别名映射（更友好的名称）
MODEL_ALIASES = {
    "qwen-3": "Qwen3-235B-A22B-FP8",
    "llama-4": "meta-llama-Llama-4-Maverick-17B-128E-Instruct-FP8",
    "llama-3-3": "nvidia-Llama-3-3-Nemotron-Super-49B-v1",
    "qwen-qwq": "Qwen-QwQ-32B",
    "llama-3-70b": "Meta-Llama-3-3-70B-Instruct",
    "deepseek": "DeepSeek-R1",
    "llama-3-405b": "Meta-Llama-3-1-405B-Instruct-FP8",
}

# 全局模型列表和映射
AVAILABLE_MODELS = []
MODEL_MAPPING = {}

# 获取Akash可用模型列表
def fetch_available_models():
    global AVAILABLE_MODELS, MODEL_MAPPING
    
    try:
        # 先设置一些默认值，以防获取失败
        default_models = [
            {
                "id": "DeepSeek-R1",
                "name": "DeepSeek R1 671B",
                "description": "Strong Mixture-of-Experts (MoE) LLM"
            }
        ]
        
        # 尝试从JavaScript文件中获取模型列表
        try:
            response = httpx.get(
                AKASH_JS_URL,
                headers=AKASH_HEADERS,
                follow_redirects=True,
                timeout=TIMEOUT
            )
            
            if response.status_code == 200:
                # 使用专门的解析模块提取模型列表
                extracted_models = extract_models_from_js(response.text)
                
                if extracted_models:
                    AVAILABLE_MODELS = extracted_models
                    logger.info(f"成功从JS文件中提取 {len(AVAILABLE_MODELS)} 个模型")
                else:
                    # 如果提取失败，使用默认模型
                    AVAILABLE_MODELS = default_models
                    logger.warning("无法从JS文件中提取模型，使用默认模型")
            else:
                # 如果请求失败，使用默认模型
                AVAILABLE_MODELS = default_models
                logger.warning(f"获取JS文件失败，状态码: {response.status_code}，使用默认模型")
        except Exception as e:
            # 如果发生异常，使用默认模型
            AVAILABLE_MODELS = default_models
            logger.error(f"获取模型列表时出错: {e}", exc_info=True)
        
        # 构建模型映射
        MODEL_MAPPING = {}
        
        # 1. 添加直接映射（模型ID到自身）
        for model in AVAILABLE_MODELS:
            MODEL_MAPPING[model["id"]] = model["id"]
        
        # 2. 添加别名映射
        for alias, model_id in MODEL_ALIASES.items():
            if model_id in MODEL_MAPPING:
                MODEL_MAPPING[alias] = model_id
        
        # 3. 添加默认模型
        MODEL_MAPPING["default"] = DEFAULT_MODEL if DEFAULT_MODEL in MODEL_MAPPING else AVAILABLE_MODELS[0]["id"]
        
        logger.info(f"已加载 {len(AVAILABLE_MODELS)} 个可用模型")
        
    except Exception as e:
        logger.error(f"获取模型列表时出错: {e}", exc_info=True)
        # 如果发生错误，使用默认模型
        AVAILABLE_MODELS = default_models
        # 构建基本映射
        MODEL_MAPPING = {model["id"]: model["id"] for model in AVAILABLE_MODELS}
        MODEL_MAPPING["default"] = AVAILABLE_MODELS[0]["id"]

# 定义数据模型
class Message(BaseModel):
    role: str
    content: str

class OpenAIRequest(BaseModel):
    model: str
    messages: List[Message]
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = 1.0
    max_tokens: Optional[int] = None
    stream: Optional[bool] = False
    # 其他OpenAI参数...

# 将请求转换为Akash请求
def convert_to_akash_request(openai_request: OpenAIRequest) -> Dict[str, Any]:
    # 提取系统消息和用户消息
    system_message = ""
    user_messages = []
    
    for msg in openai_request.messages:
        if msg.role == "system":
            system_message = msg.content
        else:
            user_messages.append({"role": msg.role, "content": msg.content})
    
    # 如果没有用户消息，添加一个空的用户消息
    if not user_messages:
        user_messages.append({"role": "user", "content": "Hello"})
    
    # 获取对应的Akash模型
    # 如果请求的模型已经是Akash模型ID，直接使用；否则尝试从映射中获取
    if openai_request.model in [model["id"] for model in AVAILABLE_MODELS]:
        akash_model = openai_request.model
    else:
        akash_model = MODEL_MAPPING.get(openai_request.model, MODEL_MAPPING["default"])
    
    # 创建Akash请求
    akash_request = {
        "id": str(uuid.uuid4()).replace("-", "")[:16],  # 生成一个类似的ID
        "messages": user_messages,
        "model": akash_model,
        "system": system_message,
        "temperature": openai_request.temperature or 0.6,
        "topP": openai_request.top_p or 0.95,
        "context": []
    }
    
    logger.info(f"Converted request to Akash format: {akash_request}")
    return akash_request

# 清理响应文本，移除思考过程和处理换行符
def clean_response_text(text: str) -> str:
    """
    清理响应文本：
    1. 移除<think>...</think>标签中的内容
    2. 修复换行符问题，确保正确显示
    3. 移除多余的空行
    4. 将字符串'\n'转换为实际的换行符
    """
    # 移除<think>...</think>标签中的内容
    cleaned_text = re.sub(r'<think>[\s\S]*?</think>', '', text)
    
    # 将字符串'\n'转换为实际的换行符
    cleaned_text = cleaned_text.replace('\\n', '\n')
    
    # 替换连续的多个换行符为两个换行符
    cleaned_text = re.sub(r'\n{3,}', '\n\n', cleaned_text)
    
    # 移除前导和尾随的空白
    cleaned_text = cleaned_text.strip()
    
    # 记录清理前后的差异
    if text != cleaned_text:
        logger.info(f"Cleaned response text. Original length: {len(text)}, Cleaned length: {len(cleaned_text)}")
    
    return cleaned_text

# 将Akash非流式响应转换为OpenAI响应
def convert_to_openai_response(akash_response: str) -> Dict[str, Any]:
    try:
        logger.info(f"Processing Akash response: {akash_response[:200]}...")
        
        # 提取完整的响应文本
        full_text = ""
        
        # 使用正则表达式提取所有0:开头的内容片段
        chunks = re.findall(r'0:"(.*?)"', akash_response)
        if chunks:
            # 合并所有文本片段
            raw_text = "".join(chunks)
            # 清理响应文本
            full_text = clean_response_text(raw_text)
        
        # 如果没有找到文本，尝试其他方式解析
        if not full_text:
            logger.warning("Could not extract text using regex, trying alternate parsing")
            # 尝试从d:行解析完成信息
            finish_info_match = re.search(r'd:(.*?)$', akash_response)
            if finish_info_match:
                try:
                    finish_info = json.loads(finish_info_match.group(1))
                    logger.info(f"Extracted finish info: {finish_info}")
                except json.JSONDecodeError:
                    logger.warning("Could not parse finish info as JSON")
            
            # 提取消息ID
            msg_id_match = re.search(r'f:{"messageId":"(.*?)"}', akash_response)
            if msg_id_match:
                msg_id = msg_id_match.group(1)
                logger.info(f"Extracted message ID: {msg_id}")
            
            # 如果无法解析，返回原始响应
            full_text = f"Failed to parse response. Raw response: {akash_response[:500]}..."
        
        # 创建OpenAI格式的响应
        openai_response = {
            "id": f"chatcmpl-{uuid.uuid4()}",
            "object": "chat.completion",
            "created": int(uuid.uuid1().time),
            "model": "gpt-3.5-turbo",  # 固定返回这个模型名称
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": full_text
                },
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": 0,  # 无法准确获取
                "completion_tokens": 0,  # 无法准确获取
                "total_tokens": 0  # 无法准确获取
            }
        }
        
        logger.info(f"Converted to OpenAI response: {openai_response}")
        return openai_response
    except Exception as e:
        logger.error(f"Error converting Akash response: {e}", exc_info=True)
        # 返回一个基本的错误响应
        return {
            "id": f"chatcmpl-{uuid.uuid4()}",
            "object": "chat.completion",
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": f"Error processing response: {str(e)}"
                },
                "finish_reason": "stop"
            }],
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        }

# 处理流式响应
async def process_real_time_streaming(response_stream) -> AsyncGenerator[str, None]:
    """处理Akash的实时流式响应并转换为OpenAI的SSE格式"""
    # 创建OpenAI的响应ID
    response_id = f"chatcmpl-{uuid.uuid4()}"
    
    # 跟踪已收到的文本
    accumulated_text = ""
    buffer = ""
    finish_reason = None
    
    # 解析响应流
    async for chunk in response_stream:
        if not chunk:
            continue
            
        chunk_text = chunk.decode('utf-8') if isinstance(chunk, bytes) else chunk
        buffer += chunk_text
        
        # 处理完整的行
        while '\n' in buffer:
            line, buffer = buffer.split('\n', 1)
            line = line.strip()
            
            if not line:
                continue
                
            # 提取消息ID
            if line.startswith('f:{"messageId":'):
                msg_id_match = re.search(r'f:{"messageId":"(.*?)"}', line)
                if msg_id_match:
                    msg_id = msg_id_match.group(1)
                    logger.info(f"Stream message ID: {msg_id}")
                continue
                
            # 提取文本片段
            if line.startswith('0:"'):
                # 提取引号中的内容
                text_match = re.search(r'0:"(.*?)"', line)
                if text_match:
                    text = text_match.group(1)
                    # 处理转义字符
                    text = text.replace('\\n', '\n')
                    accumulated_text += text
                    
                    # 创建OpenAI格式的响应块
                    openai_chunk = {
                        "id": response_id,
                        "object": "chat.completion.chunk",
                        "created": int(uuid.uuid1().time),
                        "model": "gpt-3.5-turbo",
                        "choices": [{
                            "index": 0,
                            "delta": {
                                "content": text
                            },
                            "finish_reason": None
                        }]
                    }
                    
                    yield f"data: {json.dumps(openai_chunk)}\n\n"
                continue
                
            # 检查是否完成
            if line.startswith('e:') or line.startswith('d:'):
                try:
                    finish_data = json.loads(line.split(':', 1)[1])
                    finish_reason = finish_data.get("finishReason", "stop")
                    logger.info(f"Stream finished with reason: {finish_reason}")
                except json.JSONDecodeError:
                    logger.warning(f"Could not parse finish info: {line}")
                    finish_reason = "stop"
    
    # 发送最终的完成块
    final_chunk = {
        "id": response_id,
        "object": "chat.completion.chunk",
        "created": int(uuid.uuid1().time),
        "model": "gpt-3.5-turbo",
        "choices": [{
            "index": 0,
            "delta": {},
            "finish_reason": finish_reason or "stop"
        }]
    }
    yield f"data: {json.dumps(final_chunk)}\n\n"
    
    # 发送完成标记
    yield "data: [DONE]\n\n"
    
    logger.info(f"Streaming completed. Total text length: {len(accumulated_text)}")


# 保留此函数用于非流式响应处理
async def process_streaming_response(response_text: str) -> AsyncGenerator[str, None]:
    """处理Akash的非流式响应并转换为OpenAI的SSE格式（用于备份）"""
    from config import STREAM_DELAY
    
    # 提取消息ID
    msg_id_match = re.search(r'f:{"messageId":"(.*?)"}', response_text)
    msg_id = msg_id_match.group(1) if msg_id_match else f"msg-{uuid.uuid4()}"
    
    # 创建OpenAI的响应ID
    response_id = f"chatcmpl-{uuid.uuid4()}"
    
    # 提取所有文本片段
    chunks = re.findall(r'0:"(.*?)"', response_text)
    
    # 如果没有找到片段，返回错误消息
    if not chunks:
        error_chunk = {
            "id": response_id,
            "object": "chat.completion.chunk",
            "created": int(uuid.uuid1().time),
            "model": "gpt-3.5-turbo",
            "choices": [{
                "index": 0,
                "delta": {
                    "content": "Error: Could not parse streaming response"
                },
                "finish_reason": None
            }]
        }
        yield f"data: {json.dumps(error_chunk)}\n\n"
        yield "data: [DONE]\n\n"
        return
    
    # 将所有文本片段合并为一个完整的响应
    full_text = "".join(chunks)
    cleaned_full_text = clean_response_text(full_text)
    
    # 将清理后的文本拆分成更小的片段，实现更真实的流式效果
    # 可以按句子、单词或字符拆分
    # 这里我们按句子拆分
    sentences = re.split(r'([.!?。！？\n]+)', cleaned_full_text)
    stream_chunks = []
    
    current_chunk = ""
    for i in range(0, len(sentences), 2):
        if i < len(sentences):
            current_chunk += sentences[i]
            
        if i + 1 < len(sentences):
            current_chunk += sentences[i + 1]
            
        if current_chunk:
            stream_chunks.append(current_chunk)
            current_chunk = ""
    
    # 如果没有找到句子，按字符拆分
    if not stream_chunks and cleaned_full_text:
        # 每次发送10-30个字符
        import random
        chunk_size = random.randint(10, 30)
        for i in range(0, len(cleaned_full_text), chunk_size):
            stream_chunks.append(cleaned_full_text[i:i+chunk_size])
    
    # 发送每个文本片段
    for i, chunk in enumerate(stream_chunks):
        is_last = i == len(stream_chunks) - 1
        
        openai_chunk = {
            "id": response_id,
            "object": "chat.completion.chunk",
            "created": int(uuid.uuid1().time),
            "model": "gpt-3.5-turbo",
            "choices": [{
                "index": 0,
                "delta": {
                    "content": chunk
                },
                "finish_reason": "stop" if is_last else None
            }]
        }
        
        yield f"data: {json.dumps(openai_chunk)}\n\n"
        
        # 在每个块之间添加一个小延迟，模拟流式效果
        if not is_last:
            await asyncio.sleep(STREAM_DELAY)
    
    # 发送完成标记
    yield "data: [DONE]\n\n"

# 主端点：处理OpenAI格式的聊天完成请求
@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    try:
        # 记录原始请求
        body_bytes = await request.body()
        body_str = body_bytes.decode('utf-8')
        logger.info(f"Received request: {body_str}")
        
        # 解析请求体
        body = json.loads(body_str)
        openai_request = OpenAIRequest(**body)
        
        # 转换为Akash请求格式
        akash_request = convert_to_akash_request(openai_request)
        
        # 获取会话令牌（实际使用时需要配置）
        session_token = request.headers.get("x-akash-session-token")
        cf_clearance = request.headers.get("x-akash-cf-clearance")
        
        # 确保cookie有效
        ensure_valid_cookies()
        
        # 使用全局cookie，但允许通过headers覆盖
        cookies = COOKIES.copy()
        
        if session_token:
            cookies["session_token"] = session_token
            
        if cf_clearance:
            cookies["cf_clearance"] = cf_clearance
        
        # 处理流式请求
        if openai_request.stream:
            # 使用真正的流式请求从Akash API获取响应
            logger.info(f"Sending real-time streaming request to Akash: {akash_request}")
            
            # 添加响应头，确保流式传输工作正常
            response_headers = {
                "Content-Type": "text/event-stream",
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Transfer-Encoding": "chunked",
                "X-Accel-Buffering": "no"  # 禁用Nginx缓冲，确保实时流式传输
            }
            
            # 创建一个异步生成器，用于从Akash API获取流式响应
            async def akash_stream_generator():
                async with httpx.AsyncClient(timeout=None) as client:  # 无超时，因为是流式请求
                    try:
                        # 使用stream=True参数启用流式传输
                        async with client.stream(
                            "POST",
                            AKASH_API_URL,
                            headers=AKASH_HEADERS,
                            cookies=cookies,
                            json=akash_request,
                        ) as response:
                            # 检查响应状态
                            if response.status_code != 200:
                                error_text = await response.text()
                                logger.error(f"Akash API streaming error: {error_text}")
                                yield f"Error: {error_text}".encode('utf-8')
                                return
                                
                            # 逐块接收数据并转发
                            buffer = ""
                            async for chunk in response.aiter_text():
                                if chunk:
                                    # 直接传递原始文本块
                                    yield chunk
                    except Exception as e:
                        logger.error(f"Streaming request error: {e}", exc_info=True)
                        yield f"Error during streaming: {str(e)}".encode('utf-8')
            
            # 返回真正的流式响应
            return StreamingResponse(
                process_real_time_streaming(akash_stream_generator()),
                media_type="text/event-stream",
                headers=response_headers
            )
        else:
            # 非流式请求
            logger.info(f"Sending request to Akash: {akash_request}")
            async with httpx.AsyncClient() as client:
                # 添加重试逻辑
                retry_count = 0
                while True:
                    try:
                        response = await client.post(
                            AKASH_API_URL,
                            headers=AKASH_HEADERS,
                            cookies=cookies,
                            json=akash_request,
                            timeout=TIMEOUT
                        )
                        break  # 成功则跳出循环
                    except Exception as e:
                        retry_count += 1
                        if retry_count > MAX_RETRIES:
                            raise  # 重试次数用完，抛出异常
                        logger.warning(f"请求失败，正在重试 ({retry_count}/{MAX_RETRIES}): {e}")
                        await asyncio.sleep(RETRY_DELAY * retry_count)  # 指数退避
            
            # 记录响应
            logger.info(f"Akash response status: {response.status_code}")
            
            # 检查响应状态
            if response.status_code != 200:
                error_msg = f"Akash API error: {response.text}"
                logger.error(error_msg)
                return JSONResponse(
                    status_code=response.status_code,
                    content={"error": error_msg}
                )
            
            try:
                # 转换为OpenAI格式并返回
                return convert_to_openai_response(response.text)
            except Exception as e:
                logger.error(f"Failed to convert Akash response: {e}", exc_info=True)
                logger.info(f"Raw response: {response.text}")
                return JSONResponse(
                    status_code=500,
                    content={"error": f"Failed to convert Akash response: {str(e)}", "raw_response": response.text[:1000]}
                )
    
    except Exception as e:
        logger.error(f"Internal server error: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": f"Internal server error: {str(e)}"}
        )

# 模型列表端点
@app.get("/v1/models")
def list_models():
    """返回支持的模型列表，与OpenAI API兼容"""
    data = []
    
    for model in AVAILABLE_MODELS:
        data.append({
            "id": model["id"],
            "object": "model",
            "created": int(time.time()) - 10000,  # 假设模型是最近创建的
            "owned_by": "akash-network",
            "permission": [],
            "root": model["id"],
            "parent": None
        })
    
    return {
        "object": "list",
        "data": data
    }

# Embeddings端点
@app.post("/v1/embeddings")
async def create_embeddings(request: Request):
    """创建文本嵌入，返回兼容OpenAI的响应格式"""
    try:
        # 解析请求
        body = await request.json()
        input_text = body.get("input", "")
        model = body.get("model", "text-embedding-ada-002")
        
        if not input_text:
            return JSONResponse(
                status_code=400,
                content={"error": {"message": "Input text is required", "type": "invalid_request_error"}}
            )
        
        # 如果是字符串，转换为列表
        if isinstance(input_text, str):
            input_texts = [input_text]
        else:
            input_texts = input_text
            
        # 记录请求
        logger.info(f"Embeddings request received for {len(input_texts)} texts using model {model}")
        
        # 创建一个模拟的嵌入向量（实际应用中，这里应该调用真正的嵌入模型）
        # 在此示例中，我们只返回一个固定长度的随机向量
        embeddings = []
        for i, text in enumerate(input_texts):
            # 创建一个1536维的随机向量（与OpenAI的text-embedding-ada-002相同）
            # 在实际应用中，这应该是从模型获取的真实嵌入
            import numpy as np
            vector = list(np.random.normal(0, 0.1, 1536).astype(float))
            
            embeddings.append({
                "object": "embedding",
                "embedding": vector,
                "index": i
            })
        
        # 返回OpenAI兼容的响应
        return {
            "object": "list",
            "data": embeddings,
            "model": model,
            "usage": {
                "prompt_tokens": sum(len(text.split()) for text in input_texts),
                "total_tokens": sum(len(text.split()) for text in input_texts)
            }
        }
    
    except Exception as e:
        logger.error(f"Error creating embeddings: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": {"message": f"Error creating embeddings: {str(e)}", "type": "server_error"}}
        )
# 健康检查端点
@app.get("/health")
def health_check():
    return {"status": "ok", "version": "1.0.0"}

# 添加一个调试端点，用于直接测试Akash API
@app.post("/debug/akash-api")
async def debug_akash_api(request: Request):
    try:
        # 获取请求体
        body = await request.json()
        
        # 获取会话令牌
        session_token = request.headers.get("x-akash-session-token")
        cf_clearance = request.headers.get("x-akash-cf-clearance")
        
        # 确保cookie有效
        ensure_valid_cookies()
        
        # 使用全局cookie，但允许通过headers覆盖
        cookies = COOKIES.copy()
        
        if session_token:
            cookies["session_token"] = session_token
            
        if cf_clearance:
            cookies["cf_clearance"] = cf_clearance
        
        # 发送请求到Akash
        logger.info(f"Debug: Sending request to Akash: {body}")
        async with httpx.AsyncClient() as client:
            # 添加重试逻辑
            retry_count = 0
            while True:
                try:
                    response = await client.post(
                        AKASH_API_URL,
                        headers=AKASH_HEADERS,
                        cookies=cookies,
                        json=body,
                        timeout=TIMEOUT
                    )
                    break  # 成功则跳出循环
                except Exception as e:
                    retry_count += 1
                    if retry_count > MAX_RETRIES:
                        raise  # 重试次数用完，抛出异常
                    logger.warning(f"调试请求失败，正在重试 ({retry_count}/{MAX_RETRIES}): {e}")
                    await asyncio.sleep(RETRY_DELAY * retry_count)  # 指数退避
        
        # 记录响应
        logger.info(f"Debug: Akash response status: {response.status_code}")
        
        # 返回原始响应
        try:
            return {"status_code": response.status_code, "text": response.text}
        except:
            return {"status_code": response.status_code, "error": "Could not parse response"}
    
    except Exception as e:
        logger.error(f"Debug endpoint error: {e}", exc_info=True)
        return {"error": str(e)}

# 启动服务器
if __name__ == "__main__":
    import uvicorn
    
    # 打印配置信息
    print_config()
    
    # 初始化cookie
    init_cookies()
    
    # 获取可用模型列表
    fetch_available_models()
    
    # 启动后台cookie更新线程
    cookie_updater = threading.Thread(target=cookie_updater_task, daemon=True)
    cookie_updater.start()
    
    logger.info("Starting OpenAI to Akash Network Proxy server...")
    uvicorn.run(app, host=HOST, port=PORT)