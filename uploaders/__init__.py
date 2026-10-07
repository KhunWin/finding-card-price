"""
Uploaders package for Boutir product upload automation
"""

from .selenium_uploader import SeleniumUploader
from .playwright_uploader import PlaywrightUploader

__all__ = ['SeleniumUploader', 'PlaywrightUploader']
