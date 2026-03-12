# -*- coding: utf-8 -*-
"""
I18n Translations Module
支持英语和中文的多语言翻译
"""

TRANSLATIONS = {
    'en': {
        # WelcomePage
        'title': 'OpenLOA',
        'subtitle': 'Alliance of Agents · Define Your Own Truly Efficient Agents',
        'start_btn': 'Launch Now',
        'project_info': 'PROJECT: OpenLOA v1.0.0-OpenSource',
        'developer_info': 'Developed by JustMeStudio @ JustMeStudio AI Studio',
        'language': 'Language',
        
        # ChooseAgentPage
        'welcome_message': 'Welcome to the Intelligent Canyon, dear Summoner',
        'system_status': 'System Status: Connected (OpenSource Mode)',
        'star_button': '⭐ Star OpenLOA on GitHub',
        'select_agent': 'Please select an agent',
    },
    'zh': {
        # WelcomePage
        'title': 'OpenLOA',
        'subtitle': '智能体联盟 · 真正高效的智能体由你定义',
        'start_btn': '现在启动',
        'project_info': 'PROJECT: OpenLOA v1.0.0-OpenSource',
        'developer_info': 'Developed by JustMeStudio @ 就我智己AI工作室',
        'language': '语言',
        
        # ChooseAgentPage
        'welcome_message': '欢迎来到智能峡谷，亲爱的召唤师',
        'system_status': '系统状态: 接入中 (OpenSource Mode)',
        'star_button': '⭐ 为 OpenLOA 点亮 Star',
        'select_agent': '请选择一个智能体',
    }
}


def get_text(key, language='en'):
    """
    获取指定语言的翻译文本
    
    Args:
        key: 翻译键
        language: 语言代码 ('en' 或 'zh')
        
    Returns:
        翻译后的文本，如果键不存在则返回键本身
    """
    if language not in TRANSLATIONS:
        language = 'en'
    
    return TRANSLATIONS[language].get(key, key)
