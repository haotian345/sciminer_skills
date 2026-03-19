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

# 导入工具注册表 - 支持相对和绝对导入
try:
    from .scimin_registry import find_tool, get_tool_info, TOOLS_REGISTRY
except ImportError:
    from scimin_registry import find_tool, get_tool_info, TOOLS_REGISTRY

BASE_URL = "https://sciminer.tech/console/api"
INVOKE_ENDPOINT = "/v1/internal/tools/invoke"
FILE_UPLOAD_ENDPOINT = "/v1/internal/tools/file"
RESULT_ENDPOINT = "/v1/internal/tools/result"

MAX_RETRIES = 900
POLL_INTERVAL = 2
SHARE_URL_TEMPLATE = "https://sciminer.tech/share?id={task_id}&type=API_TOOL"


def build_share_url(task_id: str) -> str:
    """根据 task_id 构建分享链接"""
    if not task_id:
        return ""
    return SHARE_URL_TEMPLATE.format(task_id=task_id)

# 安全配置
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
ALLOWED_EXTENSIONS = {".sdf", ".mol", ".mol2", ".smi", ".csv", ".xlsx", ".txt"}


def sanitize_string(s: str, max_len: int = 1000) -> str:
    """清理字符串，防止日志注入"""
    if not isinstance(s, str):
        return ""
    # 移除控制字符
    return "".join(c for c in s if ord(c) >= 32 or c in "\n\r\t")[:max_len]


def validate_tool_name(tool_name: str) -> bool:
    """验证 tool_name 是否有效，支持友好名或内部接口名。"""
    if not tool_name:
        return False
    try:
        from .scimin_registry import get_tool_info as _get
    except Exception:
        from scimin_registry import get_tool_info as _get

    return _get(tool_name) is not None


def validate_file_path(file_path: str) -> tuple[bool, str]:
    """验证文件路径安全性：允许绝对路径，要求存在、不是目录、后缀受限且大小合规。"""
    if not file_path:
        return False, ""

    # 解析真实路径（处理符号链接）
    try:
        real_path = os.path.realpath(file_path)
    except Exception:
        return False, "路径无法解析"

    # 必须存在且为文件
    if not os.path.exists(real_path):
        return False, "文件不存在"
    if not os.path.isfile(real_path):
        return False, "不是一个常规文件"

    # 检查扩展名
    ext = os.path.splitext(real_path)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return False, f"不支持的文件类型: {ext}"

    # 检查文件大小
    try:
        size = os.path.getsize(real_path)
        if size > MAX_FILE_SIZE:
            size_mb = size // (1024 * 1024)
            max_mb = MAX_FILE_SIZE // (1024 * 1024)
            return False, f"文件过大: {size_mb}MB > {max_mb}MB"
    except OSError:
        return False, "无法读取文件大小"

    return True, ""


def get_api_key():
    """从环境变量获取 API Key"""
    api_key = os.environ.get("SCIMINER_API_KEY")
    if not api_key:
        raise ValueError(
            "API Key 未配置。请设置环境变量: export SCIMINER_API_KEY=YOUR_API_KEY"
        )
    return api_key


def upload_file(file_path: str, api_key: str) -> str:
    """上传文件并返回 file_id；任何网络或解析错误返回 None。"""
    if not file_path:
        return None

    # 先解析真实路径，再验证
    real_path = os.path.realpath(file_path)
    is_valid, error_msg = validate_file_path(real_path)
    if not is_valid:
        print(f"⚠️ 文件验证失败: {error_msg}")
        return None

    try:
        with open(real_path, "rb") as f:
            files = {"file": (os.path.basename(real_path), f)}
            headers = {"X-Auth-Token": api_key}

            try:
                response = requests.post(
                    f"{BASE_URL}{FILE_UPLOAD_ENDPOINT}",
                    files=files,
                    headers=headers,
                    timeout=60
                )
            except requests.exceptions.RequestException as e:
                print(f"⚠️ 文件上传失败（网络错误）: {e}")
                return None

            try:
                response.raise_for_status()
            except requests.exceptions.HTTPError:
                print(f"⚠️ 文件上传返回非200: {response.status_code} - {response.text}")
                return None

            try:
                file_id = response.json().get("file_id")
            except ValueError:
                print("⚠️ 解析文件上传响应失败（非 JSON）")
                return None

            return file_id
    except OSError as e:
        print(f"⚠️ 无法打开文件: {e}")
        return None


