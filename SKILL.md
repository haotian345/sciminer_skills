---
name: scimin-api
description: 调用 SciMiner (https://sciminer.tech) 药物设计工具 API。支持根据用户问题自动匹配工具，支持 ADMET 预测、分子描述符计算、专利检索等多种工具。用于调用 SciMiner 的各种计算工具，上传分子文件进行批量处理，查询专利信息获取化合物结构。API Key 通过环境变量 SCIMINER_API_KEY 配置。
metadata:
  {
    "openclaw":
      {
        "requires":
          {
            "env": ["SCIMINER_API_KEY"],
            "bins": ["python3"],
          },
      },
  }
---

# SciMiner API 工具

> ⚠️ **安装前必读**：本 skill 需要 SciMiner API Key 才能使用。

## 前置要求

### 1. 获取 API Key

如果没有 API Key，请先访问 **[https://sciminer.tech/utility](https://sciminer.tech/utility)** 生成：

1. 登录 SciMiner 账号
2. 进入「工具」页面
3. 点击「生成 API Key」或类似按钮
4. 复制生成的 Key

### 2. 配置环境变量

```bash
# 方式一：当前终端生效
export SCIMINER_API_KEY=你的APIKey

# 方式二：持久化（添加到 ~/.bashrc 或 ~/.zshrc）
echo 'export SCIMINER_API_KEY=你的APIKey' >> ~/.bashrc
source ~/.bashrc
```

### 3. 在 OpenClaw 中配置

在 `~/.openclaw/openclaw.json` 的 `skills.entries` 中添加：

```json
{
  "skills": {
    "entries": {
      "scimin-api": {
        "enabled": true,
        "env": {
          "SCIMINER_API_KEY": "你的APIKey"
        }
      }
    }
  }
}
```

> **注意**：安装本 skill 前，请确保已完成以上步骤。未配置 API Key 将导致 skill 无法正常使用。

## 快速开始

### 配置 API Key

```bash
export SCIMINER_API_KEY=your_api_key_here
```

### 最智能的调用方式（推荐）

用户只需要描述想要做什么，系统自动匹配工具：

```python
from scimin_tool import run_task

# 自动识别为 ADMET Predictor
result = run_task("预测分子的ADMET性质", {"smiles": "CCO"})

# 自动识别为 Graph-pKa
result = run_task("计算分子的pKa值", {"smiles": "CCO"})

# 自动识别为 Get Mol From Patent
result = run_task("从专利中提取分子结构", {"patent_id": "CN112345678"})
```

### 指定工具调用

```python
from scimin_tool import run_with_tool, execute

# 通过工具名调用
result = run_with_tool("ADMET Predictor", {"smiles": "CCO"})

# 直接指定参数
result = execute(
    tool_name="smiles_admet_post",
    provider_name="ADMET Predictor",
    parameters={"smiles": "CCO"}
)
```

### 文件上传

**方式1：通过 file_path 参数**

```python
result = run_with_tool(
    "ADMET Predictor",
    parameters={"features": ["HCT"]},
    file_path="/path/to/molecules.sdf"
)
```

**方式2：参数中直接传文件路径**

```python
result = run_with_tool(
    "ADMET Predictor", 
    parameters={
        "file": "/path/to/molecules.sdf"  # 自动识别上传
    }
)
```

### 返回结果

```python
{
    "status": "SUCCESS",      # SUCCESS | FAILURE | PENDING | ERROR
    "result": {...},          # 任务结果
    "task_id": "xxx",         # 任务ID
    "matched_tool": "xxx"     # 自动匹配时返回
}
```

## 自动匹配工具

系统会根据问题自动识别合适的工具：

| 用户问题 | 匹配工具 | tool_name |
|----------|----------|-----------|
| 预测ADMET | ADMET Predictor | `smiles_admet_post` |
| 药代动力学 | ADMET Predictor | `smiles_admet_post` |
| 口服生物利用度 | αOBA | - |
| pKa值 | Graph-pKa | - |
| 类药性 | Check Lipinski | - |
| PAINS | Check PAINS | - |
| 专利提取 | Get Mol From Patent | `query_patentid_to_file_*` |
| 分子描述符 | Molecular Descriptors | - |
| 合成可及性 | SAScore | - |
| 蛋白配体相互作用 | PLIP Analysis | - |

## 常用工具列表

完整列表请参考 `scimin_registry.py`：

```python
from scimin_registry import list_tools, get_tool_info, list_categories

# 列出所有类别
print(list_categories())

# 列出所有工具
print(list_tools())

# 获取具体工具信息
info = get_tool_info("ADMET Predictor")
```

## 完整参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| tool_name | string | 是 | SciMiner 工具名称 |
| parameters | dict | 是 | 工具参数，完全动态 |
| provider_name | string | 否 | 供应商名称 |
| file_path | string | 否 | 上传文件路径 |
| api_key | string | 否 | API Key（默认从环境变量读取） |
| **kwargs | any | 否 | 额外参数，会合并到 parameters |

## 注意事项

- API Key 仅从环境变量读取，不写入代码
- 文件上传为可选项，不传文件时自动跳过
- 长时间任务自动轮询，最多等待 10 分钟
- 推荐使用 `run_task()` 智能匹配方式
