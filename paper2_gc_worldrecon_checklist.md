# 论文二执行清单：GC-WorldRecon

题目：

**面向生成视频的几何一致性约束三维重建**

英文可用题目：

**GC-WorldRecon: Geometry-Consistent World Reconstruction from Generated Videos**

## 1. 论文二目标

证明：生成视频虽然视觉连续，但三维几何不一致；通过几何一致性诊断和约束，可以重建出更稳定、可探索的三维世界。

## 2. 最小可行实验

### 2.1 输入数据

第一优先级：

- WorldScore 样例。
- 开源生成视频模型输出。
- 论文或项目中公开的生成视频样例。

第二优先级：

- Replica/Habitat/Kubric 合成视频。
- RealEstate10K 或 ScanNet 真实视频作为辅助对照。

### 2.2 Baseline

必须对比：

- COLMAP + 3DGS。
- VGGT-Ω/DUSt3R + 3DGS 或 2DGS。
- World Reconstruction From Inconsistent Views。

可选对比：

- Text2Room。
- LucidDreamer。
- WonderJourney。
- WonderWorld。
- ViewCrafter/SEVA/Gen3C 作为生成视频来源。

## 3. 实验步骤

### Step 1：证明生成视频重建失败

输入：

- 3-5 个生成视频。

操作：

- 抽帧。
- 估计相机和点云。
- 训练 3DGS/2DGS。
- 可视化新视角。

观察：

- 多层墙面。
- 物体漂移。
- 闭环错位。
- 点云分裂。
- 新视角破碎。

完成标准：

- 至少有 3 个清楚失败案例。
- 每个失败案例有图像、点云或新视角截图。

### Step 2：几何提升

使用前馈几何模型为每帧生成：

- depth。
- normal。
- camera pose。
- local point cloud。

完成标准：

- 能把视频帧转换为点云序列。
- 能计算相邻帧对齐误差。
- 能可视化错误区域。

### Step 3：不一致检测

指标：

- 相邻帧重投影误差。
- 点云 ICP/alignment error。
- 深度变化异常。
- 法线变化异常。
- 语义区域漂移。

输出：

- frame confidence。
- pixel/region confidence。
- unreliable frame list。

完成标准：

- 能标出最不可靠的帧。
- 能解释为什么这些帧破坏重建。

### Step 4：一致性约束

第一版必须做：

- depth consistency。
- normal consistency。
- reprojection consistency。

第二版再做：

- semantic consistency。
- cycle consistency。
- frame filtering。

推荐损失：

```text
L = L_rgb
  + lambda_depth * C * L_depth_consistency
  + lambda_normal * C * L_normal_consistency
  + lambda_reproj * C * L_reprojection
  + lambda_cycle * L_cycle
```

完成标准：

- 与直接重建相比，点云更稳定。
- 新视角破碎减少。
- cycle error 或 reprojection error 降低。

## 4. 结果表格

### 主表

| 方法 | 数据集 | Reproj ↓ | Align ↓ | Cycle ↓ | Multi-layer ↓ | LPIPS ↓ | FVD ↓ | 可探索性 ↑ |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| COLMAP + 3DGS |  |  |  |  |  |  |  |  |
| VGGT-Ω + 3DGS |  |  |  |  |  |  |  |  |
| Inconsistent Views |  |  |  |  |  |  |  |  |
| Ours |  |  |  |  |  |  |  |  |

### 消融表

| 方法 | Reproj ↓ | Align ↓ | Cycle ↓ | 观察 |
|---|---:|---:|---:|---|
| Full |  |  |  |  |
| w/o depth |  |  |  |  |
| w/o normal |  |  |  |  |
| w/o semantic |  |  |  |  |
| w/o cycle |  |  |  |  |
| w/o filtering |  |  |  |  |

## 5. 论文二图表清单

必须有：

- 生成视频直接重建失败图。
- 几何不一致检测热力图。
- 点云对齐前后对比。
- 新视角渲染对比。
- 闭环轨迹误差图。

## 6. 写作大纲

### 摘要

一句话问题：

生成视频模型能产生视觉上连续的视频，但其跨帧几何不一致会导致三维重建失败。

一句话方法：

本文提出一种几何一致性约束三维重建框架，通过不一致检测、深度/法线/重投影一致性和帧置信度加权提升生成视频重建稳定性。

一句话结果：

实验表明，方法降低跨视角误差和闭环误差，并生成更可探索的三维世界。

### 引言

结构：

1. 世界生成和视频生成的发展。
2. 视觉连续不等于三维一致。
3. 直接重建生成视频会失败。
4. 需要诊断和修复几何不一致。
5. 本文贡献。

### 方法

结构：

1. Overview。
2. Generated video geometry lifting。
3. Inconsistency detection。
4. Geometry-consistent reconstruction。
5. Confidence-aware optimization。

### 实验

结构：

1. Datasets and generated videos。
2. Baselines。
3. Metrics。
4. Main results。
5. Ablation。
6. Failure cases。

## 7. 失败时的调整策略

如果 WorldScore 获取或评测困难：

- 使用公开生成视频样例和 Replica/Habitat 合成视频。
- 自定义 reprojection/cycle/alignment 指标。

如果 World Reconstruction From Inconsistent Views 复现困难：

- 只使用其官方结果作为定性参考。
- 主 baseline 改为 COLMAP + 3DGS 和 VGGT-Ω/DUSt3R + 3DGS。

如果生成视频质量太差：

- 先做诊断型论文。
- 题目改为“生成视频三维一致性评估与重建分析”。

## 8. 与论文一的关系

论文二可以复用论文一的：

- confidence-aware loss。
- depth/normal consistency。
- geometric pruning。
- 可视化和评测代码。

区别在于：

- 论文一处理真实采集中的噪声。
- 论文二处理生成视频中的跨帧几何漂移。
