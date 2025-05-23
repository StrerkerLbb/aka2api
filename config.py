import os
from dotenv import load_dotenv
import logging

# 加载.env文件中的环境变量
load_dotenv()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("config")

# Akash API配置
AKASH_API_URL = os.getenv("AKASH_API_URL", "https://chat.akash.network/api/chat/")
AKASH_JS_URL = os.getenv("AKASH_JS_URL", "https://chat.akash.network/_next/static/chunks/939-e56b9689ddc1242a.js")

# 默认模型
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "DeepSeek-R1")

# 服务器配置
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

# Cookie配置
COOKIE_FILE = os.getenv("COOKIE_FILE", "akash_cookies.json")
COOKIE_EXPIRY_THRESHOLD = int(os.getenv("COOKIE_EXPIRY_THRESHOLD", "3600"))  # 默认1小时

# 重试配置
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
RETRY_DELAY = float(os.getenv("RETRY_DELAY", "1.0"))  # 秒

# 流式响应配置
STREAM_CHUNK_SIZE = int(os.getenv("STREAM_CHUNK_SIZE", "1024"))
STREAM_DELAY = float(os.getenv("STREAM_DELAY", "0.01"))  # 秒

# HTTP请求超时设置
TIMEOUT = float(os.getenv("TIMEOUT", "30.0"))  # 秒

# 打印配置信息
def print_config():
    """打印当前配置信息"""
    logger.info("=== 当前配置 ===")
    logger.info(f"AKASH_API_URL: {AKASH_API_URL}")
    logger.info(f"DEFAULT_MODEL: {DEFAULT_MODEL}")
    logger.info(f"HOST: {HOST}, PORT: {PORT}")
    logger.info(f"MAX_RETRIES: {MAX_RETRIES}, RETRY_DELAY: {RETRY_DELAY}")
    logger.info(f"COOKIE_EXPIRY_THRESHOLD: {COOKIE_EXPIRY_THRESHOLD}")
    logger.info("================")

# 创建示例.env文件
def create_example_env():
    """创建示例.env文件"""
    env_content = """# Akash API配置
AKASH_API_URL=https://chat.akash.network/api/chat/
AKASH_JS_URL=https://chat.akash.network/_next/static/chunks/939-e56b9689ddc1242a.js

# 默认模型
DEFAULT_MODEL=DeepSeek-R1

# 服务器配置
HOST=0.0.0.0
PORT=8000

# Cookie配置
COOKIE_FILE=akash_cookies.json
COOKIE_EXPIRY_THRESHOLD=3600

# 重试配置
MAX_RETRIES=3
RETRY_DELAY=1.0

# 流式响应配置
STREAM_CHUNK_SIZE=1024
STREAM_DELAY=0.01

# HTTP请求超时设置
TIMEOUT=30.0
"""
    
    # 如果.env文件不存在，则创建
    if not os.path.exists(".env.example"):
        with open(".env.example", "w") as f:
            f.write(env_content)
        logger.info("已创建.env.example文件")

if __name__ == "__main__":
    print_config()
    create_example_env()