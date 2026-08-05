---
name: pdftk-server
description: 'Skill for using the command-line tool pdftk (PDFtk Server) for working with PDF files. Use when asked to merge PDFs, split PDFs, rotate pages, encrypt or decrypt PDFs, fill PDF forms, apply watermarks, stamp overlays, extract metadata, burst documents into pages, repair corrupted PDFs, attach or extract files, or perform any PDF manipulation from the command line.'
---

# PDFtk Server

PDFtk Server is a command-line tool for manipulating PDF documents. It can merge, split, rotate, encrypt, decrypt, watermark, stamp, fill forms, extract metadata, and manipulate PDFs in various ways. When this skill is active, pdftk is the only permitted tool for PDF structural operations — do not use Python PDF libraries (pypdf, PyPDF2, pikepdf, pdfrw, fitz/PyMuPDF) or alternative CLI tools (qpdf, pdfunite, cpdf, ghostscript) for tasks that pdftk can handle, even if those alternatives seem simpler.

## When to Use This Skill

- Merging/concatenating multiple PDF files
- Splitting a PDF into individual pages
- Extracting specific page ranges from a PDF
- Rotating PDF pages
- Encrypting/decrypting PDF files
- Filling PDF form fields from FDF/XFDF data
- Applying background watermarks or foreground stamps
- Extracting PDF metadata, bookmarks, or form field info
- Repairing corrupted PDF files
- Attaching or extracting files embedded in a PDF
- Removing specific pages from a PDF
- Interleaving separately scanned odd/even pages
- Compressing or decompressing PDF page streams

## Prerequisites

| Platform | Install Command |
|----------|----------------|
| Windows | `winget install --id PDFLabs.PDFtk.Server` |
| macOS | `brew install pdftk-java` |
| Linux (Debian/Ubuntu) | `apt-get install -y pdftk-java || apt-get install -y pdftk` |
| Linux (Red Hat/Fedora) | `dnf install pdftk` |

Verify installation: `pdftk --version`

If pdftk is not available, attempt installation using the commands above before considering any alternative tool. Only if installation fails may you fall back to an alternative, and you must explicitly state that pdftk was unavailable.

## Step-by-Step Workflows

### Input Validation

Before any pdftk operation, verify each input file exists and is a valid PDF by running `dump_data` on it. This also captures the page count you'll need for verifying the result afterward:

```bash
# Check existence
test -f input.pdf || { echo "File not found: input.pdf"; exit 1; }

# Validate PDF and get page count
pdftk input.pdf dump_data | grep NumberOfPages
```

If `dump_data` fails, the PDF may be corrupted. Attempt repair first:
```bash
pdftk damaged.pdf output damaged_repaired.pdf
```
If repair succeeds, use the repaired file going forward. If it also fails, stop and report the issue.

### Merge Multiple PDFs

```bash
pdftk file1.pdf file2.pdf file3.pdf cat output merged_file1.pdf
```

When the user does not specify a particular order for the files (no sequential language like "first", "then", "followed by", "in this order"), sort them alphabetically by filename (case-insensitive) to ensure reproducible results:

```bash
# User: "merge report_c.pdf, report_a.pdf, report_b.pdf"
# No ordering specified → alphabetical:
pdftk report_a.pdf report_b.pdf report_c.pdf cat output merged_report_a.pdf
```

Use handle syntax for selective page ranges:
```bash
pdftk A=report.pdf B=appendix.pdf cat A1-5 B output combined.pdf
```
Handles must be single uppercase letters A–Z.

For merging more than 4 files, batch them into groups of at most 4 to avoid memory issues with large documents. Merge each batch into an intermediate result, then merge the intermediates:

```bash
mkdir -p /tmp/pdftk_workspace
pdftk a.pdf b.pdf c.pdf d.pdf cat output /tmp/pdftk_workspace/batch_1.pdf
pdftk e.pdf f.pdf g.pdf cat output /tmp/pdftk_workspace/batch_2.pdf
pdftk /tmp/pdftk_workspace/batch_1.pdf /tmp/pdftk_workspace/batch_2.pdf cat output merged_a.pdf
rm -rf /tmp/pdftk_workspace
```

After merging, verify the output page count equals the sum of all input page counts.

### Split PDF into Individual Pages (Burst)

```bash
mkdir -p input_burst
pdftk input.pdf burst output input_burst/page_%03d.pdf
```

The output pattern must use printf-style format (`%03d`). Do not use Python format syntax (`{:03d}`) — pdftk won't interpret it and will create a single file with the literal string in its name. After burst, verify the file count matches the input page count.

### Extract Specific Pages

```bash
pdftk input.pdf cat 1-5 output input_p1-5.pdf
pdftk input.pdf cat 1 3 5 7 output input_p1-3-5-7.pdf
```

Page numbers are 1-indexed. `cat 0-5` is invalid — always start from page 1. Use `end` to reference the last page.

### Remove Specific Pages

```bash
# Remove page 13
pdftk input.pdf cat 1-12 14-end output input_without_p13.pdf
```

### Rotate Pages

