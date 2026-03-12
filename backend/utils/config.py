import yaml
from pathlib import Path

# 1. 动态获取路径
# __file__ 是当前 Sara.py 的路径
# .parent 是 backend 目录
# .parent.parent 是 OpenLOA 根目录
BASE_DIR = Path(__file__).resolve().parent.parent.parent
CONFIG_PATH = BASE_DIR / "configs" / "models.yaml"

def load_model_config(config_name):
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            # 加载整个 YAML 文件
            all_configs = yaml.safe_load(f)
            
            # 读取指定的 Sara_agent_model_config 部分
            return all_configs.get(config_name, {})
    except FileNotFoundError:
        print(f"❌ 错误：找不到配置文件 {CONFIG_PATH}")
        return {}
    except Exception as e:
        print(f"❌ 读取配置出错: {e}")
        return {}