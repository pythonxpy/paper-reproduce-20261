# 三维重建研究方向工作区

这个工作区把参考论文中的思路整理成两个可以落地推进的研究方向，目标是服务于开题、论文构思、实验设计和后续实现。

## 推荐主线

优先推进 **方向一：基于不确定性几何先验的大场景 Gaussian 表面重建**。

原因：

- 数据集、指标和 baseline 更成熟，适合稳定产出论文。
- 更容易围绕“提高三维重建精度”建立清晰贡献。
- 可以自然复用 3DGS、2DGS、CityGaussian、CityGaussianV2、VGGT-Ω、Depth Anything、单目法线估计等已有方法。

方向二 **面向生成视频的几何一致性约束三维重建** 更适合作为创新扩展或第二篇工作，难点在于生成视频几何不一致、评测标准更复杂、baseline 复现成本更高。

## 文件说明

- [research_directions.md](research_directions.md)：两个研究方向的完整方案，包括问题、方法、数据集、对比方法、指标和风险。
- [experiment_matrix.md](experiment_matrix.md)：实验配置矩阵，包括主实验、消融实验、鲁棒性实验和结果表格模板。
- [proposal_outline.md](proposal_outline.md)：开题报告/论文初稿提纲，可直接扩写成中文论文结构。
- [execution_guide.md](execution_guide.md)：两篇论文从复现、实验到写作的总执行手册。
- [paper1_up_gaussian_checklist.md](paper1_up_gaussian_checklist.md)：论文一的实验步骤、消融表、图表清单和写作大纲。
- [paper2_gc_worldrecon_checklist.md](paper2_gc_worldrecon_checklist.md)：论文二的实验步骤、指标、图表清单和写作大纲。
- [weekly_progress_template.md](weekly_progress_template.md)：每周实验与写作记录模板。
- [docs/autodl_citygaussian_reproduction.md](docs/autodl_citygaussian_reproduction.md)：AutoDL 复现 CityGaussian/CityGaussianV2 的环境、脚本和实验说明。

## AutoDL 复现入口

在 AutoDL 中建议先执行：

```bash
git clone https://github.com/pythonxpy/paper-reproduce-20261.git
cd paper-reproduce-20261
bash scripts/autodl_setup_citygaussian.sh
bash scripts/run_citygaussian_v2_smoke.sh
```

CityGaussianV2 通过后，再执行：

```bash
bash scripts/run_citygaussian_v1_smoke.sh
```

## 建议推进顺序

1. 先选择方向一作为主论文方向。
2. 用 DTU 或 Tanks and Temples 做小规模可控验证。
3. 再扩展到 MatrixCity、KITTI-360 或 ScanNet++ 等大场景/真实视频数据。
4. 如果时间允许，把方向二作为生成视频场景下的补充实验或未来工作。

## 当前第一步

先完成论文一的最小闭环：

1. 选定 DTU 或 Tanks and Temples 的 1 个场景。
2. 跑通 3DGS baseline。
3. 跑通 2DGS 或 CityGaussianV2 baseline。
4. 接入一种几何先验，优先深度或法线。
5. 记录第一周实验到 `experiments/week01_baseline.md`。
