import json
import logging
import os
import time
import requests
from typing import Dict, Optional, Tuple

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("cookie-updater")

# 配置
AKASH_URL = "https://chat.akash.network/"
AKASH_SESSION_URL = "https://chat.akash.network/api/auth/session/"
COOKIE_FILE = "akash_cookies.json"
COOKIE_EXPIRY_THRESHOLD = 3600  # 1小时，单位：秒


def save_cookies(cookies: Dict[str, str]) -> None:
    """保存cookie到文件"""
    with open(COOKIE_FILE, "w") as f:
        json.dump(cookies, f)
    logger.info(f"Cookie已保存到{COOKIE_FILE}")


def load_cookies() -> Optional[Dict[str, str]]:
    """从文件加载cookie"""
    if not os.path.exists(COOKIE_FILE):
        logger.info(f"Cookie文件{COOKIE_FILE}不存在")
        return None
    
    try:
        with open(COOKIE_FILE, "r") as f:
            cookies = json.load(f)
        
        # 检查是否包含必要的cookie
        if "cf_clearance" not in cookies or "session_token" not in cookies:
            logger.warning("Cookie文件不包含必要的cookie")
            return None
        
        # 检查文件修改时间，判断cookie是否过期
        file_mtime = os.path.getmtime(COOKIE_FILE)
        if time.time() - file_mtime > COOKIE_EXPIRY_THRESHOLD:
            logger.info("Cookie可能已过期，需要更新")
            return None
        
        logger.info("成功加载Cookie")
        return cookies
    except Exception as e:
        logger.error(f"加载Cookie时出错: {e}")
        return None


def get_manual_cookie_input() -> Dict[str, str]:
    """手动输入cookie"""
    print("\n===== 手动输入Cookie =====")
    print("请从浏览器中获取以下Cookie值:")
    print("1. 打开Chrome浏览器，访问 https://chat.akash.network/")
    print("2. 按F12打开开发者工具，切换到'应用'或'Application'标签")
    print("3. 在左侧找到'Cookies'，点击'https://chat.akash.network'")
    print("4. 找到并复制以下cookie值:\n")
    
    cookies = {}
    
    # 获取cf_clearance
    cf_clearance = input("cf_clearance: ").strip()
    if cf_clearance:
        cookies["cf_clearance"] = cf_clearance
    
    # 获取session_token
    session_token = input("session_token: ").strip()
    if session_token:
        cookies["session_token"] = session_token
    
    # 可选: 获取其他cookie
    _ga = input("_ga (可选): ").strip()
    if _ga:
        cookies["_ga"] = _ga
    
    _ga_lfrgn = input("_ga_LFRGN2J2RV (可选): ").strip()
    if _ga_lfrgn:
        cookies["_ga_LFRGN2J2RV"] = _ga_lfrgn
    
    # 检查是否获取了必要的cookie
    if "cf_clearance" not in cookies or "session_token" not in cookies:
        logger.warning("未提供必要的cookie")
        return {}
    
    logger.info("成功获取Cookie")
    return cookies


def auto_get_cf_clearance() -> Dict[str, str]:
    """
    半自动化获取 cf_clearance
    使用 undetected-chromedriver 尝试获取
    """
    try:
        # 尝试导入依赖
        import undetected_chromedriver as uc
        from selenium.webdriver.common.by import By
        
        logger.info("开始半自动化获取 cf_clearance...")
        
        # 设置 Chrome 选项
        options = uc.ChromeOptions()
        
        # 反检测设置
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-extensions')
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # 创建驱动
        driver = uc.Chrome(options=options, version_main=120)
        
        try:
            logger.info("正在访问 Akash Network...")
            driver.get("https://chat.akash.network/")
            
            # 等待页面加载和可能的 Cloudflare 挑战
            time.sleep(10)
            
            # 检测并等待 Cloudflare 挑战解决
            max_wait_time = 60  # 最多等待60秒
            start_time = time.time()
            
            while time.time() - start_time < max_wait_time:
                try:
                    # 检查是否还在 Cloudflare 挑战页面
                    challenge_elements = [
                        "//title[contains(text(), 'Just a moment')]",
                        "//*[contains(text(), 'Checking your browser')]",
                        "//*[contains(text(), 'Cloudflare')]"
                    ]
                    
                    in_challenge = False
                    for xpath in challenge_elements:
                        try:
                            element = driver.find_element(By.XPATH, xpath)
                            if element.is_displayed():
                                in_challenge = True
                                break
                        except:
                            continue
                    
                    if not in_challenge:
                        logger.info("Cloudflare 挑战已解决")
                        break
                        
                    time.sleep(2)
                    
                except Exception:
                    time.sleep(2)
                    continue
            
            # 获取 cookies
            cookies = driver.get_cookies()
            cookie_dict = {}
            
            for cookie in cookies:
                cookie_dict[cookie['name']] = cookie['value']
            
            driver.quit()
            
            if 'cf_clearance' in cookie_dict:
                logger.info("✅ 成功获取 cf_clearance!")
                return cookie_dict
            else:
                logger.warning("❌ 未能获取 cf_clearance")
                return {}
                
        except Exception as e:
            logger.error(f"浏览器操作出错: {e}")
            if 'driver' in locals():
                try:
                    driver.quit()
                except:
                    pass
            return {}
            
    except ImportError:
        logger.warning("未安装 undetected-chromedriver，无法使用半自动化获取功能")
        logger.info("请运行: pip install undetected-chromedriver selenium")
        return {}
    except Exception as e:
        logger.error(f"半自动化获取 cf_clearance 失败: {e}")
        return {}


