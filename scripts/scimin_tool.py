"""
SciMiner API 工具调用脚本

安全说明：
- API Key 从配置读取，不硬编码
- 文件上传为可选项，有则传，无则跳过
- 不在日志中打印敏感信息
"""

import os
import time
import requests

BASE_URL = "https://sciminer.tech/console/api"
INVOKE_ENDPOINT = "/v1/internal/tools/invoke"
FILE_UPLOAD_ENDPOINT = "/v1/internal/tools/file"
RESULT_ENDPOINT = "/v1/internal/tools/result"

MAX_RETRIES = 300
POLL_INTERVAL = 2


def get_api_key():
    """从配置获取 API Key"""
    # 尝试从环境变量或配置文件读取
    api_key = os.environ.get("SCIMINER_API_KEY")
    if not api_key:
        raise ValueError(
            "API Key 未配置。请运行: openclaw config set scimin.api_key YOUR_API_KEY\n"
            "或设置环境变量: export SCIMINER_API_KEY=YOUR_API_KEY"
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


def invoke_tool(tool_name: str, parameters: dict, file_path: str = None, api_key: str = None, provider_name: str = None) -> dict:
    """
    调用 SciMiner 工具
    
    Args:
        tool_name: 工具名称
        parameters: 参数字典
        file_path: 可选，文件路径（有则上传，无则跳过）
        api_key: API Key（可选，默认从配置读取）
        provider_name: 可选，供应商名称
    
    Returns:
        包含 status 和 result 的字典
    """
    # 获取 API Key
    if not api_key:
        api_key = get_api_key()
    
    headers = {
        "X-Auth-Token": api_key,
        "Content-Type": "application/json"
    }
    
    # 构建 payload
    payload = {
        "tool_name": tool_name,
        "parameters": parameters.copy()
    }
    
    # 添加 provider_name（如果提供）
    if provider_name:
        payload["provider_name"] = provider_name
    
    # 条件性文件上传：有文件就传，没文件就跳过
    if file_path and os.path.exists(file_path):
        file_id = upload_file(file_path, api_key)
        if file_id:
            # 将 file_id 放入参数（工具会自动识别）
            # 注意：具体参数名需根据工具定义，此处为通用处理
            payload["parameters"]["file"] = file_id
            print(f"文件已上传，file_id: {file_id}")
    else:
        print("未提供文件或文件不存在，跳过文件上传步骤")
    
    # 提交任务
    response = requests.post(
        f"{BASE_URL}{INVOKE_ENDPOINT}",
        json=payload,
        headers=headers,
        timeout=30
    )
    response.raise_for_status()
    
    task_id = response.json().get("task_id")
    if not task_id:
        return {"status": "FAILURE", "result": "无法获取 task_id"}
    
    # 轮询结果
    return poll_result(task_id, api_key)


def poll_result(task_id: str, api_key: str) -> dict:
    """轮询任务结果"""
    headers = {"X-Auth-Token": api_key}
    
    for attempt in range(MAX_RETRIES):
        response = requests.get(
            RESULT_ENDPOINT,
            params={"task_id": task_id},
            headers=headers,
            timeout=10
        )
        response.raise_for_status()
        
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


def execute(tool_name: str, parameters: dict, file_path: str = None, api_key: str = None, provider_name: str = None) -> dict:
    """
    主入口函数，供外部调用
    
    Args:
        tool_name: SciMiner 工具名称
        parameters: 工具参数字典
        file_path: 可选的文件路径
        api_key: 可选的 API Key
        provider_name: 可选的供应商名称
    
    Returns:
        执行结果字典
    """
    return invoke_tool(tool_name, parameters, file_path, api_key, provider_name)


if __name__ == "__main__":
    # 测试调用示例
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python scimin_tool.py <tool_name> [file_path]")
        sys.exit(1)
    
    tool_name = sys.argv[1]
    file_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    # 示例参数（实际使用时根据工具调整）
    parameters = {"test_param": "value"}
    
    result = execute(tool_name, parameters, file_path)
    print(f"结果: {result}")
