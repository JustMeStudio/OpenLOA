# OpenLOA I18n (国际化) 实现指南

## 概述

本项目已经成功实现了国际化(I18n)支持，支持**英语(English)**和**中文(简体中文)**两种语言。

## 功能特性

✅ **语言选择下拉框** - 在WelcomePage顶部添加了语言选择器  
✅ **自动保存配置** - 用户选择的语言会自动保存到`./configs/settings.yaml`  
✅ **启动时加载** - 应用启动时会自动从settings.yaml加载上次保存的语言设置  
✅ **默认英语** - 第一次启动时默认使用English  
✅ **动态更新UI** - 切换语言时，所有UI文本会实时更新  

## 目录结构

```
pages/
├── i18n/                    # I18n模块（新增）
│   ├── __init__.py         # 模块初始化
│   ├── translations.py     # 翻译文本定义
│   └── config.py           # 配置管理器
├── WelcomePage.py          # 修改：添加语言选择器
├── ChooseAgentPage.py      # 修改：支持I18n
└── MainWindow.py           # 修改：初始化I18n配置

configs/
└── settings.yaml           # 修改：现在存储语言配置
```

## 文件详解

### 1. `pages/i18n/translations.py`
包含所有支持的语言翻译文本：
- 支持英文(en)和中文(zh)
- 可简单添加更多语言
- 包含WelcomePage和ChooseAgentPage的所有文本

```python
TRANSLATIONS = {
    'en': { /* 英文翻译 */ },
    'zh': { /* 中文翻译 */ }
}
```

### 2. `pages/i18n/config.py`
负责配置的读写和全局状态管理：
- `I18nConfig` 类：管理语言配置
- `get_i18n_config()` 函数：获取全局配置实例
- `get_current_language()` 函数：获取当前语言
- `set_language(language)` 函数：设置语言

**工作流程：**
1. 首次启动：从settings.yaml读取（如果不存在则默认'en'）
2. 用户改变语言：调用`set_language()`
3. `set_language()`更新settings.yaml并更新内存状态

### 3. `configs/settings.yaml`
存储应用配置，现在包含：
```yaml
language: en  # 或 zh
```

## 使用方法

### 用户视角

1. **启动应用**
   ```bash
   python app_GUI.py
   ```

2. **选择语言**
   - 在WelcomePage顶部右侧可看到语言选择下拉框
   - 选择"English"或"中文"
   - 所有UI文本会立即更新

3. **下次启动**
   - 应用会自动加载上次选择的语言设置

### 开发者视角

#### 在代码中使用翻译

```python
from pages.i18n import get_current_language, get_text

# 获取当前语言
language = get_current_language()

# 获取翻译文本
button_text = get_text('start_btn', language)
```

#### 在UI中使用翻译

```python
from pages.i18n import get_text, set_language

# 设置标签文本
label = QLabel(get_text('title', current_language))

# 监听语言改变事件
def on_language_changed(new_language):
    label.setText(get_text('title', new_language))
    set_language(new_language)
```

## 添加新翻译

### 步骤1：在`pages/i18n/translations.py`中添加新键值对

```python
TRANSLATIONS = {
    'en': {
        # ... 已有的翻译
        'new_key': 'New Text in English',
    },
    'zh': {
        # ... 已有的翻译
        'new_key': '新文本的中文翻译',
    }
}
```

### 步骤2：在UI代码中使用

```python
text = get_text('new_key', current_language)
```

## 支持的语言及代码

| 语言 | 代码 | 备注 |
|------|------|------|
| English | `en` | 默认语言 |
| 中文(简体) | `zh` | 简体中文 |

## 技术细节

### 全局配置单例模式
```python
_i18n_config_instance = None

def get_i18n_config():
    global _i18n_config_instance
    if _i18n_config_instance is None:
        _i18n_config_instance = I18nConfig()
    return _i18n_config_instance
```

这确保整个应用只有一个I18n配置实例，避免状态不一致。

### 配置文件操作
- 使用PyYAML库读写YAML格式的配置文件
- 自动处理文件不存在的情况
- 线程安全的配置更新

### MainWindow集成
在MainWindow.__init__中显式初始化I18n配置：
```python
get_i18n_config()  # 确保在应用启动时加载配置
```

## 修改的文件列表

| 文件 | 修改内容 |
|------|--------|
| `pages/WelcomePage.py` | 添加语言选择下拉框，所有UI文本使用i18n |
| `pages/ChooseAgentPage.py` | 所有UI文本使用i18n |
| `pages/MainWindow.py` | 导入并初始化I18n配置 |
| `configs/settings.yaml` | 新增语言配置字段 |
| `pages/i18n/` | 新增I18n模块（3个文件） |

## 测试验证

### 验证清单
- [x] 应用启动时正确加载语言配置
- [x] WelcomePage显示语言选择下拉框
- [x] 选择不同语言后UI立即更新
- [x] 语言配置保存到settings.yaml
- [x] 重启应用后使用上次保存的语言
- [x] ChooseAgentPage使用i18n翻译

## 常见问题

### Q: 如何重置为默认语言？
A: 删除`configs/settings.yaml`文件，下次应用启动将使用默认的English。

### Q: 如何添加新语言？
A: 
1. 在`pages/i18n/translations.py`中添加新的语言字典
2. 在`pages/WelcomePage.py`的combo box中添加新选项
3. 更新任何硬编码的语言列表

### Q: 配置文件位置是什么？
A: `./configs/settings.yaml`

### Q: 支持多个配置吗？
A: 目前只存储语言配置，但可以轻松扩展来存储其他配置。

## 扩展建议

### 未来可能的增强

1. **更多语言支持** - 可添加日语、韩语、西班牙语等
2. **配置UI** - 创建专门的设置页面来管理语言和其他选项
3. **自动语言检测** - 根据系统语言自动选择界面语言
4. **翻译文件外部化** - 将翻译存储在JSON或专门的翻译文件中
5. **RTL语言支持** - 支持阿拉伯语等从右到左的语言

## 依赖

- `PySide6` - GUI框架
- `PyYAML` - YAML配置文件处理
- `Python 3.7+` - 基础版本要求

## 许可证

遵循项目原有许可证。
