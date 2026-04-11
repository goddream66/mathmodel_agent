# outputs 目录说明

这里存放本次运行的落盘产物：

- `problem_text.md`：从 txt/pdf（含可选 OCR）解析出的题面文本
- `report.md`：最终生成的 Markdown 论文草稿

运行示例：

```bash
python -m mathagent --problem-file inputs/problem.pdf --ocr --out-dir outputs
```

