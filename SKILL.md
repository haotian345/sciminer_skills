---
name: scimin-api
description: 调用 SciMiner (https://sciminer.tech) 药物设计工具 API。支持 ADMET 预测、分子描述符计算、专利检索等多种工具。用于：(1) 调用 SciMiner 的各种计算工具，(2) 上传分子文件进行批量处理，(3) 查询专利信息获取化合物结构。API Key 需要在首次使用时配置。
---

# SciMiner API 调用

## 配置

首次使用需要配置 API Key：

```
openclaw config set scimin.api_key YOUR_API_KEY
```

可在 https://sciminer.tech/console 获取 API Key。

## 使用方法

### 基本调用

```python
from scripts.scimin_tool import execute

result = execute(
    tool_name="query_patentid_to_file_query_patentid_to_file_get",
    parameters={"patent_id": "CN112345678"},
    # 可选：上传文件
    # file_path="/path/to/molecule.sdf"
)
```

### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| tool_name | string | 是 | SciMiner 工具名称，如 `query_patentid_to_file_query_patentid_to_file_get` |
| parameters | dict | 是 | 工具参数字典 |
| file_path | string | 否 | 需要上传的文件路径，有则上传，无则跳过 |
| provider_name | string | 否 | 供应商名称，如 `Get Mol From Patent` |

### 可用工具示例

- `admet_predict` - ADMET 预测
- `molecular_descriptors` - 分子描述符计算
- `query_patentid_to_file_query_patentid_to_file_get` - 专利检索

### 返回结果

返回包含 `status` 和 `result` 的字典。成功时 `status` 为 `"SUCCESS"`，失败时为 `"FAILURE"`。

## 注意事项

- API Key 仅存储在本地配置，不会在代码中暴露
- 文件上传为可选项，不传文件时自动跳过上传步骤
- 长时间任务会自动轮询，最多等待 10 分钟
