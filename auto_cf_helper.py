#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
半自动化 cf_clearance 获取助手
使用 undetected-chromedriver 来减少被检测的概率
"""

import json
import time
import logging
from typing import Dict, Optional
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("cf-helper")

class CloudflareHelper:
    def __init__(self, headless: bool = False):
        self.driver = None
        self.headless = headless
        
    def setup_driver(self):
        """设置 undetected Chrome 驱动"""
        try:
            options = uc.ChromeOptions()
            
            # 基本设置
            if self.headless:
                options.add_argument('--headless')
            
            # 反检测设置
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--disable-extensions')
            options.add_argument('--disable-plugins')
            options.add_argument('--disable-images')
            options.add_argument('--disable-javascript')  # 可选：禁用JS以减少检测
            
            # 模拟真实用户环境
            options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            options.add_argument('--accept-language=zh-CN,zh;q=0.9,en;q=0.8')
            
            # 创建驱动
            self.driver = uc.Chrome(options=options, version_main=120)
            logger.info("Chrome 驱动已启动")
            
        except Exception as e:
            logger.error(f"启动 Chrome 驱动失败: {e}")
            raise
    
    def get_cf_clearance(self, url: str = "https://chat.akash.network/", timeout: int = 30) -> Optional[Dict[str, str]]:
        """
        尝试获取 cf_clearance cookie
        
        Args:
            url: 目标网站 URL
            timeout: 超时时间（秒）
            
        Returns:
            包含 cookies 的字典，失败时返回 None
        """
        if not self.driver:
            self.setup_driver()
            
        try:
            logger.info(f"正在访问: {url}")
            self.driver.get(url)
            
            # 等待页面加载
            time.sleep(5)
            
            # 检测是否遇到 Cloudflare 挑战
            if self._detect_cloudflare_challenge():
                logger.info("检测到 Cloudflare 挑战，等待解决...")
                
                # 等待挑战解决（最多等待 timeout 秒）
                success = self._wait_for_challenge_resolution(timeout)
                
                if not success:
                    logger.warning("Cloudflare 挑战未能在指定时间内解决")
                    return None
            
            # 获取所有 cookies
            cookies = self.driver.get_cookies()
            cookie_dict = {}
            
            for cookie in cookies:
                cookie_dict[cookie['name']] = cookie['value']
            
            # 检查是否成功获取 cf_clearance
            if 'cf_clearance' in cookie_dict:
                logger.info("成功获取 cf_clearance!")
                return cookie_dict
            else:
                logger.warning("未找到 cf_clearance cookie")
                return cookie_dict  # 返回其他 cookies，可能包含有用信息
                
        except Exception as e:
            logger.error(f"获取 cf_clearance 时出错: {e}")
            return None
    
    def _detect_cloudflare_challenge(self) -> bool:
        """检测是否遇到 Cloudflare 挑战"""
        try:
            # 检查常见的 Cloudflare 挑战元素
            challenge_indicators = [
                "//title[contains(text(), 'Just a moment')]",
                "//div[contains(@class, 'cf-browser-verification')]", 
                "//div[contains(@class, 'cf-loading')]",
                "//*[contains(text(), 'Checking your browser')]",
                "//*[contains(text(), 'Cloudflare')]"
            ]
            
            for indicator in challenge_indicators:
                try:
                    element = self.driver.find_element(By.XPATH, indicator)
                    if element.is_displayed():
                        return True
                except:
                    continue
                    
            return False
            
        except Exception:
            return False
    
    def _wait_for_challenge_resolution(self, timeout: int) -> bool:
        """等待 Cloudflare 挑战解决"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                # 检查是否还在挑战页面
                if not self._detect_cloudflare_challenge():
                    logger.info("Cloudflare 挑战已解决")
                    return True
                
                # 等待一段时间再检查
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"检查挑战状态时出错: {e}")
                time.sleep(2)
                
        return False
    
    def save_cookies(self, cookies: Dict[str, str], filename: str = "cloudflare_cookies.json"):
        """保存 cookies 到文件"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(cookies, f, indent=2, ensure_ascii=False)
            logger.info(f"Cookies 已保存到: {filename}")
        except Exception as e:
            logger.error(f"保存 cookies 失败: {e}")
    
    def close(self):
        """关闭浏览器"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("浏览器已关闭")
            except Exception as e:
                logger.error(f"关闭浏览器时出错: {e}")


def main():
    """主函数"""
    helper = CloudflareHelper(headless=False)  # 设置为 False 以便观察过程
    
    try:
        # 尝试获取 cf_clearance
        cookies = helper.get_cf_clearance("https://chat.akash.network/")
        
        if cookies:
            print("\n=== 获取到的 Cookies ===")
            for name, value in cookies.items():
                print(f"{name}: {value}")
            
            # 保存 cookies
            helper.save_cookies(cookies)
            
            # 检查关键 cookies
            if 'cf_clearance' in cookies:
                print(f"\n✅ 成功获取 cf_clearance: {cookies['cf_clearance'][:50]}...")
            else:
                print("\n❌ 未获取到 cf_clearance")
                
        else:
            print("❌ 获取 cookies 失败")
            
    finally:
        helper.close()


if __name__ == "__main__":
    main() 