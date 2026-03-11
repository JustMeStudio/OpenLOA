import os
import json
import time
from typing import List, Dict, Any

def qprint(*args, **kwargs):
    time.sleep(0.1)
    print(*args, **kwargs)
    time.sleep(0.1)


def update_metadata_file(metadata_file_path: str,
                         metadata_content: List[Dict[str, Any]],
                         unique_key: str = 'id') -> None:
    """
    如果文件不存在，则创建并写入 metadata_content；
    如果文件已存在，则读取、合并（基于 unique_key 去重）、写回。

    metadata_content 应是 List[Dict] 格式。
    unique_key 用于去重，如果不存在该键则按整个字典判断重复。
    """
    # 1. 读取已有内容
    if os.path.isfile(metadata_file_path):
        with open(metadata_file_path, 'r', encoding='utf-8') as f:
            try:
                existing = json.load(f)
                if not isinstance(existing, list):
                    existing = []
            except (json.JSONDecodeError, ValueError):
                existing = []
    else:
        existing = []

    # 2. 确保新内容是列表
    new_list = metadata_content if isinstance(metadata_content, list) else [metadata_content]

    # 3. 去重合并逻辑
    if unique_key:
        seen = {item[unique_key] for item in existing
                if isinstance(item, dict) and unique_key in item}
        merged = existing.copy()
        for item in new_list:
            if isinstance(item, dict) and unique_key in item:
                if item[unique_key] not in seen:
                    merged.append(item)
                    seen.add(item[unique_key])
            else:
                # 若不包含 unique_key 或不是 dict，可按需追加或忽略
                if item not in merged:
                    merged.append(item)
    else:
        # 不指定 unique_key 时按 dict 整体去重
        merged = existing.copy()
        for item in new_list:
            if item not in merged:
                merged.append(item)

    # 4. 写回文件（覆盖／创建）
    with open(metadata_file_path, 'w', encoding='utf-8') as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)
