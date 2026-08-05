---
name: payroll-data-audit
version: 7.4.0
description: 工资数据审核系统，基于确定性规则引擎 + Python 脚本执行。
  全量对齐《工资审核标准流程 SOP》6 步流程。v7.2 修复P0阻断bug：_get_pay_month() 支持
  中文格式（"2026年4月"/"2026年04月"/"202604"），RL-003/RL-007 排除逻辑完全生效。
  v7.1 修复5个P0阻断bug：全角/半角括号统一、RL-003状态列检查、RL-007新员工排除+上月1号调薪豁免、FR-003实习生排除、YL-006上月1号豁免。
  v6.2 新增总审核报告（Master Report）、 规则判定过程详解（judgment）、黄线排除逻辑完善。
  v6.2.1 新增编排指南：单节点原则。
  Use when user asks to 工资数据审核、薪资校验、算薪逻辑验证、薪酬合规检查、
  工资单审核、月度薪资校验、发薪前数据检查、payroll audit、salary check、
  wage verification、payroll compliance.
  不适用于非薪酬类数据审核、纯算薪操作（非审核）、外部薪酬调研、个税/社保计算.
  此技能需手动触发.
---

# Payroll Data Audit v7.4.1

**架构原则**：确定性操作下沉到代码，模糊推理留给 LLM。AI 不做计算和判断，只做路由决策和报告翻译。

## 概述

工资数据审核系统，全量对齐《工资审核标准流程 SOP》6 步流程，对飞书/SAP/ADP 导出的工资表执行自动化合规校验。SOP 覆盖率 95%（41/43 项）。

### v6.3 新功能

- **RL-003 排除逻辑修复**：低于最低工资检查排除实习生(日薪)、实习生(月薪)、当月入职、当月离职、当月长时间请假（病假>5天或事假>5天）
- **RL-004 排除逻辑修复**：社保公积金应缴未缴排除实习生(月薪)
- **YL-006 误报修复**：非1号转正/调薪导致的跨月工资变化不再误报（生效日期在[上月发薪月, 当月发薪月]范围内自动排除）
- **COLUMN_ALIAS 扩充**：新增 40+ 个字段别名变体，覆盖更多实际工资表列名（如"应发工资合计"、"实发工资"、"个人所得税扣款"等）
- **连续在职人员环比分析**：新增 `analyze_continuous_employees()` 方法，自动识别连续在职人员，排除实习生/当月入离职/近期调薪转正/请假>2天/多主体发薪人员，对比12项计薪科目环比变化，自动标记 >10% 异常波动并分类原因
- **场景十·文件交付（Step 9）**：新增 `deliver_audit_files.py`，11个必发文件清单生成 + 审核结论摘要自动生成，流水线结束后 Phase 8/8 自动交付准备
- **审核清单增强**：呈现审核数据情况、通过/不通过原因、判定过程详解

### v6.2 新功能

- **总审核报告（Master Report）**：Phase 7/7，将数据扫描、审核结果、判定过程、问题清单、抽样校验聚合为一份完整的 HTML 总报告（`06_master_report.html`）
- **规则判定过程详解（judgment）**：每条规则输出 `judgment` 字段，包含规则逻辑、检查范围、排除人数及原因、实际检查人数、通过率、判定结论，让看报告的人能看到"怎么判的、排了谁、阈值是什么"
- **黄线排除逻辑完善**：YL-001~004、YL-006 新增实习生/日薪/保洁/当月入职/当月离职排除；YL-005（出勤天数超计薪天数）不排除任何人（数据质量问题全员检查）

### v6.0 新功能

- **表格化报告**：整体以表格形式呈现，信息密度高，替代 v5 的卡片+SVG 风格
- **动态交互看板**：支持筛选/排序/搜索/展开明细/导出CSV/深色模式（零依赖，纯内嵌JS）
- **数据支撑索引**：`data_index.json` 作为报告和看板的关联核心，保证数据一致性
- **三者联动**：报告 ↔ 看板 ↔ 数据索引，通过 rule_id 双向锚定

