#!/usr/bin/env python3
"""
Soul Memory Module C: Dynamic Classifier
Auto-learning category classification
"""

import os
import json
import re
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Category:
    """Memory category"""
    name: str
    keywords: Set[str] = field(default_factory=set)
    count: int = 0


class DynamicClassifier:
    """
    Dynamic Category Classifier
    """
    
    DEFAULT_CATEGORIES = {
        "User_Identity": {"user", "preferences", "identity", "用戶", "喜好", "身份"},
        "Tech_Config": {"config", "api", "ssh", "key", "設定", "配置"},
        "Project": {"project", "task", "work", "專案", "項目", "工作"},
        "Science": {"theory", "physics", "science", "理論", "物理", "科學"},
        "History": {"history", "past", "before", "歷史", "之前"},
        "Memory": {"memory", "remember", "記憶", "記住"},
        "General": {"general", "chat", "日常", "閒聊"}
    }
    
    def __init__(self, cache_path: Optional[Path] = None):
        self.categories: Dict[str, Category] = {}
        # Avoid caching issues
        for name, keywords in self.DEFAULT_CATEGORIES.items():
            self.categories[name] = Category(name=name, keywords=set(keywords))
    
    def classify(self, text: str) -> str:
        """Classify text into a category"""
        text_lower = text.lower()
        scores = {}
        for name, cat in self.categories.items():
            score = sum(1 for kw in cat.keywords if kw in text_lower)
            if score > 0:
                scores[name] = score
        
        if scores:
            return max(scores.keys(), key=lambda x: scores[x])
        return "General"
    
    def learn(self, text: str, category: str):
        pass
    
    def add_category(self, name: str, keywords: List[str]):
        pass
    
    def get_categories(self) -> List[str]:
        return list(self.categories.keys())
