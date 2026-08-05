#!/usr/bin/env python3
"""
Soul Memory Module A: Priority Parser
智能記憶優先級解析器
"""

import re
from enum import Enum
from dataclasses import dataclass
from typing import Optional, Tuple

class Priority(Enum):
    """Memory priority levels"""
    CRITICAL = "C"   # Key: must remember
    IMPORTANT = "I"  # Important: needs attention
    NORMAL = "N"     # Normal: daily chat


@dataclass
class ParsedMemory:
    """Parsed memory item"""
    original: str        # Original text
    priority: Priority     # Priority level
    content: str         # Content (without tags)
    has_explicit_tag: bool # Has explicit tag


class PriorityParser:
    """
    Priority Parser
    """
    
    # Explicit tag pattern
    PRIORITY_PATTERN = re.compile(r'^\s*\[([CIN])\]\s*', re.IGNORECASE)
    
    # Keywords indicating CRITICAL priority
    CRITICAL_KEYWORDS = {
        'zh': ['記住', '關鍵', '核心', '重要', '必須', '配置', '決定', '記得'],
        'en': ['remember', 'critical', 'core', 'key', 'must', 'config', 'decision']
    }
    
    # Keywords indicating IMPORTANT priority
    IMPORTANT_KEYWORDS = {
        'zh': ['喜歡', '計厭', '項目', '進度', '約定', '觀點', '想法'],
        'en': ['like', 'dislike', 'project', 'progress', 'schedule', 'view', 'thought']
    }
    
    def __init__(self):
        pass
    
    def parse(self, text: str) -> ParsedMemory:
        """
        Parse memory text to extract priority
        """
        match = self.PRIORITY_PATTERN.match(text)
        if match:
            tag = match.group(1).upper()
            priority = Priority(tag)
            content = text[match.end():].strip()
            return ParsedMemory(
                original=text,
                priority=priority,
                content=content,
                has_explicit_tag=True
            )
        
        priority = self._detect_priority_semantic(text)
        return ParsedMemory(
            original=text,
            priority=priority,
            content=text,
            has_explicit_tag=False
        )
    
    def _detect_priority_semantic(self, text: str) -> Priority:
        """Detect priority using keyword analysis"""
        text_lower = text.lower()
        if any(kw in text_lower for kw in self.CRITICAL_KEYWORDS['zh']):
            return Priority.CRITICAL
        if any(kw in text_lower for kw in self.CRITICAL_KEYWORDS['en']):
            return Priority.CRITICAL
        if any(kw in text_lower for kw in self.IMPORTANT_KEYWORDS['zh']):
            return Priority.IMPORTANT
        if any(kw in text_lower for kw in self.IMPORTANT_KEYWORDS['en']):
            return Priority.IMPORTANT
        return Priority.NORMAL
