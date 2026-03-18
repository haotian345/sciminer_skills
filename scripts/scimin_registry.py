"""
SciMiner 工具注册表 - 完整版
包含所有支持 API 调用的工具信息及参数定义
"""

TOOLS_REGISTRY = {
    # ========== 分子性质评估 ==========
    "ADMET Predictor": {
        "provider_name": "ADMET Predictor",
        "description": "预测小分子的吸收、分布、代谢、排泄和毒性（ADMET）性质",
        "category": "分子性质评估",
        "interfaces": {
            "SMILES输入": {
                "tool_name": "smiles_admet_post",
                "description": "输入 SMILES 字符串预测 ADMET 性质",
                "parameters": {
                    "smiles": {"type": "string", "required": True, "description": "分子 SMILES 字符串"},
                    "features": {"type": "array", "required": False, "description": "选择预测的特征项"}
                }
            },
            "文件输入": {
                "tool_name": "admet_post",
                "description": "上传文件批量预测 ADMET 性质",
                "parameters": {
                    "file": {"type": "file", "required": True, "description": "包含 SMILES 的文件"},
                    "features": {"type": "array", "required": False, "description": "选择预测的特征项"}
                },
                "file_params": ["file"]
            }
        }
    },
    
    "Molecular Descriptors": {
        "provider_name": "Molecular Descriptors",
        "description": "计算分子描述符",
        "category": "分子性质评估",
        "interfaces": {
            "默认接口": {
                "tool_name": "molecular_descriptors_post",
                "description": "计算分子描述符",
                "parameters": {
                    "smiles": {"type": "string", "required": True, "description": "分子 SMILES"}
                }
            }
        }
    },
    
    "Graph-pKa": {
        "provider_name": "Graph-pKa",
        "description": "计算小分子的 pKa 值",
        "category": "分子性质评估",
        "interfaces": {
            "默认接口": {
                "tool_name": "graph_pka_post",
                "description": "预测分子 pKa 值",
                "parameters": {
                    "smiles": {"type": "string", "required": True, "description": "分子 SMILES"}
                }
            }
        }
    },
    
    "Check Lipinski": {
        "provider_name": "Check Lipinski",
        "description": "判断小分子是否符合五项类药规则",
        "category": "分子性质评估",
        "interfaces": {
            "默认接口": {
                "tool_name": "check_lipinski_post",
                "description": "检查 Lipinski 规则",
                "parameters": {
                    "smiles": {"type": "string", "required": True, "description": "分子 SMILES"}
                }
            }
        }
    },
    
    "Check PAINS": {
        "provider_name": "Check PAINS",
        "description": "判断小分子是否为泛测定干扰化合物",
        "category": "分子性质评估",
        "interfaces": {
            "默认接口": {
                "tool_name": "check_pains_post",
                "description": "检查 PAINS 过滤器",
                "parameters": {
                    "smiles": {"type": "string", "required": True, "description": "分子 SMILES"}
                }
            }
        }
    },
    
    "SAScore": {
        "provider_name": "SAScore",
        "description": "计算分子的合成可及性评分",
        "category": "分子性质评估",
        "interfaces": {
            "默认接口": {
                "tool_name": "sascore_post",
                "description": "计算合成可及性",
                "parameters": {
                    "smiles": {"type": "string", "required": True, "description": "分子 SMILES"}
                }
            }
        }
    },
    
    "Structural Alert Filters": {
        "provider_name": "Structural Alert Filters",
        "description": "识别分子中的毒性和反应性亚结构",
        "category": "分子性质评估",
        "interfaces": {
            "默认接口": {
                "tool_name": "structural_alert_filters_post",
                "description": "结构警告过滤",
                "parameters": {
                    "smiles": {"type": "string", "required": True, "description": "分子 SMILES"}
                }
            }
        }
    },
    
    # ========== 数据库检索 ==========
    "Get Mol From Patent": {
        "provider_name": "Get Mol From Patent",
        "description": "通过专利号查询分子结构",
        "category": "数据库检索",
        "interfaces": {
            "默认接口": {
                "tool_name": "query_patentid_to_file_query_patentid_to_file_get",
                "description": "通过专利号获取分子结构",
                "parameters": {
                    "patent_id": {"type": "string", "required": True, "description": "专利号，如 CN112345678"}
                }
            }
        }
    },
    
    "PDB By Code": {
        "provider_name": "PDB By Code",
        "description": "通过 PDB 代码下载结构文件",
        "category": "数据库检索",
        "interfaces": {
            "默认接口": {
                "tool_name": "pdb_by_code_post",
                "description": "下载 PDB 文件",
                "parameters": {
                    "pdb_code": {
                        "type": "string",
                        "required": True,
                        "description": "PDB 代码，如 1ABC",
                    }
                }
            }
        }
    },
    
    "Clinical Trials": {
        "provider_name": "Clinical Trials",
        "description": "查询临床试验信息",
        "category": "数据库检索",
        "interfaces": {
            "默认接口": {
                "tool_name": "clinical_trials_post",
                "description": "查询临床试验",
                "parameters": {
                    "drug_name": {
                        "type": "string",
                        "required": False,
                        "description": "药物名称",
                    },
                    "nct_id": {
                        "type": "string",
                        "required": False,
                        "description": "NCT ID",
                    },
                }
            }
        }
    },
    
    # ========== 蛋白-配体对接 ==========
    "DiffDock": {
        "provider_name": "DiffDock",
        "description": "基于扩散模型的分子对接",
        "category": "蛋白-配体对接",
        "interfaces": {
            "默认接口": {
                "tool_name": "diffdock_post",
                "description": "分子对接",
                "parameters": {
                    "protein": {
                        "type": "file",
                        "required": True,
                        "description": "蛋白质 PDB 文件",
                    },
                    "ligand": {
                        "type": "file",
                        "required": True,
                        "description": "配体 SDF 文件",
                    },
                },
                "file_params": ["protein", "ligand"]
            }
        }
    },
    
    # ========== 格式转换 ==========
    "SMILES 2 Image": {
        "provider_name": "SMILES 2 Image",
        "description": "将 SMILES 转换为化学结构图像",
        "category": "格式转换",
        "interfaces": {
            "默认接口": {
                "tool_name": "smiles_2_image_post",
                "description": "SMILES 转图像",
                "parameters": {
                    "smiles": {
                        "type": "string",
                        "required": True,
                        "description": "SMILES 字符串",
                    }
                }
            }
        }
    },
    
    "SDF 2 SMILES": {
        "provider_name": "SDF 2 SMILES",
        "description": "将 SDF 转换为 SMILES",
        "category": "格式转换",
        "interfaces": {
            "默认接口": {
                "tool_name": "sdf_2_smiles_post",
                "description": "SDF 转 SMILES",
                "parameters": {
                    "file": {
                        "type": "file",
                        "required": True,
                        "description": "SDF 文件",
                    }
                },
                "file_params": ["file"]
            }
        }
    },
}


