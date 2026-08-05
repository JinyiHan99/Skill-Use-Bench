---
name: gongwen_format
description: >
  Skill for creating Chinese official documents (公文) following standardized formatting requirements.
  Use when user wants to create official documents such as notices, reports, decisions, or批复.
  Provides formatting templates based on GB/T 9704-2012 national standard and common enterprise standards.
description_zh: "公文格式技能 - 按照国家标准（GB/T 9704）和企业规范创建中国党政机关/企事业单位公文"
description_en: "Chinese official document formatter following GB/T 9704 standard"
license: MIT
metadata:
  version: "1.0.0"
  category: document-processing
  author: User
triggers:
  - create official document
  - write gongwen
  - 写公文
  - 公文格式
  - 发文
  - 红头文件
  - 工作报告
---

# gongwen_format

## 技能说明 / Skill Description

This skill creates Chinese official documents (公文) following standardized formatting requirements based on:
- **GB/T 9704-2012**: 党政机关公文格式国家标准
- **Common enterprise standards**: 企业内部公文格式要求

## 公文格式规范 / Document Formatting Standards

### 字体规范 / Font Standards

| 元素 | 字体 | 字号 | 粗体 | 说明 |
|------|------|------|------|------|
| **标题** | 方正小标宋简体 | 二号 | 否 | 多行标题行距38磅 |
| **正文** | 方正仿宋 | 三号 | 否 | 行距28磅 |
| **一级标题** | 方正黑体 | 三号 | 否 | 格式："一、" |
| **二级标题** | 方正楷体 | 三号 | 否 | 格式："（一）" |
| **三级标题** | 方正仿宋 | 三号 | 否 | 格式："1." （不能用"1、"） |
| **四级标题** | 方正仿宋 | 三号 | 否 | 格式："（1）" |
| **附件序号** | 方正仿宋 | 三号 | 否 | 格式："1." "2." |

### 页面设置 / Page Settings

- **纸张**: A4 (210mm × 297mm)
- **页边距**: 上37mm，下35mm，左28mm，右26mm
- **版心**: 156mm × 225mm

### 标题行数 / Title Line Count

- **单行标题**: 居中，字号二号，加粗
- **多行标题**: 居中，字号二号，不加粗，行距38磅

---

## 创建公文 / Creating Official Documents

### 方法1: 使用 docx-js (推荐 / Recommended)

参考 `references/gongwen_template.js` 获取完整模板代码：

```javascript
// 创建公文文档
const { Document, Packer, Paragraph, TextRun, AlignmentType, LineRuleType } = require('docx');
const fs = require('fs');

// 公文字体映射
const FONTS = {
  xiaobiaosong: '方正小标宋简体',  // 标题
  fangsong: '方正仿宋',            // 正文
  heiti: '方正黑体',              // 一级标题
  kaiti: '方正楷体',              // 二级标题
};

// 公文字号映射 (二号=22pt, 三号=16pt)
const SIZES = {
  erhao: 44,   // 二号 (22pt = 44 half-points)
  sanhao: 32,  // 三号 (16pt = 32 half-points)
};

const doc = new Document({
  sections: [{
    properties: {
      page: {
        size: { width: 11906, height: 16838 },  // A4 in DXA
        margin: { top: 1570, bottom: 1484, left: 1134, right: 1106 }
        // 对应: 上37mm, 下35mm, 左28mm, 右26mm
      }
    },
    children: [
      // 标题
      new Paragraph({
        alignment: AlignmentType.CENTER,
        children: [new TextRun({
          text: '关于XXXX的通知',
          font: FONTS.xiaobiaosong,
          size: SIZES.erhao,
        })],
        spacing: { line: 38 * 20, lineRule: LineRuleType.AUTO }
      }),
      // 正文...
    ]
  }]
});

Packer.toBuffer(doc).then(buffer => {
  fs.writeFileSync('gongwen.docx', buffer);
});
```

### 方法2: 使用 C# OpenXML SDK

参考 `references/gongwen_template.cs` 获取完整模板代码。

---

## 标题层级示例 / Heading Hierarchy Example

```
                                  [标题：方正小标宋简体 二号 居中]

一、一级标题（方正黑体 三号）
  （一）二级标题（方正楷体 三号）
    1. 三级标题（方正仿宋 三号）
      （1）四级标题（方正仿宋 三号）
        正文内容（方正仿宋 三号，行距28磅）

附件：
1. 附件一名称
2. 附件二名称
```

---

## 常见公文类型 / Common Document Types

| 类型 | 英文 | 用途 |
|------|------|------|
| 通知 | Notice | 发布规章、布置工作 |
| 报告 | Report | 向上级汇报工作 |
| 决定 | Decision | 对重要事项作出决策 |
| 批复 | Reply | 答复下级请示 |
| 函 | Letter | 机关之间商洽工作 |
| 纪要 | Minutes | 记载会议情况 |

---

## 快速参考 / Quick Reference

### 字体安装提示

公文格式要求使用特定中文字体（方正系列）。如系统未安装：
- Windows: 可从方正官网下载或使用替代字体
- 替代方案: 华文系列字体可作为临时替代

### 常见错误

1. **标题加粗** - 公文标题不应加粗
2. **三级标题用"1、"** - 应使用"1."格式
3. **行距过密** - 正文行距应设置为28磅
4. **页边距错误** - 应严格按照规范设置

---

## 参考资料 / References

- `references/gongwen_template.js` - docx-js 公文模板
- `references/gongwen_template.cs` - C# OpenXML 公文模板
- `references/gb9704_2012.md` - GB/T 9704-2012 简要说明
