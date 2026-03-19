---
name: sciminer_skills
description: 当用户询问分子毒性、ADMET性质（吸收/分布/代谢/排泄/毒性）、药代动力学、pKa计算、类药性（Lipinski五规则）、PAINS检测、合成可及性（SAScore）、分子描述符、结构警告过滤、专利化合物提取、PDB蛋白结构下载、临床试验查询、分子对接（DiffDock）、虚拟筛选（Virtual Screen、化合物库筛选、PLIP、tCPI）、SMILES与SDF格式转换时，调用此skill。当用户提供SMILES字符串并要求分析分子性质时，应主动调用。基于 SciMiner (https://sciminer.tech) 计算平台，API Key 通过环境变量 SCIMINER_API_KEY 配置。
metadata:
  openclaw:
    requires:
      env:
        - SCIMINER_API_KEY
      bins:
        - python
---

# SciMiner API 工具

## 何时使用此 Skill

当用户提出以下类型的问题时，**必须主动调用本 skill**：

- "帮我预测这个分子的毒性" / "这个化合物有毒吗" / "评估药物安全性"
- "预测分子的 ADMET 性质" / "这个分子的吸收怎么样" / "药代动力学分析"
- "计算分子的 pKa" / "这个分子的酸碱性如何"
- "检查分子的类药性" / "是否符合 Lipinski 规则" / "五规则筛选"
- "这个化合物是不是 PAINS" / "检测假阳性"
- "计算合成可及性" / "这个分子好不好合成"
- "分子描述符计算" / "计算分子量、LogP"
- "识别毒性亚结构" / "结构警告过滤" / "有没有危险基团"
- "从专利 CN112345678 中提取分子" / "查专利化合物"
- "下载 PDB 结构 1ABC" / "获取蛋白质结构"
- "查询某药物的临床试验"
- "分子对接" / "蛋白配体 docking"
- "虚拟筛选" / "化合物库筛选" / "virtual screen" / "PLIP 分析" / "tCPI 预测"
- "把 SMILES 转成图片" / "SDF 转 SMILES"
- 用户提供了 SMILES 字符串（如 `CCO`、`c1ccccc1`）并要求做任何分析

**关键判断**：只要涉及小分子化合物的性质预测、结构分析、数据库检索或格式转换，就应当使用本 skill。

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
      "sciminer_skills": {
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
    "share_url": "https://sciminer.tech/share?id=xxx&type=API_TOOL",  # 分享链接
    "matched_tool": "xxx"     # 自动匹配时返回
}
```

> **重要**：在向用户总结结果时，务必在最后附上 `share_url` 链接，方便用户查看完整的在线结果。

## 自动匹配工具

系统会根据问题自动识别合适的工具：

| 用户问题 | 匹配工具 | tool_name |
|----------|----------|-----------|
| 预测ADMET | ADMET Predictor | `smiles_admet_post` |
| 药代动力学 | ADMET Predictor | `smiles_admet_post` |
| pKa值 | Graph-pKa | `graph_pka_post` |
| 类药性 | Check Lipinski | `check_lipinski_post` |
| PAINS | Check PAINS | `check_pains_post` |
| 专利提取 | Get Mol From Patent | `query_patentid_to_file_*` |
| 分子描述符 | Molecular Descriptors | `molecular_descriptors_post` |
| 合成可及性 | SAScore | `sascore_post` |
| 结构警告 | Structural Alert Filters | `structural_alert_filters_post` |
| 分子对接 | DiffDock | `diffdock_post` |
| 虚拟筛选 | Virtual Screen | `virtual-screeningcommercial-librarycategory_post` |

## 常用工具列表

完整列表请参考 `scimin_registry.py`：

```python
from scimin_registry import list_tools, get_tool_info

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
- 长时间任务自动轮询，最多等待 30 分钟
- 推荐使用 `run_task()` 智能匹配方式