# 关键词到工具的映射
KEYWORD_TOOL_MAP = {
    # ADMET
    "admet": "ADMET Predictor",
    "吸收": "ADMET Predictor",
    "分布": "ADMET Predictor",
    "代谢": "ADMET Predictor",
    "排泄": "ADMET Predictor",
    "毒性": "ADMET Predictor",
    "药代动力学": "ADMET Predictor",
    
    # 分子性质
    "描述符": "Molecular Descriptors",
    "pka": "Graph-pKa",
    "pKa": "Graph-pKa",
    "lipinski": "Check Lipinski",
    "类药性": "Check Lipinski",
    "pains": "Check PAINS",
    "合成": "SAScore",
    # 数据库
    "专利": "Get Mol From Patent",
    "patent": "Get Mol From Patent",
    "pdb": "PDB By Code",
    "临床试验": "Clinical Trials",
    # 对接
    "对接": "DiffDock",
    "docking": "DiffDock",
    # 格式转换
    "smiles转图像": "SMILES 2 Image",
    "sdf转smiles": "SDF 2 SMILES",
}


def find_tool(query: str) -> dict:
    """根据用户查询自动搜索合适的工具"""
    if not query:
        return None
    
    query_lower = query.lower()
    
    # 1. 精确匹配工具名称
    for tool_name in TOOLS_REGISTRY:
        if tool_name.lower() in query_lower:
            return get_tool_info(tool_name)
    
    # 2. 关键词匹配
    for keyword, tool_name in KEYWORD_TOOL_MAP.items():
        if keyword.lower() in query_lower:
            return get_tool_info(tool_name)
    
    return None


def get_tool_info(tool_name: str) -> dict:
    """获取工具详细信息。

    支持两种查询方式：
    - 友好名称（TOOLS_REGISTRY 的键）
    - 内部接口名称（interface 中的 "tool_name" 值）
    返回与原来相似的字典结构，找不到时返回 None。
    """
    # 直接按友好名称查找
    if tool_name in TOOLS_REGISTRY:
        tool = TOOLS_REGISTRY[tool_name]
        result = {
            "name": tool_name,
            "provider_name": tool.get("provider_name"),
            "description": tool.get("description"),
            "category": tool.get("category"),
            "interfaces": tool.get("interfaces", {})
        }

        # 添加默认接口信息
        if result["interfaces"]:
            first_interface = list(result["interfaces"].values())[0]
            result["tool_name"] = first_interface.get("tool_name")
            result["parameters"] = first_interface.get("parameters", {})
            result["file_params"] = first_interface.get("file_params", [])

        return result

    # 支持按内部接口名称查找（如 smiles_admet_post）
    for friendly_name, tool in TOOLS_REGISTRY.items():
        interfaces = tool.get("interfaces", {})
        for iface in interfaces.values():
            if iface.get("tool_name") == tool_name:
                result = {
                    "name": friendly_name,
                    "provider_name": tool.get("provider_name"),
                    "description": tool.get("description"),
                    "category": tool.get("category"),
                    "interfaces": tool.get("interfaces", {})
                }
                result["tool_name"] = tool_name
                result["parameters"] = iface.get("parameters", {})
                result["file_params"] = iface.get("file_params", [])
                return result

    return None


def list_tools(category: str = None) -> list:
    """列出所有工具"""
    if category:
        return [
            {"name": name, "category": info.get("category")}
            for name, info in TOOLS_REGISTRY.items()
            if info.get("category") and category.lower() in info.get("category", "").lower()
        ]
    return [
        {"name": name, "category": info.get("category"), "description": info.get("description")}
        for name, info in TOOLS_REGISTRY.items()
    ]


if __name__ == "__main__":
    print(f"已注册工具数: {len(TOOLS_REGISTRY)}")
    for name in TOOLS_REGISTRY:
        info = get_tool_info(name)
        print(f"\n{name}:")
        print(f"  tool_name: {info.get('tool_name', 'N/A')}")
        print(f"  parameters: {list(info.get('parameters', {}).keys())}")