### 功能范围

- **SOP 第一步（强制）**：数据扫描确认（发薪月/公司主体/计薪项/特殊人员/工号重复检测）
- 字段完整性检查（30+ 列名容错映射）
- 公式校验（Decimal 精度，0.01 容差）
- 业务逻辑校验（出勤工资/天数/绩效系数/加班/最低工资）
- 红线校验（实发≤0、加班超36h、低于最低工资、社保未缴）
- 黄线校验（绩效异常、出勤超限、工资波动）
- 蓝线校验（跨月趋势，仅提示）
- 政策校验（道旅国际豁免、15号后入职、实习生/保洁豁免、离职当月社保）
- 人数对比分析（新入职/离职/波动>5%）
- 总额环比分析（12项计薪科目，±10%阈值自动标记）
- 分主体/分四级部门对比（按公司主体分组环比）
- 按人深入分析（连续在职筛选+排除逻辑+六类变化分类+核实标记）
- HTML/Markdown 审核报告生成
- **数据支撑**：每个审核结论必须有数据依据
- **审核清单看板**：完整条目清单（结果+数据依据+处理建议），HTML+Markdown 双格式
- **分段审核**：7阶段独立执行，避免上下文截断，支持断点续传
- **抽样校验**：随机抽样+独立重算+偏差检测，二次确认审核结果
- **超链接复核**：异常项可点击复核链接（支持 {emp_id}/{emp_name}/{row_index}）
- **端到端流水线**：`run_full_pipeline.py` 一键跑完不中断（数据扫描→审核→报告→看板→抽样→问题清单→总审核报告）

**不覆盖**：实际算薪操作、薪酬市场调研、个税计算、社保核算。

### SOP 流程映射

| SOP 步骤 | 本 Skill 对应 | 说明 |
|---------|-------------|------|
| 第一步：审核流程（强制） | `data_scan.py` + 用户确认 | **禁止跳步** |
| 第二步：数据逻辑验证 | `rules_engine.py` 公式+业务逻辑 | 公式校验+5项业务规则 |
| 第三步：异常数据扫描 | `rules_engine.py` 红/黄/蓝线 | 4红+6黄+4蓝 |
| 第四步：总额对比分析 | `rules_engine.py --prev` 总额环比 | ±10%阈值 |
| 第五步：按人深入分析 | `rules_engine.py --prev` 按人分析 | 排除+6类变化 |
| 第六步：汇总审核报告 | `generate_report.py` / `generate_report_v6.py` | 结构化报告（v5）/ 表格化报告（v6） |
| 第七步：审核清单看板 | `generate_kanban.py` / `generate_kanban_v6.py` | 静态看板（v5）/ 动态交互看板（v6） |
| 第八步：抽样校验 | `sampling_verify.py` | 二次确认审核结果 |
| 数据支撑索引 | `generate_data_index.py` | 三者关联核心（报告↔看板↔数据） |
|| 分段审核编排 | `run_audit.py` | 7阶段独立执行+断点续传 |
|| 端到端流水线 | `run_full_pipeline.py` | 一键跑完不中断，始终生成所有输出（含总报告） |
|| 总审核报告 | `generate_master_report.py` | 聚合所有输出为一份完整 HTML 总报告 |
| 连续在职环比分析 | `rules_engine.py::analyze_continuous_employees()` | 12项计薪科目环比，排除规则，异常标记 |
| 文件交付（Step 9） | `deliver_to_feishu.py` | 11个必发文件上传云盘 + 飞书文档创建 + 交付消息生成（自动化交付，LLM只负责发送） |

## 使用

### 决策路由

先判断用户需求属于哪类场景，再执行对应流程：