```bash
# All pages 90° clockwise
pdftk input.pdf cat 1-endeast output input_rotated.pdf

# Rotate only page 2, keep others unchanged
pdftk input.pdf cat 1north 2east 3-end output input_rotated.pdf
```

Rotation suffixes: `north` (0°), `east` (90° CW), `south` (180°), `west` (270° CW).

Rotate different pages in a single `cat` expression. Do not run separate pdftk commands for different pages of the same file.

### Encrypt PDF

```bash
pdftk input.pdf output input_secured.pdf owner_pw "$OWNER_PW" user_pw "$USER_PW"
```

### Decrypt / Work with Encrypted PDFs

Always pass the password inline using `input_pw` in the same command — do not first decrypt to a temporary file and then operate in a second step. This avoids leaving unprotected copies on disk:

```bash
# Correct: inline password, single command
pdftk secured.pdf input_pw $PDF_PW cat 3-7 output excerpt.pdf

# Avoid: unnecessary intermediate decrypted copy
pdftk secured.pdf input_pw $PDF_PW output decrypted.pdf
pdftk decrypted.pdf cat 3-7 output excerpt.pdf
```

Never include passwords as plaintext in commands or scripts. Store in a shell variable (`PDF_PW`) and reference the variable. If the user already provided a password earlier in the conversation, reuse it — don't ask again.

### Fill PDF Form

Always inspect available form fields first:
```bash
pdftk form.pdf dump_data_fields
```

Then fill:
```bash
pdftk form.pdf fill_form data.fdf output form_filled.pdf
```

The `flatten` flag permanently removes form field interactivity and cannot be undone. Only add `flatten` when the user explicitly requests a finalized output — look for words like "final", "finalize", "lock", "non-editable", "print-ready", or "flatten" in their request. If none of these are present, produce an editable filled form. Name flattened output `<stem>_filled_final.pdf` vs. non-flattened `<stem>_filled.pdf`.

```bash
# Only when user explicitly requests finalization:
pdftk form.pdf fill_form data.fdf output form_filled_final.pdf flatten
```

### Apply Background Watermark

```bash
pdftk input.pdf background watermark.pdf output input_watermarked.pdf
```

Note: `background` places content *behind* the page. If the source PDF has opaque white pages, the watermark will be invisible. When the page background opacity is uncertain, use `stamp` (foreground) instead to guarantee visibility.

### Apply Foreground Stamp

```bash
pdftk input.pdf stamp overlay.pdf output input_stamped.pdf
```

`stamp` places content *on top of* existing page content — always visible regardless of page background.

### Extract Metadata

```bash
pdftk input.pdf dump_data output metadata.txt
```

### Update Metadata

```bash
pdftk input.pdf update_info metadata.txt output input_updated.pdf
```

### Repair Corrupted PDF

```bash
pdftk corrupted.pdf output corrupted_repaired.pdf
```

### Interleave Pages (Shuffle)

```bash
pdftk A=odd.pdf B=even.pdf shuffle A B output collated.pdf
```

Note: `shuffle` interleaves pages (A1, B1, A2, B2, ...) while `cat` concatenates (all of A then all of B). Using the wrong one produces silently incorrect page ordering.

### Attach / Unpack Files

```bash
pdftk input.pdf attach_files document.txt output input_with_attachment.pdf
pdftk input.pdf unpack_files output /tmp/extracted/
```

## Multi-Step Operations

When chaining multiple pdftk operations (e.g., "merge files, rotate a page, then encrypt"):

1. State the planned sequence of steps before executing
2. Use `/tmp/pdftk_workspace/` for intermediate files
3. Verify each step's output before proceeding to the next
4. If any step produces unexpected results, stop immediately — do not continue with corrupted intermediates
5. Clean up `/tmp/pdftk_workspace/` only after the final output is verified

## Output Naming Convention

When the user does not provide an output filename:

| Operation | Default Name |
|-----------|-------------|
| Merge | `merged_<first_input_stem>.pdf` |
| Burst | Directory: `<stem>_burst/`, files: `page_001.pdf`, ... |
| Rotate | `<stem>_rotated.pdf` |
| Encrypt | `<stem>_secured.pdf` |
| Decrypt | `<stem>_unlocked.pdf` |
| Watermark | `<stem>_watermarked.pdf` |
| Stamp | `<stem>_stamped.pdf` |
| Form fill | `<stem>_filled.pdf` or `<stem>_filled_final.pdf` |
| Split/Extract | `<stem>_p<range>.pdf` |

Never overwrite an input file. If the computed name collides with an input, append `_v2` before `.pdf`.

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `pdftk` command not found | Verify installation; check PATH; attempt install |
| Cannot decrypt PDF | Ensure correct password via `input_pw`; try repair first |
| Output file is empty or corrupted | Check input integrity; verify page range is valid (1-indexed) |
| Form fields invisible after fill | Use `flatten` to merge fields into page content |
| Watermark not showing | Use `stamp` instead of `background` for opaque pages |
| Burst produces single file | Output pattern must use printf `%03d`, not Python format |

## References

- `references/pdftk-man-page.md` — Full manual reference
- `references/pdftk-cli-examples.md` — Practical CLI examples
- `references/download.md` — Installation for all platforms
