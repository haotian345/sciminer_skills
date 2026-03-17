"""
SciMiner API 工具调用脚本

安全说明：
- API Key 从环境变量读取，不硬编码
- 文件上传为可选项，有则传，无则跳过
- 支持根据用户问题自动匹配工具

用法:
    # 方式1: 直接指定工具
    from scimin_tool import execute
    result = execute(
        tool_name="smiles_admet_post",
        provider_name="ADMET Predictor",
        parameters={"smiles": "CCO"}
    )
    
    # 方式2: 根据问题自动匹配（推荐）
    from scimin_tool import run_task
    result = run_task("预测CCO的ADMET性质")
    # 自动识别：ADMET Predictor, tool_name=smiles_admet_post
    
    # 方式3: 指定工具名，自动调用
    from scimin_tool import run_with_tool
    result = run_with_tool("ADMET Predictor", {"smiles": "CCO"})
"""

import os
import time
import requests
from typing import Dict, Optional, Union

# 导入工具注册表 - 支持相对和绝对导入
try:
    from .scimin_registry import find_tool, get_tool_info, TOOLS_REGISTRY
except ImportError:
    from scimin_registry import find_tool, get_tool_info, TOOLS_REGISTRY

BASE_URL = "https://sciminer.tech/console/api"
INVOKE_ENDPOINT = "/v1/internal/tools/invoke"
FILE_UPLOAD_ENDPOINT = "/v1/internal/tools/file"
RESULT_ENDPOINT = "/v1/internal/tools/result"

MAX_RETRIES = 300
POLL_INTERVAL = 2


def get_api_key():
    """从环境变量获取 API Key"""
    api_key = os.environ.get("SCIMINER_API_KEY")
    if not api_key:
        raise ValueError(
            "API Key 未配置。请设置环境变量: export SCIMINER_API_KEY=YOUR_API_KEY"
        )
    return api_key


def upload_file(file_path: str, api_key: str) -> str:
    """上传文件并返回 file_id"""
    if not file_path or not os.path.exists(file_path):
        return None
    
    with open(file_path, "rb") as f:
        files = {"file": (os.path.basename(file_path), f)}
        headers = {"X-Auth-Token": api_key}
        
        response = requests.post(
            f"{BASE_URL}{FILE_UPLOAD_ENDPOINT}",
            files=files,
            headers=headers,
            timeout=60
        )
        response.raise_for_status()
        
        file_id = response.json().get("file_id")
        return file_id


def process_parameters(parameters: dict, api_key: str) -> dict:
    """
    处理参数，自动识别文件路径并上传
    
    支持两种文件传参方式:
    1. 通过 file_path 参数上传
    2. 自动检测 parameters 中的文件路径并上传
    """
    if not parameters:
        return {}
    
    processed = parameters.copy()
    file_extensions = (".sdf", ".mol", ".mol2", ".smi", ".csv", ".xlsx", ".txt")
    
    for key, value in parameters.items():
        # 检查是否是文件路径
        if isinstance(value, str) and os.path.exists(value):
            if value.lower().endswith(file_extensions):
                file_id = upload_file(value, api_key)
                if file_id:
                    processed[key] = file_id
                    print(f"文件已上传: {os.path.basename(value)}, file_id: {file_id}")
    
    return processed


def invoke_tool(tool_name: str, parameters: dict = None, file_path: str = None, 
                api_key: str = None, provider_name: str = None, **kwargs) -> dict:
    """
    调用 SciMiner 工具
    
    Args:
        tool_name: 工具名称（必填）
        parameters: 工具参数字典
        file_path: 可选，文件路径（有则上传，无则跳过）
        api_key: 可选，API Key（默认从环境变量读取）
        provider_name: 可选，供应商名称
        **kwargs: 其他参数会合并到 parameters
    
    Returns:
        包含 status 和 result 的字典
    """
    if parameters is None:
        parameters = {}
    
    # 合并额外参数
    parameters.update(kwargs)
    
    # 获取 API Key
    if not api_key:
        api_key = get_api_key()
    
    headers = {
        "X-Auth-Token": api_key,
        "Content-Type": "application/json"
    }
    
    # 处理参数（自动检测文件上传）
    processed_params = process_parameters(parameters.copy(), api_key)
    
    # 构建 payload
    payload = {
        "tool_name": tool_name,
        "parameters": processed_params
    }
    
    # 添加 provider_name（如果提供）
    if provider_name:
        payload["provider_name"] = provider_name
    
    # 条件性文件上传：有 file_path 就传，没就跳过
    if file_path and os.path.exists(file_path):
        file_id = upload_file(file_path, api_key)
        if file_id:
            payload["parameters"]["file"] = file_id
            print(f"文件已上传，file_id: {file_id}")
    else:
        print("未提供文件或文件不存在，跳过文件上传步骤")
    
    # 提交任务
    try:
        response = requests.post(
            f"{BASE_URL}{INVOKE_ENDPOINT}",
            json=payload,
            headers=headers,
            timeout=30
        )
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        return {
            "status": "ERROR",
            "result": f"HTTP Error: {e.response.status_code} - {e.response.text}",
            "payload": payload
        }
    
    task_id = response.json().get("task_id")
    if not task_id:
        return {"status": "FAILURE", "result": "无法获取 task_id", "raw": response.json()}
    
    # 轮询结果
    return poll_result(task_id, api_key)


