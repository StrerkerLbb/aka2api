#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动安装 cf_clearance 获取助手的依赖
"""

import subprocess
import sys
import os

def install_package(package):
    """安装Python包"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✅ 成功安装: {package}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 安装失败: {package} - {e}")
        return False

def main():
    """主安装函数"""
    print("🚀 开始安装 cf_clearance 获取助手的依赖...")
    
    # 需要安装的包列表
    required_packages = [
        "undetected-chromedriver",
        "selenium",
        "requests"
    ]
    
    success_count = 0
    total_packages = len(required_packages)
    
    for package in required_packages:
        print(f"\n📦 正在安装: {package}")
        if install_package(package):
            success_count += 1
    
    print(f"\n{'='*50}")
    print(f"安装完成！成功: {success_count}/{total_packages}")
    
    if success_count == total_packages:
        print("🎉 所有依赖安装成功！")
        print("\n📋 使用说明:")
        print("1. 运行: python auto_cf_helper.py")
        print("2. 脚本将自动打开浏览器并尝试获取 cf_clearance")
        print("3. 如果遇到 Cloudflare 挑战，请耐心等待自动解决")
        print("4. cookies 将保存到 cloudflare_cookies.json 文件中")
        
        print("\n⚠️  注意事项:")
        print("- 首次运行可能需要下载 Chrome 驱动，请耐心等待")
        print("- 建议在网络环境良好时运行")
        print("- 如果失败，可以尝试多次运行")
        
    else:
        print("❌ 部分依赖安装失败，请检查网络连接或手动安装")
        print("\n手动安装命令:")
        for package in required_packages:
            print(f"pip install {package}")

if __name__ == "__main__":
    main() 