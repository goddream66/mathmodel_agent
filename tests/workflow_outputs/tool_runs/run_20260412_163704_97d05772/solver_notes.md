# Solver Notes

- subproblem_count: 2
- detected_numbers: [1.0, 7.0, 2.0]

## 问题1
- objective: 建立预测模型并给出可解释的误差评估。
- chosen_method: 线性/非线性回归
- constraints:
  - 训练与验证数据划分方式需要保持时序一致。

## 问题2
- objective: 在满足约束的前提下最大化收益、效率或覆盖率。
- chosen_method: 线性规划
- constraints:
  - 题目文本中存在显式约束，需要转写为数学不等式或逻辑条件。
  - 需要明确资源上限、容量约束和业务规则。