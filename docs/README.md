# 文档索引

仓库是项目知识的记录来源。`AGENTS.md` 提供简短导航；本目录保存设计、实现、验证和维护所需的详细资料。

## 知识地图

| 主题 | 权威文档 |
| --- | --- |
| 系统领域、分层与依赖 | [`../ARCHITECTURE.md`](../ARCHITECTURE.md) |
| 设计目录与决策 | [`design-docs/index.md`](design-docs/index.md) |
| 面向代理的工程原则 | [`design-docs/core-beliefs.md`](design-docs/core-beliefs.md) |
| 跨组件技术设计 | [`DESIGN.md`](DESIGN.md) |
| 前端行为与约定 | [`FRONTEND.md`](FRONTEND.md) |
| 产品意图与取舍 | [`PRODUCT_SENSE.md`](PRODUCT_SENSE.md) |
| 面向用户的行为契约 | [`product-specs/index.md`](product-specs/index.md) |
| 执行中与已完成工作 | [`exec-plans/`](exec-plans/) |
| 计划编写规则 | [`PLANS.md`](PLANS.md) |
| 已知技术债 | [`exec-plans/tech-debt-tracker.md`](exec-plans/tech-debt-tracker.md) |
| 质量评估与缺口 | [`QUALITY_SCORE.md`](QUALITY_SCORE.md) |
| 可靠性预期 | [`RELIABILITY.md`](RELIABILITY.md) |
| 安全与隐私 | [`SECURITY.md`](SECURITY.md) |
| 从源码派生的系统事实 | [`generated/`](generated/) |
| 后端运行说明 | [`../server/README.md`](../server/README.md) |
| 桌面端运行说明 | [`../ui/README.md`](../ui/README.md) |

## 权威来源与时效

- 代码和测试说明已实现的精确行为。
- 架构文档定义允许的边界和依赖方向。
- 产品规格定义预期的用户可见行为。
- 设计文档解释决策原因与备选方案。
- 执行计划记录临时状态、进度、决策和完成证据。
- 派生文档必须标明来源和刷新方法。

当来源不一致时，应核实并消除漂移。提议中的行为要明确标注；声称完成需要实际观察到的证据。

## 维护约定

- 保持 `AGENTS.md` 简短，以导航为主。
- 在 `design-docs/index.md` 中登记每份设计文档及验证状态。
- 行为变化时更新相应产品、可靠性、安全和架构文档。
- 只有验收证据齐全后，才能将计划移入 `completed/`。
- 检查、可观测能力或产品领域变化时，重新评估 `QUALITY_SCORE.md`。
- 反复被忽略的文字约束，应逐步转成测试、类型、检查器或脚本。

