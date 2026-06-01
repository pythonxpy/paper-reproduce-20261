# 论文一执行清单：UP-Gaussian

题目：

**基于不确定性几何先验的大场景 Gaussian 表面重建**

英文可用题目：

**UP-Gaussian: Uncertainty-aware Prior Guided Gaussian Surface Reconstruction**

## 1. 论文一目标

证明：在真实视频或真实采集场景中，引入置信度感知几何先验后，Gaussian 表示不仅渲染更好，而且几何更准确。

## 2. 最小可行实验

### 2.1 数据集

第一优先级：

- DTU：用于几何指标。
- Tanks and Temples：用于真实采集鲁棒性。

第二优先级：

- ScanNet 或 ScanNet++：用于室内真实视频。
- MatrixCity 或 KITTI-360：用于大场景扩展。

### 2.2 Baseline

必须对比：

- 3DGS
- 2DGS
- CityGaussianV2 或 CityGaussian
- SuGaR 或 GOF

可选对比：

- VastGaussian
- HierarchicalGS
- Mip-Splatting
- Scaffold-GS

### 2.3 方法版本

| 版本 | 名称 | 作用 |
|---|---|---|
| V0 | Baseline | 原始 3DGS/2DGS |
| V1 | Prior Init | 加几何先验初始化 |
| V2 | Prior Loss | 加深度/法线几何损失 |
| V3 | Confidence Loss | 加置信度权重 |
| V4 | Geometric Pruning | 加几何裁剪 |
| V5 | Full Model | 完整方法 |

## 3. 实验步骤

### Step 1：跑通 baseline

输入：

- COLMAP 格式相机。
- 图像序列。

输出：

- 训练日志。
- 渲染图。
- PSNR/SSIM/LPIPS。
- point cloud 或 mesh。

完成标准：

- 至少一个场景能完整训练和渲染。
- 结果可重复。
- 保存配置文件。

### Step 2：加入几何先验

可选先验：

- 单目深度。
- 单目法线。
- VGGT-Ω/DUSt3R/MASt3R 点云或相机。

建议优先级：

1. 深度先验。
2. 法线先验。
3. VGGT-Ω/DUSt3R 点云初始化。

完成标准：

- 每帧都有深度或法线预测结果。
- 先验能投影到训练相机。
- 能可视化先验质量。

### Step 3：实现置信度

置信度来源可以从简单到复杂：

- 深度梯度过大处降低置信度。
- 多视图重投影误差高处降低置信度。
- 深度和法线不一致处降低置信度。
- 多模型预测不一致处降低置信度。

第一版建议：

```text
confidence = exp(-reprojection_error) * valid_mask
```

如果没有重投影误差，先使用：

```text
confidence = valid_depth_mask * non_sky_mask * non_dynamic_mask
```

完成标准：

- 能输出 confidence map。
- 能可视化高置信和低置信区域。
- 低置信区域不会主导几何损失。

### Step 4：加入几何损失

建议损失：

```text
L = L_rgb + lambda_ssim * L_ssim
  + lambda_depth * C * L_depth
  + lambda_normal * C * L_normal
  + lambda_reg * L_gaussian_reg
```

注意：

- 深度损失只在有效深度区域计算。
- 法线损失只在非边界和高置信区域计算。
- 几何损失权重从小到大 warm up。

完成标准：

- 加损失后训练不崩。
- 渲染质量不明显下降。
- 几何指标有提升趋势。

### Step 5：几何 pruning/densification

第一版先做 pruning，后做 densification。

裁剪对象：

- 低 opacity Gaussian。
- 重投影误差长期过高的 Gaussian。
- 尺度异常大的 Gaussian。
- 与深度先验偏差过大的漂浮 Gaussian。

增密对象：

- 高 RGB error 且高 depth/normal error 区域。
- 深度边界。
- 法线突变区域。

完成标准：

- Gaussian 数量变化合理。
- 漂浮点减少。
- Chamfer/F1 变好或可视化明显更干净。

## 4. 结果表格

### 主表

| 方法 | 数据集 | PSNR ↑ | SSIM ↑ | LPIPS ↓ | Chamfer ↓ | F1 ↑ | Normal ↑ |
|---|---|---:|---:|---:|---:|---:|---:|
| 3DGS |  |  |  |  |  |  |  |
| 2DGS |  |  |  |  |  |  |  |
| CityGaussianV2 |  |  |  |  |  |  |  |
| Ours |  |  |  |  |  |  |  |

### 消融表

| 方法 | PSNR ↑ | Chamfer ↓ | F1 ↑ | 观察 |
|---|---:|---:|---:|---|
| Full |  |  |  |  |
| w/o prior init |  |  |  |  |
| w/o confidence |  |  |  |  |
| w/o depth loss |  |  |  |  |
| w/o normal loss |  |  |  |  |
| w/o pruning |  |  |  |  |

## 5. 论文一图表清单

必须有：

- 方法框架图。
- Confidence map 可视化。
- 深度/法线先验可视化。
- baseline 与 ours 的 mesh/point cloud 对比。
- 稀疏视角结果对比。
- 消融可视化。

## 6. 写作大纲

### 摘要

一句话问题：

3D Gaussian Splatting 渲染效果好，但真实几何重建仍存在漂浮点、厚壳和表面不准确问题。

一句话方法：

本文提出一种不确定性感知的几何先验引导方法，自适应融合深度、法线和多视图一致性约束。

一句话结果：

实验表明，方法在多个数据集上提升 Chamfer、F1 和 normal consistency，同时保持较高渲染质量。

### 引言

结构：

1. 三维重建的重要性。
2. 3DGS 的优势。
3. 现有方法的几何问题。
4. 几何先验有帮助但不可靠。
5. 本文提出置信度感知方法。
6. 总结贡献。

### 方法

结构：

1. Overview。
2. Geometry prior estimation。
3. Confidence-aware geometric supervision。
4. Geometry-driven pruning and densification。
5. Training objective。

### 实验

结构：

1. Datasets and metrics。
2. Implementation details。
3. Main comparison。
4. Ablation study。
5. Robustness analysis。
6. Limitations。

## 7. 失败时的调整策略

如果 PSNR 降低但几何变好：

- 论文重点改为几何精度，而不是渲染质量。
- 强调适用于测量、建模、数字孪生场景。

如果几何指标提升不明显：

- 先只做 DTU。
- 简化大场景目标。
- 聚焦 confidence 比 direct prior 更稳定。

如果 baseline 太难复现：

- 使用 3DGS、2DGS、SuGaR 作为主要 baseline。
- CityGaussianV2 只做大场景定性或引用结果。
