#!/usr/bin/env python3
"""
Soul Memory Tag Index v3.3
核心改進：多標籤索引系統 + 標籤搜索
特性：使用通用術語，無需硬編碼用戶特定字眼
"""

import json
from pathlib import Path
from typing import Dict, List, Set, Tuple
from datetime import datetime


# ============================================
# 標籤索引類
# ============================================

class TagIndex:
    """
    標籤索引系統
    
    功能：
    - 為每個記憶維護多個標籤
    - 支持標籤組合搜索
    - 按權重排序結果
    """
    
    def __init__(self, index_file: str = None):
        """
        初始化標籤索引
        
        Args:
            index_file (str): 索引文件路徑（可選，持久化）
        """
        self.index_file = Path(index_file) if index_file else None
        
        # 標籤索引: {tag: [{file, line, weight, priority}, ...]}
        self.index: Dict[str, List[Dict]] = {}
        
        # 反向索引: {file: [tag, ...]}
        self.reverse_index: Dict[str, List[str]] = {}
        
        # 從文件加載
        if self.index_file and self.index_file.exists():
            self._load_from_file()
    
    def add(self, tags: List[Tuple[str, int]], file: str, line: int, priority: str = 'N'):
        """
        添加標籤索引
        
        Args:
            tags (list): [(tag, weight), ...]
            file (str): 文件路徑
            line (int): 行號
            priority (str): 優先級 [C/I/N]
        """
        file_name = Path(file).name
        
        for tag, weight in tags:
            # 優先級加權
            priority_weight = {
                'C': 1.5,
                'I': 1.2,
                'N': 1.0
            }.get(priority, 1.0)
            
            # 添加標籤索引
            if tag not in self.index:
                self.index[tag] = []
            
            entry = {
                'file': file_name,
                'line': line,
                'weight': weight,
                'priority': priority,
                'score': weight * priority_weight
            }
            
            self.index[tag].append(entry)
        
        # 添加反向索引
        if file_name not in self.reverse_index:
            self.reverse_index[file_name] = []
        for tag, _ in tags:
            if tag not in self.reverse_index[file_name]:
                self.reverse_index[file_name].append(tag)
    
    def search(self, query_tags: List[str], operator: str = 'AND') -> List[Dict]:
        """
        標籤搜索
        
        Args:
            query_tags (list): 標籤列表
            operator (str): 'AND' 或 'OR'（標籤組合邏輯）
        
        Returns:
            list: [{file, line, score, ...}, ...] 按分數排序
        """
        if not query_tags:
            return []
        
        # 收集結果
        results = {}
        
        for tag in query_tags:
            if tag not in self.index:
                continue
            
            for entry in self.index[tag]:
                key = (entry['file'], entry['line'])
                
                if operator == 'OR':
                    # OR: 任何標籤匹配都加入
                    if key not in results:
                        results[key] = entry.copy()
                        results[key]['matched_tags'] = [tag]
                    else:
                        results[key]['score'] += entry['score']
                        results[key]['matched_tags'].append(tag)
                else:  # AND
                    # AND: 必須包含所有查詢標籤
                    if key not in results:
                        results[key] = entry.copy()
                        results[key]['matched_tags'] = [tag]
                    else:
                        results[key]['matched_tags'].append(tag)
        
        # AND: 過濾不匹配所有標籤的結果
        if operator == 'AND':
            results = {
                k: v for k, v in results.items()
                if set(query_tags).issubset(set(v.get('matched_tags', [])))
            }
        
        # 按分數排序
        sorted_results = sorted(
            results.values(),
            key=lambda x: x['score'],
            reverse=True
        )
        
        return sorted_results
    
    def get_stats(self) -> Dict:
        """
        統計信息
        
        Returns:
            dict: 統計數據
        """
        total_tags = len(self.index)
        total_entries = sum(len(entries) for entries in self.index.values())
        total_files = len(self.reverse_index)
        
        # 計算最常見標籤
        tag_counts = {tag: len(entries) for tag, entries in self.index.items()}
        top_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            'total_tags': total_tags,
            'total_entries': total_entries,
            'total_files': total_files,
            'top_tags': top_tags
        }
    
    def _save_to_file(self):
        """保存到文件"""
        data = {
            'index': self.index,
            'reverse_index': self.reverse_index,
            'updated_at': datetime.now().isoformat()
        }
        
        if self.index_file:
            self.index_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _load_from_file(self):
        """從文件加載"""
        try:
            with open(self.index_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.index = data.get('index', {})
            self.reverse_index = data.get('reverse_index', {})
        except Exception as e:
            print(f"⚠️ 加載標籤索引失敗: {e}")
    
    def sync(self):
        """同步到文件"""
        if self.index_file:
            self._save_to_file()


# ============================================
# 集成到 Heartbeat
# ============================================

def update_tag_index(content: str, priority: str, tags: List[Tuple[str, int]],
                     daily_file: str, tag_index: TagIndex = None):
    """
    更新標籤索引（集成函數）
    
    Args:
        content (str): 內容
        priority (str): 優先級 [C/I/N]
        tags (list): [(tag, weight), ...]
        daily_file (str): daily file 路徑
        tag_index (TagIndex): 標籤索引實例
    """
    if not tag_index:
        return
    
    # 計算行號（簡單估算）
    line_number = content.count('\n') + 1
    
    # 添加到索引
    tag_index.add(tags, daily_file, line_number, priority)
    
    # 同步到文件
    tag_index.sync()


# ============================================
# 測試代碼
# ============================================

if __name__ == '__main__':
    print("=" * 60)
    print("Soul Memory Tag Index v3.3 - 測試")
    print("=" * 60)
    
    # 創建標籤索引
    import tempfile
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
    temp_file.close()
    
    tag_idx = TagIndex(index_file=temp_file.name)
    
    # 添加測試數據
    test_data = [
        ([
            ('framework', 10),
            ('deployment', 7),
            ('website', 9)
        ], '2026-02-26.md', 100, 'C'),
        ([
            ('api_key', 10),
            ('config', 9),
            ('security', 8)
        ], '2026-02-26.md', 200, 'C'),
        ([
            ('repository', 7),
            ('git', 8),
            ('commit', 9)
        ], '2026-02-26.md', 300, 'I'),
    ]
    
    for tags, file, line, priority in test_data:
        tag_idx.add(tags, file, line, priority)
        print(f"\n添加記憶: {file}:{line} [{priority}]")
        print(f"  標籤: {[t[0] for t in tags]}")
    
    tag_idx.sync()
    
    # 標籤搜索測試
    print("\n" + "=" * 60)
    print("標籤搜索測試")
    print("=" * 60)
    
    # AND 搜索
    results = tag_idx.search(['framework', 'website'], operator='AND')
    print(f"\n搜索: ['framework', 'website'] (AND)")
    print(f"結果: {len(results)} 條")
    for r in results:
        print(f"  - {r['file']}:{r['line']} [{r['priority']}] 分數={r['score']:.1f}")
    
    # OR 搜索
    results = tag_idx.search(['api_key', 'repository'], operator='OR')
    print(f"\n搜索: ['api_key', 'repository'] (OR)")
    print(f"結果: {len(results)} 條")
    for r in results:
        print(f"  - {r['file']}:{r['line']} [{r['priority']}] 分數={r['score']:.1f}")
    
    # 統計信息
    print("\n" + "=" * 60)
    print("統計信息")
    print("=" * 60)
    stats = tag_idx.get_stats()
    for key, value in stats.items():
        if key != 'top_tags':
            print(f"  {key}: {value}")
    
    print(f"\n最常見標籤:")
    for tag, count in stats['top_tags']:
        print(f"  {tag}: {count} 次")
    
    # 清理臨時文件
    import os
    os.unlink(temp_file.name)
