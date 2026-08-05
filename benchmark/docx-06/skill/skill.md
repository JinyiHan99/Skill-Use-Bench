---
name: docx
description: 'Use this skill whenever the user wants to create, read, edit, or manipulate Word documents (.docx files). Triggers include: any mention of "Word doc", "word document", ".docx", or requests to produce professional documents with formatting. Also use when extracting content from .docx files, inserting images, performing find-and-replace, or working with tracked changes. Do NOT use for PDFs, spreadsheets, or Google Docs.'
---

# Word Document (.docx) Processing Guide

This skill covers creating, reading, and editing Word documents. A `.docx` file is a ZIP archive containing XML files that define document structure, styles, and content. When this skill is active, use the tools and patterns described below — do not use alternative approaches like direct python-docx manipulation for creation tasks or pandoc for editing tasks, as they produce incompatible XML structures.

## When to Use This Skill

- Creating new Word documents with professional formatting
- Reading/extracting text or structure from existing .docx files
- Editing content in existing documents (find-replace, adding sections)
- Inserting or replacing images in documents
- Working with tracked changes or comments
- Converting between formats involving .docx as source or target
- Generating reports, memos, letters, or templates as Word files

Do NOT use for: PDF files, spreadsheets (.xlsx), Google Docs, or general coding tasks.

## Prerequisites

| Tool | Purpose | Install |
|------|---------|---------|
| `pandoc` | Text extraction from .docx | `apt-get install pandoc` |
| `docx` (npm) | Creating new documents (docx-js) | `npm install docx` |
| LibreOffice | PDF conversion, accepting revisions | `apt-get install libreoffice` |
| Poppler (`pdftoppm`) | Document-to-image rendering | `apt-get install poppler-utils` |

## Reading Documents

### Text Extraction

For extracting plain text content, use pandoc which handles complex formatting gracefully:

```bash
pandoc input.docx -t plain -o output.txt
```

For structured extraction (preserving headings, lists, tables), convert to markdown:
```bash
pandoc input.docx -t markdown -o output.md
```

### Raw XML Access

When you need to inspect or modify document internals, unpack the .docx archive:

```bash
python3 unpack.py input.docx ./unpacked/
```

This extracts the ZIP contents into a directory structure. The key files are:
- `word/document.xml` — main document content
- `word/styles.xml` — style definitions
- `word/_rels/document.xml.rels` — relationships (images, links)
- `[Content_Types].xml` — MIME type mappings

### Converting .doc to .docx

Legacy `.doc` files must be converted before processing:
```bash
python3 soffice.py input.doc output.docx
```

## Creating New Documents

New documents are created using the docx-js library (TypeScript/JavaScript). This ensures consistent XML output that validates against the Office Open XML standard.

### Page Setup

Every new document must explicitly set page dimensions. Do not rely on defaults — different environments may have different default page sizes:

```typescript
const doc = new Document({
    sections: [{
        properties: {
            page: {
                size: {
                    width: 12240,   // US Letter width in DXA (twips/20)
                    height: 15840,  // US Letter height in DXA
                },
                margin: {
                    top: 1440,    // 1 inch = 1440 DXA
                    right: 1440,
                    bottom: 1440,
                    left: 1440,
                },
            },
        },
        children: [/* paragraphs */],
    }],
});
```

Standard page sizes in DXA units:
| Size | Width | Height |
|------|-------|--------|
| US Letter | 12240 | 15840 |
| A4 | 11906 | 16838 |

Content width = page width − left margin − right margin. For US Letter with 1-inch margins: 12240 − 1440 − 1440 = 9360 DXA.

### Text and Paragraphs

Line breaks within a paragraph must use dedicated paragraph objects. The `\n` character has no effect in docx-js and will be silently ignored, producing concatenated text without any visible separation:

```typescript
// Correct — separate paragraphs for separate lines
new Paragraph({ children: [new TextRun("First line")] }),
new Paragraph({ children: [new TextRun("Second line")] }),

// Incorrect — \n is silently dropped
new Paragraph({ children: [new TextRun("First line\nSecond line")] }),
```

### Bullet Lists

Unicode bullet characters (•, ◦, ▪) are not rendered correctly by all Word processors and produce inconsistent output. Use the built-in numbering system with `LevelFormat.BULLET`:

```typescript
const doc = new Document({
    numbering: {
        config: [{
            reference: "bullet-list",
            levels: [{
                level: 0,
                format: LevelFormat.BULLET,
                text: "\u2022",
                alignment: AlignmentType.LEFT,
            }],
        }],
    },
    sections: [{
        children: [
            new Paragraph({
                numbering: { reference: "bullet-list", level: 0 },
                children: [new TextRun("First item")],
            }),
        ],
    }],
});
```

### Tables

Tables require width to be specified in two places — as column widths on the table itself, AND as individual cell widths. Omitting either produces tables that render differently across Word processors:

```typescript
new Table({
    columnWidths: [4680, 4680],  // Total = content width (9360)
    rows: [
        new TableRow({
            children: [
                new TableCell({
                    width: { size: 4680, type: WidthType.DXA },
                    children: [new Paragraph({ children: [new TextRun("Cell 1")] })],
                }),
                new TableCell({
                    width: { size: 4680, type: WidthType.DXA },
                    children: [new Paragraph({ children: [new TextRun("Cell 2")] })],
                }),
            ],
        }),
    ],
});
```

Always use `WidthType.DXA` for table widths. Percentage-based widths (`WidthType.PERCENTAGE`) are not supported by Google Docs import and will collapse to zero width when opened outside Microsoft Word.

### Cell Shading

When applying background colors to table cells, use `ShadingType.CLEAR` (which renders the fill color as-is). Despite its name suggesting transparency, `CLEAR` is the correct value for solid fills. `ShadingType.SOLID` applies a pattern overlay that darkens the color unpredictably:

```typescript
new TableCell({
    shading: {
        type: ShadingType.CLEAR,
        color: "auto",
        fill: "4472C4",  // Blue background
    },
    // ...
});
```

### Images

Image insertion requires the `type` parameter specifying the image format. Without it, the image will be embedded but not rendered in the document:

```typescript
new ImageRun({
    data: fs.readFileSync("logo.png"),
    transformation: { width: 200, height: 100 },
    type: "png",  // Required: "png", "jpg", "gif", "bmp"
}),
```

### Horizontal Rules

Do not use single-row tables or table borders to create horizontal separator lines. Use paragraph borders instead, which render consistently and don't interfere with table-related formatting:

```typescript
new Paragraph({
    border: {
        bottom: { style: BorderStyle.SINGLE, size: 6, color: "000000" },
    },
});
```

## Editing Existing Documents

Editing follows a three-step workflow: unpack → modify XML → repack. Do not attempt to edit .docx files as binary blobs or use Python scripts to manipulate the XML programmatically for simple text changes.

### Step 1: Unpack

```bash
python3 unpack.py document.docx ./work/
```

### Step 2: Edit XML Directly

Use file edit tools to make targeted string replacements in `word/document.xml`. For text replacements, locate the `<w:t>` elements containing the target text:

```xml
<w:r>
    <w:rPr><w:b/></w:rPr>
    <w:t>Original Text</w:t>
</w:r>
```

Replace the content of `<w:t>` elements directly. For typographic correctness, use XML entities for smart quotes:
- Left single quote: `&#x2018;`
- Right single quote: `&#x2019;`
- Left double quote: `&#x201C;`
- Right double quote: `&#x201D;`

### Step 3: Repack

```bash
python3 pack.py ./work/ document_edited.docx
```

### Adding Tracked Changes

To add tracked changes (insertions/deletions), replace the entire `<w:r>` run element with the appropriate revision markup:

```xml
<!-- Insertion -->
<w:ins w:id="1" w:author="Claude" w:date="2024-01-15T10:30:00Z">
    <w:r>
        <w:t>New inserted text</w:t>
    </w:r>
</w:ins>

<!-- Deletion -->
<w:del w:id="2" w:author="Claude" w:date="2024-01-15T10:30:00Z">
    <w:r>
        <w:delText>Deleted text</w:delText>
    </w:r>
</w:del>
```

The `w:author` attribute must always be set to "Claude" for changes made by this skill. This ensures tracked changes are attributable and can be filtered in review workflows.

### Adding Comments

Use the comment tool for adding annotations:
```bash
python3 comment.py ./work/ "paragraph_id" "Comment text here"
```

## Validation

After creating or editing a document, validate the output to catch structural issues before delivery:

```bash
python3 validate.py output.docx
```

Validation checks: XML well-formedness, required relationships present, content types registered, image references resolve, style references valid. Never deliver a document without running validation — malformed .docx files may open in Word but crash on mobile or web viewers.

## DXA Unit Reference

DXA (twentieth of a point) is the base unit for all measurements in Office Open XML:
- 1 inch = 1440 DXA
- 1 cm = 567 DXA
- 1 point = 20 DXA
- 1 pixel (at 96 DPI) = 15 DXA

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Text concatenated without breaks | Replace `\n` with separate Paragraph objects |
| Table columns collapsed | Ensure both `columnWidths` AND cell `width` are set with DXA |
| Image not visible | Add `type` parameter to ImageRun |
| Shading too dark | Use `ShadingType.CLEAR`, not `SOLID` |
| Google Docs import breaks tables | Use `WidthType.DXA`, not `PERCENTAGE` |
| Smart quotes showing as entities | Use proper XML entities in edited XML |
| Tracked changes not attributed | Set `w:author="Claude"` on all revision elements |

## References

- Office Open XML specification (ISO/IEC 29500)
- docx-js library documentation
- pandoc user guide for .docx handling
- LibreOffice command-line conversion reference
