# OpenAI to Akash Network 代理服务器启动脚本 v2.0

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "OpenAI to Akash Network 代理服务器" -ForegroundColor Cyan  
Write-Host "========================================" -ForegroundColor Cyan

Write-Host "正在激活虚拟环境..." -ForegroundColor Green
& .\.venv\Scripts\Activate.ps1

Write-Host "`n请选择启动模式:" -ForegroundColor Yellow
Write-Host "1. 直接启动服务器 (如果已有有效cookies)" -ForegroundColor White
Write-Host "2. 半自动化获取 cf_clearance 后启动" -ForegroundColor White  
Write-Host "3. 安装/更新 cf_clearance 获取工具依赖" -ForegroundColor White
Write-Host "4. 仅获取 cf_clearance (不启动服务器)" -ForegroundColor White

$choice = Read-Host "`n请输入选择 (1-4)"

switch ($choice) {
    "1" {
        Write-Host "`n正在直接启动服务器..." -ForegroundColor Green
        python openai_to_akash_proxy.py
    }
    "2" {
        Write-Host "`n正在半自动化获取 cf_clearance..." -ForegroundColor Green
        Write-Host "提示：浏览器窗口会自动打开，请耐心等待 Cloudflare 挑战解决" -ForegroundColor Yellow
        python auto_cf_helper.py
        
        Write-Host "`n现在启动服务器..." -ForegroundColor Green
        python openai_to_akash_proxy.py
    }
    "3" {
        Write-Host "`n正在安装/更新依赖..." -ForegroundColor Green
        python install_cf_helper.py
        
        Write-Host "`n安装完成！现在您可以重新运行此脚本选择选项 2 或 4" -ForegroundColor Yellow
    }
    "4" {
        Write-Host "`n正在获取 cf_clearance..." -ForegroundColor Green
        python auto_cf_helper.py
        
        Write-Host "`ncookies 已保存，您可以稍后启动服务器" -ForegroundColor Yellow
    }
    default {
        Write-Host "`n无效选择，默认启动服务器..." -ForegroundColor Red
        python openai_to_akash_proxy.py
    }
}

Write-Host "`n服务器已停止" -ForegroundColor Yellow
Write-Host "按任意键退出..." -ForegroundColor Gray
Read-Host 