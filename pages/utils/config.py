import yaml
import os

def load_agent_profiles(file_path='./configs/profiles.yaml'):
    """
    从指定路径读取 YAML 格式的 Agent 配置并返回字典。
    """
    if not os.path.exists(file_path):
        print(f"错误: 找不到配置文件 {file_path}")
        return {}

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            # 使用 safe_load 避免执行 YAML 中的恶意代码，这是最佳实践
            profiles = yaml.safe_load(f)
            return profiles if profiles else {}
    except yaml.YAMLError as e:
        print(f"解析 YAML 时出错: {e}")
        return {}
    except Exception as e:
        print(f"读取文件时发生未知错误: {e}")
        return {}

def load_user_settings(file_path='./configs/settings.yaml'):
    """
    从指定路径读取 YAML 格式的用户设置并返回字典。
    """
    if not os.path.exists(file_path):
        print(f"错误: 找不到配置文件 {file_path}")
        return {}

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            # 使用 safe_load 避免执行 YAML 中的恶意代码，这是最佳实践
            profiles = yaml.safe_load(f)
            if profiles["language"] not in ["en", "zh"]:
                print(f"警告: 无效的语言设置 {profiles['language']}，默认使用英文")
                profiles["language"] = "en"
            if not profiles["avatar"]:
                print("警告: 用户头像设置缺失，使用默认头像")
                profiles["avatar"] = "./assets/avatar/default.jpg"
            return profiles if profiles else {}
    except yaml.YAMLError as e:
        print(f"解析 YAML 时出错: {e}")
        return {}
    except Exception as e:
        print(f"读取文件时发生未知错误: {e}")
        return {}

# 测试调用
if __name__ == "__main__":
    data = load_agent_profiles()
    print(data)