def poll_result(task_id: str, api_key: str) -> dict:
    """轮询任务结果"""
    headers = {"X-Auth-Token": api_key}
    
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(
                f"{BASE_URL}{RESULT_ENDPOINT}",
                params={"task_id": task_id},
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            return {
                "status": "ERROR",
                "result": f"查询结果失败: {e}"
            }
        
        result = response.json()
        status = result.get("status")
        
        if status == "SUCCESS":
            return {
                "status": "SUCCESS",
                "result": result.get("result"),
                "task_id": task_id
            }
        elif status == "FAILURE":
            return {
                "status": "FAILURE", 
                "result": result.get("result"),
                "task_id": task_id
            }
        
        time.sleep(POLL_INTERVAL)
    
    return {
        "status": "PENDING",
        "result": "超过最大重试次数",
        "task_id": task_id
    }


def execute(tool_name: str, parameters: dict = None, file_path: str = None, 
           api_key: str = None, provider_name: str = None, **kwargs) -> dict:
    """
    主入口函数
    
    Args:
        tool_name: SciMiner 工具名称
        parameters: 工具参数字典
        file_path: 可选的文件路径
        api_key: 可选的 API Key
        provider_name: 可选的供应商名称
        **kwargs: 额外的参数，会合并到 parameters
    
    Returns:
        执行结果字典 {"status": "SUCCESS|FAILURE|PENDING", "result": ..., "task_id": ...}
    """
    return invoke_tool(tool_name, parameters, file_path, api_key, provider_name, **kwargs)


def run_with_tool(tool_name: str, parameters: dict = None, **kwargs) -> dict:
    """
    通过工具名称调用（自动填充 provider_name）
    
    Args:
        tool_name: 工具名称（如 "ADMET Predictor"）
        parameters: 参数字典
        **kwargs: 其他参数
    
    Returns:
        执行结果
    """
    tool_info = get_tool_info(tool_name)
    if not tool_info:
        return {"status": "ERROR", "result": f"未找到工具: {tool_name}"}
    
    return execute(
        tool_name=tool_info.get("default_tool_name", tool_name),
        provider_name=tool_info.get("provider_name"),
        parameters=parameters,
        **kwargs
    )


def run_task(user_query: str, parameters: dict = None, **kwargs) -> dict:
    """
    根据用户问题自动匹配工具并执行（核心功能）
    
    这是最智能的调用方式，用户只需要描述想要做什么，
    系统会自动:
    1. 分析用户问题
    2. 匹配最合适的工具
    3. 填充必要的参数
    4. 执行调用
    
    Args:
        user_query: 用户问题，如 "预测CCO的ADMET性质"
        parameters: 用户提供的参数（如有）
        **kwargs: 其他参数
    
    Returns:
        执行结果，包含匹配的工具信息
    """
    # 1. 自动搜索工具
    tool_info = find_tool(user_query)
    
    if not tool_info:
        # 尝试直接使用 tool_name
        if parameters:
            return execute(
                tool_name=user_query if isinstance(user_query, str) else "unknown",
                parameters=parameters,
                **kwargs
            )
        return {
            "status": "ERROR",
            "result": f"无法从问题 '{user_query}' 识别出对应的工具，请明确指定工具名称",
            "suggestions": list(TOOLS_REGISTRY.keys())
        }
    
    print(f"🔍 自动匹配工具: {tool_info['name']}")
    print(f"   描述: {tool_info.get('description')}")
    print(f"   tool_name: {tool_info.get('default_tool_name')}")
    
    # 2. 构建参数
    final_params = parameters or {}
    final_params.update(kwargs)
    
    # 3. 执行调用
    result = execute(
        tool_name=tool_info.get("default_tool_name"),
        provider_name=tool_info.get("provider_name"),
        parameters=final_params
    )
    
    # 4. 添加工具信息到结果
    result["matched_tool"] = tool_info["name"]
    
    return result


if __name__ == "__main__":
    import sys
    
    # 测试自动匹配
    print("=== 测试自动工具匹配 ===")
    
    test_cases = [
        ("预测CCO的ADMET性质", {"smiles": "CCO"}),
        ("计算分子的pKa值", {"smiles": "CCO"}),
    ]
    
    for query, params in test_cases:
        print(f"\n查询: {query}")
        print(f"参数: {params}")
        
        tool_info = find_tool(query)
        if tool_info:
            print(f"  ✅ 匹配: {tool_info['name']}")
            print(f"     tool_name: {tool_info.get('default_tool_name')}")
        else:
            print(f"  ❌ 未匹配到工具")