def auto_update_cookies() -> Dict[str, str]:
    """自动获取和更新cookie"""
    logger.info("尝试自动更新Cookie...")
    
    # 先加载现有cookie，我们需要cf_clearance
    existing_cookies = load_cookies()
    
    if existing_cookies is None or "cf_clearance" not in existing_cookies:
        logger.warning("无法自动更新Cookie：缺少cf_clearance")
        return {}
    
    # 准备请求头
    headers = {
        "accept": "*/*",
        "accept-language": "zh,en;q=0.9,zh-CN;q=0.8,en-GB;q=0.7,en-US;q=0.6",
        "cache-control": "no-cache",
        "pragma": "no-cache",
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
    
    # 准备cookie
    cookies = {
        "cf_clearance": existing_cookies["cf_clearance"]
    }
    
    # 如果有其他可选cookie，也加入
    if "_ga" in existing_cookies:
        cookies["_ga"] = existing_cookies["_ga"]
    
    if "_ga_LFRGN2J2RV" in existing_cookies:
        cookies["_ga_LFRGN2J2RV"] = existing_cookies["_ga_LFRGN2J2RV"]
    
    try:
        # 发送请求
        response = requests.get(
            AKASH_SESSION_URL,
            headers=headers,
            cookies=cookies
        )
        
        # 检查响应状态
        if response.status_code == 200:
            # 从响应头中获取session_token
            cookies_dict = requests.utils.dict_from_cookiejar(response.cookies)
            
            # 检查是否有session_token
            if "session_token" in cookies_dict:
                # 更新cookie
                existing_cookies["session_token"] = cookies_dict["session_token"]
                logger.info("成功自动获取session_token")
                
                # 保存更新后的cookie
                save_cookies(existing_cookies)
                return existing_cookies
            else:
                logger.warning("响应中没有session_token")
        else:
            logger.warning(f"请求失败，状态码: {response.status_code}")
    
    except Exception as e:
        logger.error(f"自动更新Cookie时出错: {e}")
    
    return {}

def get_valid_cookies() -> Tuple[Dict[str, str], bool]:
    """获取有效的cookie，如果需要则更新"""
    # 尝试加载现有cookie
    cookies = load_cookies()
    
    # 如果cookie不存在或已过期，尝试自动更新
    if cookies is None:
        logger.info("需要更新Cookie")
        
        # 首先尝试自动更新
        cookies = auto_update_cookies()
        
        # 如果自动更新失败，尝试半自动化获取 cf_clearance
        if not cookies:
            logger.info("尝试半自动化获取 cf_clearance...")
            auto_cookies = auto_get_cf_clearance()
            
            if auto_cookies and 'cf_clearance' in auto_cookies:
                logger.info("半自动化获取 cf_clearance 成功，继续获取 session_token...")
                
                # 保存获取到的 cookies
                save_cookies(auto_cookies)
                
                # 尝试使用新的 cf_clearance 获取 session_token
                cookies = auto_update_cookies()
                
                if not cookies:
                    # 如果仍然失败，直接使用获取到的 cookies
                    cookies = auto_cookies
        
        # 如果所有自动化方法都失败，则请求手动输入
        if not cookies:
            print("\n🤖 自动获取Cookie失败，请手动输入。")
            print("\n💡 提示：你也可以:")
            print("1. 先运行: python install_cf_helper.py 安装依赖")
            print("2. 然后运行: python auto_cf_helper.py 尝试半自动化获取")
            cookies = get_manual_cookie_input()
        
        if cookies:
            save_cookies(cookies)
            return cookies, True
        else:
            logger.error("无法获取有效的Cookie")
            return {}, False
    
    return cookies, False


def update_cookies_manually() -> Dict[str, str]:
    """强制手动更新cookie"""
    cookies = get_manual_cookie_input()
    if cookies:
        save_cookies(cookies)
        logger.info("已手动更新Cookie")
    return cookies

def update_cookies_auto() -> Dict[str, str]:
    """强制自动更新cookie"""
    cookies = auto_update_cookies()
    if cookies:
        logger.info("已自动更新Cookie")
    else:
        logger.warning("自动更新Cookie失败")
    return cookies


if __name__ == "__main__":
    # 测试cookie更新功能
    cookies, updated = get_valid_cookies()
    if updated:
        print("Cookie已更新:")
    else:
        print("使用现有Cookie:")
    
    print(json.dumps(cookies, indent=2))