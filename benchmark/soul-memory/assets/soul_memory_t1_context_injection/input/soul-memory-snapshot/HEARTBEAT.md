# Heartbeat Tasks (丞相職責) v3.1.1

## 🤖 自動執行：Soul Memory Heartbeat 檢查

**每次 Heartbeat 時自動執行以下命令**：

```bash
python3 /root/.openclaw/workspace/soul-memory/heartbeat-trigger.py
```

如果輸出 `HEARTBEAT_OK`，則無新記憶需要處理。

---

## Soul Memory 自動記憶系統 v3.1.1

### 🎯 系統架構（Heartbeat + 手動混合 + v3.1.1 自動儲存）

**v3.1.1 新增**：`post_response_trigger()` 自動儲存機制

| 機制 | 觸發條件 | 分級 |
|------|----------|------|
| **Post-Response Auto-Save** | 每次回應後 | 自動識別優先級 |
| **Heartbeat 檢查** | 每 30 分鐘左右 | 回顧式保存 |
| **手動即時保存** | 重要對話後立即 | 主動式保存 |

---

### 📋 Heartbeat 職責 v3.1.1

**頻率**: 每次 Heartbeat 檢查

**執行清單**:

- [ ] **1. 最近對話回顧**
  - 檢查最近對話是否有重要內容
  - 識別：定義/資料/配置/搜索結果

- [ ] **2. 關鍵記憶保存**
  - 如發現未記錄的重要信息：
    - ✅ 定義類內容 → [C] Critical
    - ✅ 資料/數據 → [I] Important
    - ✅ 配置參數 → [I] Important
    - ❌ 指令/問候 → 跳過

- [ ] **3. 檢查 v3.1.1 自動儲存**
  - 執行以下代碼檢查每日記憶：
  ```python
  from soul_memory.core import SoulMemorySystem
  from pathlib import Path
  from datetime import datetime
  
  system = SoulMemorySystem()
  system.initialize()
  
  today = datetime.now().strftime('%Y-%m-%d')
  daily_file = Path.home() / ".openclaw" / "workspace" / "memory" / f"{today}.md"
  
  if daily_file.exists():
      with open(daily_file, 'r', encoding='utf-8') as f:
          content = f.read()
      auto_save_count = content.count('[Auto-Save]')
      print(f"✅ 自動儲存檢查完成：{auto_save_count} 條新記憶")
  else:
      print("📝 今日無記憶檔案")
  ```

- [ ] **4. 更新記憶索引**
  - 如有保存，調用 `memory.update_index()`
  - 報告：「記憶檢查完成，保存 X 條」

- [ ] **5. 每日檔案檢查**
  - 檢查 `memory/YYYY-MM-DD.md` 狀態
  - 如無當日檔案，留待下次對話

---

### 🤖 v3.1.1 Post-Response Auto-Save 機制

**自動觸發**：每次 Heartbeat 檢查時

**工作流程**：
```python
from soul_memory.core import SoulMemorySystem
from datetime import datetime

system = SoulMemorySystem()
system.initialize()

# 檢查今日記憶檔案
today = datetime.now().strftime('%Y-%m-%d')
daily_file = Path.home() / ".openclaw" / "workspace" / "memory" / f"{today}.md"

if daily_file.exists():
    with open(daily_file, 'r', encoding='utf-8') as f:
        content = f.read()
    auto_save_count = content.count('[Auto-Save]')
    print(f"✅ 自動儲存檢查完成：{auto_save_count} 條新記憶")
else:
    print("📝 今日無記憶檔案")
```

**自動識別規則**：
- 解析回應中的 [C]/[I]/[N] 標籤
- 檢測粵語內容（Cantonese Detection）
- 自動分類到相應類別
- 雙軌保存：JSON 索引 + 每日 Markdown 備份

**保存位置**：
- **JSON 索引**：`cache/index.json` (快速查詢)
- **每日備份**：`memory/YYYY-MM-DD.md` (防止覆蓋)

---

### 🎭 手動即時保存職責

**使用時機**: 重要對話結束時

**觸發句式**:
- 「記住這個...」
- 「保存到記憶...」
- 「這很重要...」

**執行步驟**:
```python
from soul_memory.core import SoulMemorySystem
memory = SoulMemorySystem()
memory.add_memory(
    content="重要對話內容",
    category="User_Identity",  # 或 QST_Physics 等
    priority="I"  # C/I/N
)
```

---

### 🔍 觸發關鍵詞（識別重要內容）

| 類型 | 關鍵詞 | 分級 |
|------|--------|------|
| **定義** | 稱為、指的是、定義為、即係 | [C] |
| **資料** | 檢查結果、統計、數據、分析顯示 | [I] |
| **配置** | 版本、設定、參數、API、http | [I] |
| **搜索** | [Source: web_*]、URL引用 | [I] |
| **指令** | 打開、幫我、運行、刪除 | ❌ |

---

### 📊 報告範例

**無新記憶**:
```
🩺 Heartbeat 記憶檢查 (02-19 00:19 UTC)
- 最近對話：尋秦記討論、Heartbeat 配置更新
- 自動儲存：0 條新記憶
- 重要內容：已手動保存至 MEMORY.md
- 記憶系統：v3.1.1 就緒

HEARTBEAT_OK
```

**有新記憶**:
```
🩺 Heartbeat 記憶檢查 (02-19 01:30 UTC)
- 自動儲存：3 條新記憶
  - [C] Soul Memory v3.1.1 Hotfix 部署
  - [I] Dual-track persistence 機制
  - [I] 廣東話語法分支測試
- 每日檔案：memory/2026-02-19.md 已更新 (6 條)
- 記憶系統：v3.1.1 就緒

↳ 已保存至 MEMORY.md 長期記憶
```

---

### 🎯 核心原則

> **「檢查 + 手動 + 自動」三層保護**

- ✅ **檢查**：Heartbeat 時執行 Python 代碼檢查每日記憶
- ✅ **手動**：對話中聽到「記住」，立即調用 `post_response_trigger()`
- ✅ **自動**：`post_response_trigger()` 自動雙軌保存 (JSON + Markdown)
- ✅ **防護**：追加模式 (append-only) 防止 OpenClaw 會話覆蓋

**實際工作流程**：
1. Heartbeat 檢查點 → 執行 Python 代碼
2. 檢查 `memory/YYYY-MM-DD.md` 中的 `[Auto-Save]` 條目
3. 如有新記憶，報告數量
4. 如無新記憶，回覆 `HEARTBEAT_OK`

---

*丞相李斯職責*
*版本: v3.1.1 - Post-Response Auto-Save + Heartbeat + 手動三軌制*