| 用户说的 | 匹配场景 | 执行 |
|---------|---------|------|
| "帮我审核本月工资数据" | 完整审核 (Step 1→6) | 先 data_scan → 用户确认 → run_full_audit |
| "快速看看有没有问题" | 红线校验 | `--step red_lines` |
| "发薪前帮我理一下数据" | 字段检查 | `--step fields` |
| "帮我验一下公式对不对" | 公式校验 | `--step formulas` |
| "帮我出个审核报告" | 报告生成 | `generate_report.py` |
| "帮我出个表格版审核报告" | 报告生成 v6 | `generate_report_v6.py` |
| "帮我出个审核清单/看板" | 审核清单看板 | `generate_kanban.py` |
| "帮我出个动态交互看板" | 动态看板 v6 | `generate_kanban_v6.py`（需要 data_index.json） |
| "分段审核/怕上下文截断" | 分段审核 | `run_audit.py` |
| "帮我二次确认审核结果" | 抽样校验 | `sampling_verify.py` |
| "从头到尾跑一遍审核" | 端到端流水线 | `run_full_pipeline.py`（含 v6 报告+看板+索引+总报告+交付摘要） |
| "审核完了把文件发给我" | 文件交付 | `deliver_to_feishu.py`（自动上传11个文件+创建飞书文档+生成交付消息，LLM只负责发送消息） |

### 场景零：数据扫描确认（⚠️ 强制第一步）

**⚠️ 禁止跳过此步骤直接执行审核！**

出报告前必须先数据扫描确认，等待用户回复"确认无误"后才执行后续审核。

**第一步：数据扫描**

```bash
python3 scripts/data_scan.py \
  --data <工资数据.csv> \
  --output /tmp/data_scan_result.json
```

扫描输出以下信息供用户确认：
- 发薪月分布（往月/最新发薪月对应人数）
- 最新发薪月公司主体列表及对应人数
- 主要计薪项数据（应发合计、实发金额合计、加班费合计、个人社保合计、个人公积金合计）
- 特殊字段识别（实习生人数、保洁人数、入职人数、离职人数、转正/调薪人数）
- 工号重复检测

**数据扫描输出示例**：

```
============================================================
📊 工资数据扫描报告
============================================================

📋 总记录数: 2000
📅 最新发薪月: 2026-05

📅 发薪月分布:
  2026-05: 2000 人 ← 最新
  2026-04: 1980 人

🏢 公司主体分布:
  道旅科技: 1500 人
  道旅国际: 300 人
  道旅服务: 200 人

💰 主要计薪项汇总:
  应发合计: ¥15,234,567.89
  实发金额合计: ¥12,345,678.90
  加班费小计: ¥234,567.89
  个人社保: ¥1,234,567.89
  个人公积金: ¥987,654.32

👥 特殊人员:
  新入职: 15 人
  离职: 8 人
  转正: 12 人
  调薪: 5 人

🔍 数据质量检测:
  工号重复: ✅ 无异常
  姓名为空: ✅ 无异常

============================================================
请确认以上数据是否正确，回复'确认无误'后开始正式审核。
============================================================
```

**第二步：用户确认**

等待用户回复"确认无误"或指出问题。**如果用户指出问题，先修正数据再继续。**

**第三步：正式审核**

用户确认后才执行场景一的完整审核流程。

### 场景一：完整审核（Step 1 → 6）

**第一步：获取数据** — 要求用户提供本月工资数据文件（CSV/Excel），**必须同时提供上月数据**用于跨月对比。

**第二步：数据扫描确认** — 见场景零。

**第三步：执行审核**

```bash
python3 -m scripts.rules_engine \
  --data <本月工资数据.csv> \
  --prev <上月工资数据.csv> \
  --output /tmp/audit_result.json
```

**第四步：确认门** — 如果 `summary.blocked == true`（触发红线），**不要生成报告**，先输出红线清单并要求用户确认数据修正后再继续。

**第五步：生成报告** — 通过红线后，用脚本输出 JSON 生成人类可读报告：

```bash
python3 scripts/generate_report.py \
  --input /tmp/audit_result.json \
  --format both
```

**输出文件**：`report.html` + `report.md` 在工作目录。

### 场景二：快速红线校验

