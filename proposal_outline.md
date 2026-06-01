# 开题报告/论文提纲

## 题目建议

主推荐题目：

**基于不确定性几何先验的大场景 Gaussian 表面重建方法研究**

备选题目：

- 面向真实视频的几何一致性 Gaussian Splatting 三维重建
- 融合单目几何先验的高精度 Gaussian 表面重建
- 面向大场景的置信度感知 Gaussian 三维重建方法

如果选择生成视频方向：

**面向生成视频的几何一致性约束三维世界重建方法研究**

## 摘要初稿

三维重建是计算机视觉和三维内容生成中的重要任务。近年来，3D Gaussian Splatting 及其变体在新视角渲染中取得了显著进展，但其重建结果往往存在漂浮点、厚壳表面、远距离结构缺失和几何不稳定等问题。尤其在真实视频、大规模城市和街景场景中，稀疏视角、动态物体、低纹理区域和反光区域会进一步降低重建精度。为解决上述问题，本文拟研究一种基于不确定性几何先验的大场景 Gaussian 表面重建方法。该方法利用前馈三维基础模型、单目深度和单目法线估计提供几何先验，并通过置信度感知损失、自适应几何增密和动态区域过滤机制，提高 Gaussian 表示的表面准确性与稳定性。实验将在 DTU、Tanks and Temples、MatrixCity、KITTI-360 或 ScanNet++ 等数据集上进行，并与 3DGS、2DGS、CityGaussian、CityGaussianV2、SuGaR 等方法对比。预期结果表明，该方法不仅能保持较高渲染质量，还能在 Chamfer Distance、F1-score 和 normal consistency 等几何指标上取得提升。

## 1. 绪论

### 1.1 研究背景

- 三维重建在自动驾驶、数字孪生、AR/VR、机器人和三维内容生成中具有重要价值。
- NeRF 提升了隐式场景表示能力，但训练和渲染效率受限。
- 3DGS 显著提升实时渲染能力，但并不天然保证几何精度。
- 大场景和真实视频重建仍面临精度、效率和鲁棒性的共同挑战。

### 1.2 研究问题

- 如何减少 Gaussian 表示中的漂浮点、厚壳和表面错位？
- 如何可靠使用单目深度、法线和三维基础模型先验，而不被错误先验误导？
- 如何在大场景和动态干扰中保持几何重建稳定？
- 如何建立兼顾渲染质量和几何精度的实验评价体系？

### 1.3 研究意义

- 从只追求视觉渲染质量，转向同时关注真实三维几何。
- 为大规模城市建模、真实视频重建和可探索三维世界生成提供更可靠的表示。
- 为后续生成视频三维一致性研究奠定基础。

## 2. 相关工作

### 2.1 Neural Radiance Fields

介绍 NeRF、Mip-NeRF、Instant-NGP、Neuralangelo、NeuS 等方法，重点说明隐式方法在几何重建和效率上的特点。

### 2.2 Gaussian Splatting

介绍 3DGS、2DGS、Mip-Splatting、Scaffold-GS、SuGaR、GOF、GaussianSurfels 等方法，重点分析 Gaussian 表示的渲染优势和几何缺陷。

### 2.3 大场景重建

介绍 CityGaussian、CityGaussianV2、VastGaussian、HierarchicalGS、UrbanScene3D、MatrixCity 等工作，重点讨论分块训练、LOD、内存效率和城市级几何精度。

### 2.4 单目几何先验

介绍 Depth Anything、单目法线估计、VGGT、VGGT-Ω、DUSt3R、MASt3R 等方法，重点分析这些先验的优势和不确定性。

### 2.5 生成视频与三维世界重建

介绍 World Reconstruction From Inconsistent Views、WorldScore、ViewCrafter、SEVA、Gen3C、WorldExplorer、WonderWorld 等工作，作为扩展方向。

## 3. 方法

### 3.1 总体框架

输入为多视角图像或真实视频帧，输出为可渲染且几何准确的 Gaussian 表面表示。整体流程包括：

1. 几何先验估计。
2. Gaussian 初始化。
3. 置信度感知几何监督。
4. 几何误差驱动 densification 和 pruning。
5. 动态区域过滤。
6. 联合优化并导出 mesh 或点云用于评测。

