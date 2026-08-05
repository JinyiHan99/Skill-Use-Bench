#!/usr/bin/env python3
"""
Soul Memory Semantic Deduplication v3.3
核心改進：語意相似度去重 + MD5 完全匹配雙層機制
特性：使用通用術語，無需硬編碼用戶特定字眼
"""

import difflib
import hashlib
from typing import Dict, List, Tuple
from pathlib import Path


# ============================================
# 語意去重類
# ============================================

class SemanticDedup:
    """
    語意相似度去重（雙層機制）
    
    第一層：MD5 完全匹配（快速）
    第二層：語意相似度檢查（精確）
    """
    
    def __init__(self, threshold=0.85, category_based=True, min_length_for_dedup=100):  # v3.5.11: 降低到 0.85
        """
        初始化去重器
        
        Args:
            threshold (float): 語意相似度閾值 (0.0-1.0) - v3.5.11: 0.92→0.85
            category_based (bool): 是否基於分類去重（不同類別不檢查相似度）
            min_length_for_dedup (int): 最小去重長度 - v3.5.11: <100 字跳過去重
        """
        self.threshold = threshold
        self.category_based = category_based
        self.min_length_for_dedup = min_length_for_dedup
        
        # 已保存的內容（按分類組織）
        self.saved_contents: Dict[str, List[str]] = {}
        
        # MD5 哈希集合（第一層去重）
        self.saved_hashes: set = set()
    
    def get_content_hash(self, content: str) -> str:
        """
        計算內容 MD5 哈希
        
        Args:
            content (str): 內容
        
        Returns:
            str: MD5 哈希（16 進制）
        """
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def is_duplicate_by_hash(self, content: str) -> bool:
        """
        第一層：MD5 完全匹配檢查
        
        Args:
            content (str): 內容
        
        Returns:
            bool: 是否重複
        """
        content_hash = self.get_content_hash(content)
        return content_hash in self.saved_hashes
    
    def is_duplicate_by_similarity(self, content: str, category: str = 'General') -> bool:
        """
        第二層：語意相似度檢查
        
        Args:
            content (str): 內容
            category (str): 分類標籤
        
        Returns:
            bool: 是否語意相似
        """
        if not self.category_based:
            category = 'General'  # 不使用分類，全部檢查
        
        if category not in self.saved_contents:
            return False
        
        for saved in self.saved_contents[category]:
            # 使用 difflib 計算序列相似度
            similarity = difflib.SequenceMatcher(None, content, saved).ratio()
            
            if similarity > self.threshold:
                return True
        
        return False
    
    def is_duplicate(self, content: str, category: str = 'General') -> Tuple[bool, str]:
        """
        綜合檢查是否重複（雙層機制）
        
        Args:
            content (str): 內容
            category (str): 分類標籤
        
        Returns:
            (bool, str): (是否重複, 去重類型)
                          - 'exact': 完全匹配（MD5）
                          - 'similar': 語意相似
                          - 'unique': 唯一
        """
        # 第一層：MD5 完全匹配
        if self.is_duplicate_by_hash(content):
            return True, 'exact'
        
        # 第二層：語意相似度
        if self.is_duplicate_by_similarity(content, category):
            return True, 'similar'
        
        return False, 'unique'
    
    def save(self, content: str, category: str = 'General'):
        """
        保存內容
        
        Args:
            content (str): 內容
            category (str): 分類標籤
        """
        # 保存哈希（第一層）
        content_hash = self.get_content_hash(content)
        self.saved_hashes.add(content_hash)
        
        # 保存內容（第二層）
        if self.category_based:
            if category not in self.saved_contents:
                self.saved_contents[category] = []
            self.saved_contents[category].append(content)
        else:
            if 'General' not in self.saved_contents:
                self.saved_contents['General'] = []
            self.saved_contents['General'].append(content)
    
    def get_stats(self) -> Dict:
        """
        統計信息
        
        Returns:
            dict: 統計數據
        """
        total_contents = sum(len(contents) for contents in self.saved_contents.values())
        total_hashes = len(self.saved_hashes)
        categories = len(self.saved_contents)
        
        return {
            'total_contents': total_contents,
            'total_hashes': total_hashes,
            'categories': categories,
            'category_breakdown': {
                cat: len(contents) for cat, contents in self.saved_contents.items()
            }
        }


# ============================================
# 持久化支持
# ============================================

class PersistentDedup(SemanticDedup):
    """持久化去重器（將狀態保存到文件）"""
    
    def __init__(self, storage_path: str, threshold=0.92, category_based=True):  # v3.5.4
        """
        初始化持續化去重器
        
        Args:
            storage_path (str): 存儲路徑（JSON 文件）
            threshold (float): 語意相似度閾值
            category_based (bool): 是否基於分類
        """
        super().__init__(threshold, category_based)
        self.storage_path = Path(storage_path)
        
        # 從文件加載
        self._load_from_file()
    
    def _save_to_file(self):
        """保存到文件"""
        import json
        
        data = {
            'threshold': self.threshold,
            'category_based': self.category_based,
            'saved_hashes': list(self.saved_hashes),
            'saved_contents': self.saved_contents
        }
        
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.storage_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _load_from_file(self):
        """從文件加載"""
        import json
        
        if not self.storage_path.exists():
            return
        
        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.threshold = data.get('threshold', 0.92)
            self.category_based = data.get('category_based', True)
            self.saved_hashes = set(data.get('saved_hashes', []))
            self.saved_contents = data.get('saved_contents', {})
        except Exception as e:
            print(f"⚠️ 加載去重記錄失敗: {e}")
    
    def save(self, content: str, category: str = 'General'):
        """保存內容並持久化"""
        super().save(content, category)
        self._save_to_file()


# ============================================
# 測試代碼
# ============================================

if __name__ == '__main__':
    print("=" * 60)
    print("Soul Memory Semantic Dedup v3.3 - 測試")
    print("=" * 60)
    
    # 創建去重器
    dedup = SemanticDedup(threshold=0.85, category_based=True)
    
    # 測試用例
    test_contents = [
        ("部署 framework 到 web_server", "Deployment"),
        ("部署 framework 到 web_server", "Deployment"),  # 完全相同
        ("部署 framework 系統", "Deployment"),            # 語意相似
        ("api_key 配置已設置", "System"),                  # 不同分類
        ("api_key 設定完成", "System"),                   # 語意相似（同分類）
        ("api_key 已經設定完畢", "System"),                # 語意相似（同分類）
    ]
    
    for i, (content, category) in enumerate(test_contents, 1):
        is_dup, dedup_type = dedup.is_duplicate(content, category)
        status = {
            'exact': '📦 完全相同',
            'similar': '🔄 語意相似',
            'unique': '✨ 唯一'
        }[dedup_type]
        
        print(f"\n測試 {i}: [{category}]")
        print(f"  內容: {content}")
        print(f"  狀態: {status}")
        
        if not is_dup:
            dedup.save(content, category)
            print(f"  → 已保存")
        else:
            print(f"  → 已跳過")
    
    # 統計信息
    print("\n" + "=" * 60)
    print("統計信息")
    print("=" * 60)
    stats = dedup.get_stats()
    for key, value in stats.items():
        if key != 'category_breakdown':
            print(f"  {key}: {value}")
    
    print(f"\n分類詳情:")
    for cat, count in stats['category_breakdown'].items():
        print(f"  {cat}: {count} 條")
