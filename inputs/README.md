# inputs 目录说明

把需要读取的输入文件放在这里（例如 PDF 题目、图片、数据等）。

示例（读取 PDF 题目）：

```bash
python -m mathagent --problem-file inputs/problem.pdf
```

如果需要对 PDF 内图片做 OCR（表格截图/图表里的文字），运行时加参数：

```bash
python -m mathagent --problem-file inputs/problem.pdf --ocr
```

如果你的 PDF 图片是“整页渲染/矢量图/背景图”导致抽取不到内嵌图片，可以改用整页 OCR：

```bash
python -m mathagent --problem-file inputs/problem.pdf --ocr --ocr-mode page
```
