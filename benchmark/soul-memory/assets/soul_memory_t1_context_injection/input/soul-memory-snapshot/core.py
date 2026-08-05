import os
import sys
import json
import re
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).parent
sys.path.append(str(PROJECT_ROOT))

from modules.priority_parser import PriorityParser
from modules.vector_search import VectorSearch
from modules.dynamic_classifier import DynamicClassifier
from modules.semantic_dedup import PersistentDedup
from modules.version_control import VersionControl

class SoulMemorySystem:
    VERSION = "3.5.13"
    
    def __init__(self, workspace_path: Optional[str] = None):
        if workspace_path:
            self.workspace = Path(workspace_path)
        else:
            self.workspace = Path.home() / ".openclaw" / "workspace"
            
        self.memory_file = self.workspace / "MEMORY.md"
        self.daily_dir = self.workspace / "memory"
        self.daily_dir.mkdir(parents=True, exist_ok=True)
        
        self.priority_parser = PriorityParser()
        self.vector_search = VectorSearch()
        self.dynamic_classifier = DynamicClassifier()
        # v3.5.4: 提高 threshold 到 0.92（減少誤去重）
        self.dedup = PersistentDedup(str(self.workspace / "data" / "dedup.json"), threshold=0.92, category_based=True)
        self.version_control = VersionControl(str(self.workspace))
        
        self.indexed = False

    def initialize(self):
        """Initialize the memory system and build the search index"""
        print(f"🧠 Initializing Soul Memory System v{self.VERSION}...")
        
        if self.memory_file.exists():
            self.vector_search.index_file(self.memory_file)
            
        # Index daily files for the last 7 days
        today = datetime.now()
        for i in range(8):
            date_str = (today - timedelta(days=i)).strftime('%Y-%m-%d')
            daily_file = self.daily_dir / f"{date_str}.md"
            if daily_file.exists():
                self.vector_search.index_file(daily_file)
        
        self.indexed = True
        print("✅ Memory system initialized")

    def _extract_memory_payload(self, text: str) -> str:
        """Extract a compact, reusable memory snippet from verbose context."""
        if not text:
            return ""

        cleaned = text.strip()
        cleaned = re.sub(r'```[\s\S]*?```', ' ', cleaned)
        cleaned = re.sub(r'(?im)^\s*(user|assistant|system)\s*:\s*', '', cleaned)
        cleaned = re.sub(r'Conversation info \(untrusted metadata\):[\s\S]*$', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'Sender \(untrusted metadata\):[\s\S]*$', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'\b(?:System|Assistant|User):\s*', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'<[^>]+>', ' ', cleaned)
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()

        if not cleaned:
            return ""

        fragments = re.split(r'(?<=[。！？!?\.])\s+|\n+', cleaned)
        payloads = []
        seen = set()
        for fragment in fragments:
            fragment = re.sub(r'(?im)^\s*(user|assistant|system)\s*:\s*', '', fragment).strip()
            if not fragment:
                continue
            if len(fragment) < 10 and not re.search(r'[\u4e00-\u9fff]', fragment):
                continue
            key = fragment.lower()
            if key in seen:
                continue
            seen.add(key)
            payloads.append(fragment)

        if not payloads:
            return cleaned[:240]

        return ' '.join(payloads)[:320]

    def _classify_query(self, query: str) -> str:
        """Lightweight query bucket used for adaptive search and context routing."""
        q = (query or '').lower()
        if re.search(r'(記住|偏好|喜歡|身份|user|preference|like|favorite|timezone|name)', q):
            return 'User'
        if re.search(r'(qst|phi|varphi|fsca|dark matter|dark energy|physics|理論|物理|計算|公式|audit|審計)', q):
            return 'QST'
        if re.search(r'(config|設定|配置|token|api|gateway|port|model|provider|telegram|github|pwd|password)', q):
            return 'Config'
        if re.search(r'(上次|之前|剛才|recent|latest|last|今日|昨天|today|yesterday|剛剛)', q):
            return 'Recent'
        if re.search(r'(project|專案|repo|repository|deploy|issue|pr|pull request|workspace|build)', q):
            return 'Project'
        return 'General'

    def _resolve_search_parameters(self, query: str, top_k: int, min_score: float) -> Tuple[int, float]:
        """Tune search breadth/threshold based on query bucket."""
        bucket = self._classify_query(query)
        if bucket == 'User':
            return min(top_k, 3), 2.0
        if bucket == 'Recent':
            return min(top_k, 3), 1.8
        if bucket == 'QST':
            return max(min(top_k, 5), 4), 2.5
        if bucket == 'Config':
            return min(max(top_k, 4), 6), 2.2
        if bucket == 'Project':
            return min(max(top_k, 4), 5), 2.0
        return min(top_k, 2), 3.0

    def _should_persist_memory(self, candidate: str, priority: str, category: str) -> Tuple[bool, str]:
        """Gate what becomes long-term memory."""
        text = (candidate or '').strip()
        if len(text) < 12:
            return False, 'too_short'

        noisy_patterns = [
            r'```', r'\bcommand exited with code\b', r'\btraceback\b', r'\bexec completed\b',
            r'\bdrwxr', r'\bimporterror\b', r'\bpytest\b', r'\bconsole\.log\b'
        ]
        if any(re.search(pattern, text, re.IGNORECASE) for pattern in noisy_patterns):
            return False, 'noisy'

        if priority == 'C':
            return True, 'critical'

        # v3.5.4: 放寬 stable_cues - 技術操作/項目/QST/文件都算重要
        stable_cues = [
            # 原有偏好/決策詞
            r'\b(prefer|likes?|favorite|favour|use|choose|decide|remember|keep|avoid|needs?)\b',
            r'(配置|設定|偏好|喜歡|記住|必須|決定|方案|選擇|保留)',
            # 技術配置詞
            r'\b(api|token|provider|model|gateway|port|github|telegram|workspace|skill|plugin|repo)\b',
            # 技術操作詞（新增）
            r'\b(install|安裝|部署|deploy|update|更新|upload|上傳|download|下載|push|pull|commit|clone)\b',
            r'\b(create|創建|新增|add|edit|修改|delete|刪除|run|運行|test|測試|build|編譯)\b',
            # QST/物理/文件詞（新增）
            r'\b(qst|物理|physics|暗物質|dark matter|暗能量|dark energy|audit|審計|electron|電子)\b',
            r'\b(latex|pdf|tex|markdown|docx|document|文件|文檔|paper|論文|article|文章)\b',
            # 項目詞（新增）
            r'\b(project|專案|youtube|translate|翻譯|simulator|模擬器|dashboard|monitor)\b',
            # 對話主題詞（新增）
            r'\b(劇情|story|plot|動漫|anime|龍珠|dragon ball|尋秦記)\b'
        ]
        # 放寬條件：[I] 或包含技術/項目關鍵詞都保存
        if priority == 'I' or any(re.search(pattern, text, re.IGNORECASE) for pattern in stable_cues):
            return True, 'important'

        if category in {'User_Identity', 'Tech_Config'} and any(re.search(pattern, text, re.IGNORECASE) for pattern in stable_cues):
            return True, 'identity_or_config'

        if category == 'Project' and any(re.search(pattern, text, re.IGNORECASE) for pattern in [r'\b(plan|decision|status|deliver|deploy|issue|fix|update)\b', r'(計劃|決定|進度|部署|修復|更新)']):
            return True, 'project'

        return False, 'not_durable'

    def search(self, query: str, top_k: int = 5, min_score: float = 0.0) -> List[Dict[str, Any]]:
        """Search for relevant memories"""
        if not self.indexed:
            self.initialize()

        resolved_top_k, resolved_min_score = self._resolve_search_parameters(query, top_k, min_score)
        results = self.vector_search.search(query, top_k=resolved_top_k, min_score=resolved_min_score)
        return results

    def add_memory(self, content: str, priority: Optional[str] = None) -> str:
        """Add a new memory with automatic classification and priority detection"""
        parsed = self.priority_parser.parse(content)
        if not priority:
            priority = parsed.priority.value

        candidate = self._extract_memory_payload(parsed.content)
        if not candidate:
            candidate = self._extract_memory_payload(content)

        category = self.dynamic_classifier.classify(candidate)
        should_persist, _reason = self._should_persist_memory(candidate, priority, category)
        if not should_persist:
            return hashlib.md5(candidate.encode()).hexdigest()

        is_duplicate, _dup_type = self.dedup.is_duplicate(candidate, category)
        if is_duplicate:
            return hashlib.md5(candidate.encode()).hexdigest()

        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        memory_entry = f"\n\n---\n\n## {category} [{priority}] ({timestamp})\n\n{candidate}\n"

        # Append to daily file
        today_str = datetime.now().strftime('%Y-%m-%d')
        daily_file = self.daily_dir / f"{today_str}.md"

        with open(daily_file, "a", encoding="utf-8") as f:
            f.write(memory_entry)

        # Update index
        self.vector_search.add_segment({
            'content': candidate,
            'priority': priority,
            'category': category,
            'timestamp': timestamp,
            'source': str(daily_file)
        })

        self.dedup.save(candidate, category)

        # Version control
        self.version_control.commit(f"Add memory: {category} [{priority}]")

        return hashlib.md5(candidate.encode()).hexdigest()

    def post_response_trigger(self, query: str, response: str, importance_threshold: str = "I") -> Optional[str]:
        """Automatically identify and save important content after a response"""
        # Combine query and response for analysis
        full_context = f"User: {query}\nAssistant: {response}"
        
        priority = self.priority_parser.parse(full_context).priority.value
        
        # Check if it meets the importance threshold
        priority_map = {"C": 3, "I": 2, "N": 1}
        if priority_map.get(priority, 0) < priority_map.get(importance_threshold, 0):
            return None
            
        return self.add_memory(full_context, priority)

    def get_stats(self) -> Dict[str, Any]:
        """Get system statistics"""
        return {
            'version': self.VERSION,
            'indexed': self.indexed
        }

    def stats(self) -> Dict[str, Any]:
        """Backward-compatible stats alias."""
        return self.get_stats()

def get_hk_datetime():
    """Get current datetime in Hong Kong time (UTC+8)"""
    return datetime.utcnow() + timedelta(hours=8)
