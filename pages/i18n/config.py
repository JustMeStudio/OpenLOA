# -*- coding: utf-8 -*-
"""
I18n Configuration Manager
管理语言配置的读写
"""

import os
import yaml
from typing import Optional

CONFIG_FILE = './configs/settings.yaml'
DEFAULT_LANGUAGE = 'en'


class I18nConfig:
    """国际化配置管理器"""
    
    def __init__(self):
        self.current_language = self._load_language()
    
    def _ensure_config_file(self):
        """确保配置文件存在"""
        if not os.path.exists(CONFIG_FILE):
            os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
            self._save_language(DEFAULT_LANGUAGE)
    
    def _load_language(self) -> str:
        """从settings.yaml加载语言配置"""
        try:
            if not os.path.exists(CONFIG_FILE):
                return DEFAULT_LANGUAGE
            
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                if config and 'language' in config:
                    return config['language']
                return DEFAULT_LANGUAGE
        except Exception as e:
            print(f"Error loading language config: {e}")
            return DEFAULT_LANGUAGE
    
    def _save_language(self, language: str):
        """保存语言配置到settings.yaml"""
        try:
            self._ensure_config_file()
            
            # 读取现有配置
            config = {}
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if content.strip():
                        config = yaml.safe_load(content) or {}
            
            # 更新语言配置
            config['language'] = language
            
            # 写入配置
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
            
            self.current_language = language
        except Exception as e:
            print(f"Error saving language config: {e}")
    
    def set_language(self, language: str):
        """设置语言"""
        if language in ['en', 'zh']:
            self._save_language(language)
            self.current_language = language
    
    def get_language(self) -> str:
        """获取当前语言"""
        return self.current_language


# 全局配置实例
_i18n_config_instance: Optional[I18nConfig] = None


def get_i18n_config() -> I18nConfig:
    """获取全局的I18n配置实例"""
    global _i18n_config_instance
    if _i18n_config_instance is None:
        _i18n_config_instance = I18nConfig()
    return _i18n_config_instance


def get_current_language() -> str:
    """获取当前语言"""
    return get_i18n_config().get_language()


def set_language(language: str):
    """设置语言"""
    get_i18n_config().set_language(language)
