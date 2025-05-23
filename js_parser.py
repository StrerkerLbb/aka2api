import re
import json
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("js-parser")

def extract_models_from_js(js_content):
    """
    从JavaScript文件中提取模型列表
    
    Args:
        js_content: JavaScript文件的内容
    
    Returns:
        list: 模型列表
    """
    try:
        # 尝试匹配模型数组定义
        # 首先尝试匹配完整的数组定义
        # 在JS文件中，模型列表定义在module ID 68382中
        # 格式为: 68382:(e,t,a)=>{a.d(t,{$I:()=>r,Jn:()=>o});var n=a(2818);let o=[{...}]
        model_array_match = re.search(r'68382[^{]*\{[^{]*\$I[^{]*Jn[^{]*o\}\)[^{]*let\s+o\s*=\s*(\[.*?\])(?=,r\s*=|;)', js_content, re.DOTALL)
        
        if model_array_match:
            # 提取数组文本
            array_text = model_array_match.group(1)
            logger.info(f"找到模型数组定义，长度: {len(array_text)}")
            
            # 直接从数组文本中提取模型对象
            model_objects = []
            
            # 使用正则表达式提取每个模型对象的关键属性
            pattern = r'\{id:"([^"]+)",name:"([^"]+)",description:"([^"]+)".*?available:(!0|true)'
            matches = re.finditer(pattern, array_text, re.DOTALL)
            
            for match in matches:
                model_id = match.group(1)
                name = match.group(2)
                description = match.group(3)
                available = match.group(4) in ["!0", "true"]
                
                if available:  # 只添加可用的模型
                    model_objects.append({
                        "id": model_id,
                        "name": name,
                        "description": description
                    })
            
            if model_objects:
                logger.info(f"成功提取 {len(model_objects)} 个模型")
                return model_objects
            else:
                logger.warning("无法从数组文本中提取模型对象")
        else:
            logger.warning("无法找到模型数组定义")
        
        # 如果上面的方法失败，尝试直接搜索模型ID
        logger.info("尝试直接搜索模型ID")
        model_objects = []
        model_ids = [
            "DeepSeek-R1", 
            "Qwen3-235B-A22B-FP8", 
            "meta-llama-Llama-4-Maverick-17B-128E-Instruct-FP8",
            "nvidia-Llama-3-3-Nemotron-Super-49B-v1", 
            "Qwen-QwQ-32B", 
            "Meta-Llama-3-3-70B-Instruct",
            "Meta-Llama-3-1-405B-Instruct-FP8", 
            "AkashGen"
        ]
        
        for model_id in model_ids:
            # 注意JS中available可能是!0（JavaScript中的true）
            pattern = r'id:"' + re.escape(model_id) + r'".*?name:"([^"]+)".*?description:"([^"]+)".*?available:(!0|true)'
            model_match = re.search(pattern, js_content, re.DOTALL)
            
            if model_match:
                model_objects.append({
                    "id": model_id,
                    "name": model_match.group(1),
                    "description": model_match.group(2)
                })
        
        if model_objects:
            logger.info(f"通过直接搜索找到 {len(model_objects)} 个模型")
            return model_objects
        
        # 如果所有方法都失败，返回一个默认模型列表
        logger.warning("所有提取方法都失败，返回默认模型列表")
        return [
            {"id": "DeepSeek-R1", "name": "DeepSeek R1 671B", "description": "Strong Mixture-of-Experts (MoE) LLM"},
            {"id": "Qwen3-235B-A22B-FP8", "name": "Qwen3 235B A22B", "description": "Advanced reasoning model with 235B parameters (22B active)"},
            {"id": "meta-llama-Llama-4-Maverick-17B-128E-Instruct-FP8", "name": "Llama 4 Maverick 17B 128E", "description": "400B parameter model (17B active) with 128 experts"},
            {"id": "nvidia-Llama-3-3-Nemotron-Super-49B-v1", "name": "Llama 3.3 Nemotron Super 49B", "description": "Great tradeoff between model accuracy and efficiency"},
            {"id": "Qwen-QwQ-32B", "name": "Qwen QwQ-32B", "description": "Medium-sized reasoning model with enhanced performance"},
            {"id": "Meta-Llama-3-3-70B-Instruct", "name": "Llama 3.3 70B", "description": "Well-rounded model with strong capabilities"},
            {"id": "Meta-Llama-3-1-405B-Instruct-FP8", "name": "Llama 3.1 405B", "description": "Most capable model for complex tasks"},
            {"id": "AkashGen", "name": "AkashGen", "description": "Generate images using AkashGen"}
        ]
    
    except Exception as e:
        logger.error(f"提取模型列表时出错: {e}", exc_info=True)
        # 返回一个默认模型
        return [{"id": "DeepSeek-R1", "name": "DeepSeek R1 671B", "description": "Strong Mixture-of-Experts (MoE) LLM"}]

# 测试函数
if __name__ == "__main__":
    import requests
    
    try:
        # 获取JavaScript文件
        response = requests.get(
            "https://chat.akash.network/_next/static/chunks/939-e56b9689ddc1242a.js",
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36"
            }
        )
        
        if response.status_code == 200:
            # 提取模型列表
            models = extract_models_from_js(response.text)
            print(f"找到 {len(models)} 个模型:")
            for model in models:
                print(f"- {model['id']}: {model['name']} - {model['description']}")
        else:
            print(f"获取JavaScript文件失败: {response.status_code}")
    
    except Exception as e:
        print(f"测试时出错: {e}")