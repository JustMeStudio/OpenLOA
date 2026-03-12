# -*- coding: utf-8 -*-
"""
I18n Module
国际化模块
"""

from .config import get_i18n_config, get_current_language, set_language
from .translations import get_text

__all__ = ['get_i18n_config', 'get_current_language', 'set_language', 'get_text']