### 3.2 几何先验估计

- 使用单目深度模型估计每帧深度。
- 使用单目法线模型估计表面法线。
- 使用 VGGT-Ω、DUSt3R 或 MASt3R 估计相机、点云和跨视图几何。
- 通过多模型一致性、局部平滑性和重投影误差估计先验置信度。

### 3.3 置信度感知损失

损失函数由以下部分组成：

- RGB 渲染损失。
- SSIM 损失。
- 深度一致性损失。
- 法线一致性损失。
- 多视图重投影一致性损失。
- Gaussian 形状正则项。

其中，深度、法线和重投影损失由置信度自适应加权。

### 3.4 几何误差驱动增密与裁剪

- 在高 photometric error 且高 geometric error 的区域优先增密。
- 在深度边界和法线突变区域增加局部 Gaussian 表达能力。
- 裁剪低不透明度、几何孤立、重投影不一致和尺度退化的 Gaussian。

### 3.5 动态区域过滤

- 使用语义分割或光流一致性识别动态区域。
- 对车辆、行人、天空、水面等区域降低几何损失权重。
- 保留必要的 photometric 监督，但避免其影响静态几何。

## 4. 实验设计

### 4.1 数据集

主实验数据集：

- DTU
- Tanks and Temples
- MatrixCity
- KITTI-360
- ScanNet 或 ScanNet++

扩展数据集：

- ETH3D
- Replica
- UrbanScene3D
- Waymo Open Dataset
- nuScenes

### 4.2 对比方法

- 3DGS
- 2DGS
- CityGaussian
- CityGaussianV2
- SuGaR
- GOF
- VastGaussian
- HierarchicalGS
- VGGT-Ω + 3DGS
- Depth Anything + 2DGS

### 4.3 评价指标

渲染指标：

- PSNR
- SSIM
- LPIPS

几何指标：

- Chamfer Distance
- Precision
- Recall
- F1-score
- Normal consistency

效率指标：

- 训练时间
- 显存占用
- Gaussian 数量
- FPS

### 4.4 消融实验

- 去掉几何先验初始化。
- 去掉置信度加权。
- 去掉深度损失。
- 去掉法线损失。
- 去掉几何 densification。
- 去掉动态 mask。

### 4.5 鲁棒性实验

- 稀疏视角输入。
- 低纹理区域。
- 远距离建筑。
- 动态物体干扰。
- 几何先验噪声扰动。

## 5. 预期创新点

1. 提出置信度感知的几何先验引导机制，解决单目先验不可靠时的错误传播问题。
2. 提出几何误差驱动的 Gaussian 增密与裁剪方法，提升表面完整性和边界精度。
3. 构建面向真实视频和大场景的几何精度评测流程，证明方法不只是提高视觉质量，也提高真实三维精度。

## 6. 计划进度

| 阶段 | 时间 | 工作内容 |
|---|---|---|
| 第一阶段 | 第 1-2 周 | 阅读和复现 3DGS、2DGS、CityGaussianV2 |
| 第二阶段 | 第 3-4 周 | 接入深度、法线和 VGGT-Ω 几何先验 |
| 第三阶段 | 第 5-6 周 | 实现置信度感知几何损失 |
| 第四阶段 | 第 7-8 周 | 实现几何 densification 和 pruning |
| 第五阶段 | 第 9-10 周 | 完成多数据集实验与消融 |
| 第六阶段 | 第 11-12 周 | 整理论文图表、撰写初稿 |

## 7. 可能困难与解决方案

- 几何先验不稳定：使用置信度权重和分阶段训练。
- 大场景训练成本高：先小场景验证，再分块扩展。
- 动态物体影响重建：加入语义或光流 mask。
- baseline 复现困难：优先选择开源成熟方法，并保留统一数据预处理流程。

## 8. 方向二作为扩展章节

如果时间允许，可以增加一节生成视频重建实验：

- 输入由 ViewCrafter、SEVA、Wan 或其他生成模型产生的视频。
- 使用 VGGT-Ω 或 DUSt3R 提取跨帧几何。
- 加入语义、深度、法线和循环一致性约束。
- 在 WorldScore、Replica、Habitat 或 Kubric 上评估生成视频的三维一致性。

这部分可以作为未来工作，也可以作为论文创新扩展。