```bash
python3 -m scripts.rules_engine \
  --data <工资数据.csv> \
  --step red_lines \
  --output /tmp/red_lines_result.json
```

适用于发薪前快速检查，只需 10 秒。

### 场景三：数据梳理（字段检查）

```bash
python3 -m scripts.rules_engine \
  --data <工资数据.csv> \
  --step fields \
  --output /tmp/fields_result.json
```

检查必填字段是否缺失、格式是否正确。

### 场景四：公式校验

```bash
python3 -m scripts.rules_engine \
  --data <工资数据.csv> \
  --step formulas \
  --output /tmp/formulas_result.json
```

验证应发/实发计算是否与公式一致。

### 场景五：报告生成

```bash
# HTML 可视化报告
python3 scripts/generate_report.py \
  --input /tmp/audit_result.json --format html --output report.html

# Markdown 报告
python3 scripts/generate_report.py \
  --input /tmp/audit_result.json --format markdown --output report.md

# 两者都生成
python3 scripts/generate_report.py \
  --input /tmp/audit_result.json --format both
```

### 场景六：审核清单看板（Step 7）

**审核清单看板 = 完整审核条目展开清单**，每条包含审核结果 + 数据依据 + 处理建议。
```bash
python3 scripts/generate_kanban.py --input /tmp/audit_result.json --format both
```
**超链接复核**：`--review-link "https://hr.example/emp/{emp_id}?row={row_index}"`
输出 `kanban.html` + `kanban.md`，展开 rules.json 所有规则（28+条）。
### 场景七：抽样校验（Step 8，推荐）

审核完成后进行二次确认：`python3 scripts/sampling_verify.py --data <数据.csv> --audit <审核结果.json> --sample-size 30 --threshold 0.05 --output <输出.json>`

**流程**：随机抽样→独立重算（公式/红线/业务规则）→交叉对比→偏差率≤5%通过；>5%触发根因分析后重新审核。偏差超标时输出根因报告并使用 `run_audit.py --resume` 断点重审。
### 场景八：分段审核编排（推荐大数据量场景）

`python3 scripts/run_audit.py --data <本月.csv> --prev <上月.csv> --output-dir /tmp/audit_phases`

7个独立阶段（字段→公式→业务规则→红线阻断门→黄线→蓝线→汇总），每阶段输出独立 JSON，避免上下文截断。红线触发时自动阻断后续阶段。支持断点续传：`--resume`。

### 场景九：端到端流水线（一键跑完不中断）
**输出文件**：`00_data_scan.json` `01_audit_result.json` `02_report.html/md` `02_report_v6.html/md`（表格化，推荐）`02a_data_index.json`（三者关联核心）`03_kanban.html/md` `03_kanban_v6.html`（动态交互，推荐）`04_sampling_verify.json` `05_issue_report.md`(问题清单) `06_master_report.html`(总审核报告) `audit_summary.md`(审核结论摘要)。
```bash
python3 scripts/run_full_pipeline.py --data <本月.csv> --prev <上月.csv> --output-dir /tmp/audit_output --review-link "https://hr.example/emp/{emp_id}?row={row_index}"
```

### 场景十：文件交付到飞书（Step 9，强制）

**审核完成后必须执行此步骤，不可跳过。**

```bash
python3 scripts/deliver_to_feishu.py --output-dir /tmp/audit_output --audit-result /tmp/audit_output/01_audit_result.json
```

**自动化交付流程**（LLM 不可干预、不可跳过）：
1. **验证文件完整性** — 检查 11 个必发文件全部存在，缺失则拒绝执行
2. **上传文件到飞书云盘** — 逐一上传，输出上传结果
3. **创建飞书文档** — 用 `02_report_v6.md` import 为 docx 格式
4. **生成交付消息** — 自动生成包含文档链接+文件清单+总额环比的完整飞书消息
5. **输出 delivery_message.md + delivery_result.json** — 供 LLM 直接发送