def process_parameters(parameters: dict, api_key: str, file_param_names: list = None):
    """
    处理参数，自动识别文件路径并上传
    
    支持两种文件传参方式:
    1. 通过 file_path 参数上传
    2. 自动检测 parameters 中的文件路径并上传
    """
    if not parameters:
        return {}

    processed = parameters.copy()
    file_param_names = file_param_names or []

    for key, value in list(parameters.items()):
        # 仅对明确在 file_param_names 中的参数或常见文件字段执行上传
        is_declared_file = (
            key in file_param_names
            or key.lower()
            in {"file", "file_path", "filepath", "path", "protein", "ligand"}
        )

        if is_declared_file and isinstance(value, str) and os.path.exists(value):
            is_valid, error_msg = validate_file_path(value)
            if is_valid:
                file_id = upload_file(value, api_key)
                if file_id:
                    processed[key] = file_id
                    print(f"文件已上传: {os.path.basename(value)}, file_id: {file_id}")
            else:
                print(f"⚠️ 跳过不安全文件 {key}: {error_msg}")

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
    # 🔒 安全验证: tool_name 必须有效
    if not validate_tool_name(tool_name):
        return {
            "status": "ERROR",
            "result": f"无效的工具名称: {sanitize_string(tool_name, 100)}",
            "allowed_tools": list(TOOLS_REGISTRY.keys())
        }

    # 获取工具元信息（支持友好名或内部名）
    tool_info = None
    try:
        tool_info = get_tool_info(tool_name)
    except Exception:
        tool_info = None
    
    # 清理 provider_name（如果有）
    if provider_name:
        provider_name = sanitize_string(provider_name, 200)
    
    headers = {
        "X-Auth-Token": api_key,
        "Content-Type": "application/json"
    }

    # 处理参数（自动检测文件上传），优先使用 registry 中声明的 file_params
    declared_files = []
    if tool_info:
        declared_files = tool_info.get("file_params", [])

    processed_params = process_parameters(parameters.copy(), api_key, file_param_names=declared_files)

    # 选择要发送给 API 的 tool_name（如果 registry 提供 internal name 则使用它）
    api_tool_name = tool_name
    if tool_info and tool_info.get("tool_name"):
        api_tool_name = tool_info.get("tool_name")

    # 构建 payload
    payload = {
        "tool_name": api_tool_name,
        "parameters": processed_params
    }
    
    # 添加 provider_name（如果提供）
    if provider_name:
        payload["provider_name"] = provider_name
    
    # 条件性文件上传：有 file_path 就传，没就跳过
    if file_path:
        if os.path.exists(file_path):
            file_id = upload_file(file_path, api_key)
            if file_id:
                payload["parameters"]["file"] = file_id
                print(f"文件已上传，file_id: {file_id}")
        else:
            print("未提供文件或文件不存在，跳过文件上传步骤")
    
    # 提交任务
    try:
        try:
            response = requests.post(
                f"{BASE_URL}{INVOKE_ENDPOINT}",
                json=payload,
                headers=headers,
                timeout=30
            )
        except requests.exceptions.RequestException as e:
            return {"status": "ERROR", "result": f"请求失败: {e}", "payload": payload}

        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError:
            # 避免泄露敏感信息
            text = response.text[:1000]
            return {"status": "ERROR", "result": f"HTTP Error: {response.status_code} - {text}", "payload": payload}

        try:
            data = response.json()
        except ValueError:
            return {"status": "ERROR", "result": "无法解析响应（非 JSON）", "payload": response.text}

    except Exception as e:
        return {"status": "ERROR", "result": f"未知错误: {e}", "payload": payload}

    task_id = data.get("task_id")
    if not task_id:
        return {"status": "FAILURE", "result": "无法获取 task_id", "raw": data}
    
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
        except requests.exceptions.RequestException as e:
            return {"status": "ERROR", "result": f"查询结果请求失败: {e}", "task_id": task_id, "share_url": build_share_url(task_id)}

        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError:
            return {"status": "ERROR", "result": f"查询结果返回错误: {response.status_code}", "task_id": task_id, "share_url": build_share_url(task_id)}

        try:
            result = response.json()
        except ValueError:
            return {"status": "ERROR", "result": "解析查询响应失败（非 JSON）", "task_id": task_id, "share_url": build_share_url(task_id)}

        status = result.get("status")

        if status == "SUCCESS":
            return {"status": "SUCCESS", "result": result.get("result"), "task_id": task_id, "share_url": build_share_url(task_id)}
        if status == "FAILURE":
            return {"status": "FAILURE", "result": result.get("result"), "task_id": task_id, "share_url": build_share_url(task_id)}

        time.sleep(POLL_INTERVAL)
    
    return {
        "status": "PENDING",
        "result": "超过最大重试次数",
        "task_id": task_id,
        "share_url": build_share_url(task_id)
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
    # 安全验证
    if not validate_tool_name(tool_name):
        return {
            "status": "ERROR", 
            "result": f"未找到工具: {sanitize_string(tool_name, 100)}",
            "allowed_tools": list(TOOLS_REGISTRY.keys())
        }
    
    tool_info = get_tool_info(tool_name)
    
    return execute(
        tool_name=tool_info.get("name", tool_name),
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
    # 安全：清理用户输入
    safe_query = sanitize_string(user_query, 500)
    
    # 1. 自动搜索工具
    tool_info = find_tool(safe_query)
    
    if not tool_info:
        return {
            "status": "ERROR",
            "result": f"无法从问题 '{safe_query[:50]}...' 识别出对应的工具，请明确指定工具名称",
            "suggestions": list(TOOLS_REGISTRY.keys())
        }
    
    # 安全日志输出
    print(f"🔍 自动匹配工具: {sanitize_string(tool_info['name'], 100)}")
    print(f"   描述: {sanitize_string(tool_info.get('description', ''), 200)}")
    print(f"   tool_name: {tool_info.get('tool_name', 'N/A')}")
    
    # 2. 构建参数
    final_params = parameters or {}
    final_params.update(kwargs)
    
    # 3. 执行调用
    result = execute(
        tool_name=tool_info.get("tool_name"),
        provider_name=tool_info.get("provider_name"),
        parameters=final_params
    )
    
    # 4. 添加工具信息到结果
    result["matched_tool"] = tool_info["name"]
    
    return result


if __name__ == "__main__":
    
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
            print(f"     tool_name: {tool_info.get('tool_name')}")
        else:
            print("  ❌ 未匹配到工具")