**⚠️ LLM 层唯一职责**：把 `delivery_message.md` 的内容通过消息工具发送到飞书。
**⚠️ 禁止**：自行挑选文件上传、自行创建文档格式、自行裁剪交付内容。

### 数据来源

- **优先**：飞书多维表格导出 CSV / SAP HCM 导出 Excel / ADP 导出
- **降级**：要求用户提供 CSV/Excel 文件
- **兜底**：无任何数据源时拒绝执行，回复："请提供工资数据文件（CSV 或 Excel 格式），我才能进行审核。"

### 数据支撑原则

**每个审核结论必须有数据依据，不凭空判断。** 这是审核系统的核心原则——**"审核通过"不是感觉出来的，是数据算出来的。**

#### 一、"通过"结论的数据支撑逻辑

每个判定为"正常/通过"的审核项目，必须同时输出以下三项数据：

| 要素 | 说明 | 示例 |
|------|------|------|
| **检查数** | 共检查了多少条记录 | "2000条记录" |
| **通过数** | 多少条符合规则 | "1998条通过" |
| **阈值** | 判定标准是什么 | "容差0.01元" |

**完整示例**：
- ✅ 正确："公式校验通过：2000条记录全部在0.01元容差范围内，通过率100%"
- ❌ 错误："公式校验通过"（无数据支撑，无法验证结论可靠性）

**为什么必须这样**：如果没有检查数和通过数，"通过"可能是只检查了1条、也可能是2000条——可信度完全不同。

#### 二、异常结论的数据支撑

必须列出具体人员、工号、异常值、预期值、违反的规则ID：

- ✅ 正确："张三（工号E001）实发金额为-500元，预期值≥0，违反RL-001（实发≤0），严重等级：BLOCK"
- ❌ 错误："有人实发金额异常"（无具体信息，无法采取行动）

#### 三、趋势判断的数据支撑

必须给出具体数值、变化幅度、驱动因素：

- ✅ 正确："应发总额环比+12.3%（¥15.2M→¥17.1M），超出±10%正常范围，主要由业务线奖金增加导致（+45.2%，¥2.1M→¥3.0M）"
- ❌ 错误："工资总额有明显增长"（无数据，无法判断合理性）

#### 四、排除说明的数据支撑

当某人被排除在异常分析外时，必须说明排除原因和依据：

- ✅ 正确："李四（工号E002）应发变化+15.8%，但4月有调薪记录（调薪生效日期=2026-04-01），匹配排除规则'调薪'，已排除"
- ❌ 错误："李四的变化是正常的"（无依据）

#### 五、红线阻断的数据支撑
红线触发时输出：触发人数/具体名单(工号+姓名+异常值)/违反规则(ID+名称)。
**报告"结论与建议"结构**：总体结论(检查数+各维度通过/异常数)→各维度详情表格(检查数/通过数/异常数/通过率/结论)→异常明细→建议行动(基于具体数据)。

### 列名容错

脚本内置 `COLUMN_ALIAS` 字典，自动映射 30+ 种常见列名变体。如果列名无法识别，脚本返回 `{"error": "Missing column: XXX"}`，LLM 必须原文转述。

### 精度处理

金额计算使用 `decimal.Decimal`，避免浮点误差累积。公式校验容差 0.01（1 分钱）。

### 规则更新

所有规则集中在 `references/rules.json`。修改规则只需编辑此文件，无需修改脚本。**为什么这样设计**：业务规则变化频繁（如最低工资调整），集中管理避免每次都要改代码。

#### 如何扩展规则

1. **新增红线**：在 `rules.json` 的 `red_lines` 数组中添加新对象，包含 `id`、`name`、`condition`、`field`、`severity: "BLOCK"`
2. **新增黄线**：在 `yellow_lines` 数组中添加，`action: "flag_and_explain"`
3. **新增蓝线**：在 `blue_lines` 数组中添加，`action: "note_only"`
4. **新增政策**：在 `policies` 数组中添加，包含 `condition`（触发条件）和 `effect`（豁免效果）
5. **新增业务规则**：在 `business_rules` 数组中添加，支持 `field1 <= field2` 类双字段比较
6. **新增排除条件**：在 `person_analysis_exclusions` 对象中添加新 key，包含 `field`、`condition`、`note`

**规则 ID 命名规范**：`{类型}-{序号}`，如 `RL-005`（第5条红线）、`YL-007`（第7条黄线）、`POL-006`（第6条政策）、`BR-005`（第5条业务规则）

**添加规则后不需要修改任何 Python 代码**，引擎自动加载。

### 红线阻断

红线触发 → 立即阻断，不继续后续步骤，不生成报告。**为什么**：红线代表严重违规（如负实发、低于最低工资），必须先修正数据再审核，否则报告无意义。

### 编排指南：单节点原则（v6.2.1 新增）

**本 Skill 被 Workflow Orchestration Skill 编排时，必须作为单节点调用。**

根因：`run_full_pipeline.py` 已是端到端流水线，内部按序完成所有 8 步（扫描→规则→红黄蓝线→报告→看板→抽样→问题清单→总报告）。拆成多节点编排无收益——每个节点仍调用同一个 skill，内部全量执行一遍。

| 错误做法 | 正确做法 |
|----------|----------|
| N1 data_scan → N2 rules_engine → N3 generate_report → ... | N1 run_full_pipeline.py 一键跑完 |

**唯一例外**：当业务确实需要中间状态可见性或独立重试时，才使用 `run_audit.py` 分段模式（7阶段+断点续传），但仍然是**同一 skill 的多次调用**，不是拆成多个 skill。

### 常见错误场景

| 场景 | 处理 |
|------|------|
| 数据源字段缺失 | 列出缺失字段清单，要求用户补充后重试 |
| 日期格式混乱 | 脚本自动尝试多种格式解析，失败则返回错误 |
| 无上月数据 | 跨月对比/按人分析跳过，在报告中标注"无基准数据" |
| Python 环境无 pandas | 提示用户 `pip install pandas numpy openpyxl` |
| 红线触发 | 立即阻断，不继续后续步骤 |

### 目录结构

```
payroll-data-audit/
├── SKILL.md
├── _meta.json
├── scripts/
│   ├── data_scan.py               # 数据扫描（SOP 第一步）
│   ├── rules_engine.py            # 统一规则引擎（OOP）
│   ├── generate_report.py         # HTML/Markdown 报告生成器（v5，兼容）
│   ├── generate_report_v6.py      # 表格化报告生成器（v6，推荐）
│   ├── generate_kanban.py         # 审核清单看板生成器（Step 7，静态）
│   ├── generate_kanban_v6.py      # 动态交互看板生成器（v6，推荐）
│   ├── generate_data_index.py     # 数据支撑索引生成器（v6，三者关联核心）
│   ├── run_audit.py               # 分段审核编排器（7阶段+断点续传）
│   ├── run_full_pipeline.py       # 端到端流水线（含 v6 输出 + 总报告）
│   ├── generate_master_report.py  # 总审核报告生成器（v6.2，聚合所有输出）
│   ├── sampling_verify.py         # 抽样校验器（二次确认）
│   ├── deliver_audit_files.py     # 文件交付清单生成器（v6.3，仅生成清单，已废弃）
│   ├── deliver_to_feishu.py       # 文件交付到飞书（v7.4，自动上传+文档+消息，推荐）
│   └── tests/                     # pytest 测试套件
│       ├── test_rules_engine.py
│       └── test_parameterized.py
├── references/
│   └── rules.json                 # 所有规则声明（唯一真相来源）
└── .github/workflows/
    └── test.yml                   # CI/CD
```

### 依赖

```bash
pip install pandas numpy openpyxl
```

### 测试

```bash
cd payroll-data-audit
python -m pytest scripts/tests/ -v --cov=scripts.rules_engine --cov-report=term-missing
```

CI/CD 自动运行：push/PR 时触发 pytest + coverage（80% 门槛）+ lint。
