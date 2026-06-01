# 两个可落地的三维重建研究方向

## 0. 总体定位

本工作的核心目标不是单纯提高新视角渲染质量，而是提高三维重建的真实几何精度。建议采用“一稳一新”的研究组合：

- 方向一：面向真实视频或真实采集数据的大场景高精度 Gaussian 表面重建。
- 方向二：面向生成视频的 3D 一致性修复与可重建世界生成。

其中，方向一更适合作为主论文方向；方向二更适合作为创新扩展、后续工作或高风险高收益方向。

## 1. 方向一：基于不确定性几何先验的大场景 Gaussian 表面重建

### 1.1 研究问题

现有 3D Gaussian Splatting 类方法在渲染质量上表现很好，但几何精度仍然不稳定。典型问题包括：

- 3DGS 容易产生漂浮点、厚壳表面和不贴合真实几何的透明结构。
- 2DGS 和 CityGaussianV2 通过 surfel 或分块策略提升了表面表达和大场景扩展性，但在稀疏视角、远距离建筑、街景边界和低纹理区域仍然容易出现表面模糊或结构缺失。
- 单目深度、单目法线和前馈三维基础模型能提供几何先验，但这些先验存在不确定性，直接监督会把错误传播到最终重建。
- 动态物体、阴影、反光和天空区域会破坏多视图一致性，使静态场景重建被污染。

### 1.2 核心假设

如果能够显式估计几何先验的不确定性，并让 Gaussian 表面优化过程根据置信度自适应使用深度、法线和重投影约束，就可以在不明显牺牲渲染质量的前提下提升真实几何精度。

### 1.3 方法设计

建议方法名：

**UP-Gaussian：Uncertainty-aware Prior Guided Gaussian Surface Reconstruction**

中文名称：

**基于不确定性几何先验的大场景 Gaussian 表面重建**

核心模块：

1. **几何先验初始化**
   - 使用 VGGT-Ω、DUSt3R、MASt3R、Depth Anything 或单目法线估计模型预测深度、法线、相机或稀疏/稠密点云。
   - 将可靠点云用于 Gaussian 初始化，减少随机初始化带来的收敛不稳定。

2. **置信度感知几何监督**
   - 为每个像素或局部区域估计几何置信度。
   - 高置信区域使用较强的深度损失、法线损失和多视图一致性损失。
   - 低置信区域降低几何监督权重，只保留轻量平滑或 photometric 监督。

3. **几何误差驱动的 densification**
   - 在深度不连续、法线变化大、重投影误差高的位置主动增密 Gaussian。
   - 对漂浮点、透明厚壳和长条退化 Gaussian 进行裁剪。
   - 将原本偏渲染误差驱动的增密机制，改为渲染误差与几何误差共同驱动。

4. **动态区域过滤**
   - 使用语义分割、光流一致性或帧间 mask 过滤车辆、行人、天空、水面等不可靠区域。
   - 对这些区域降低几何监督权重，避免污染静态三维结构。

5. **几何一致性优化目标**
   - 渲染损失：RGB reconstruction loss、SSIM loss。
   - 深度一致性：预测深度与渲染深度对齐。
   - 法线一致性：预测法线与 Gaussian 表面法线对齐。
   - 多视图一致性：同一点从不同视角投影后深度和颜色保持一致。
   - 正则项：抑制过度透明、过长尺度、漂浮点和厚壳结构。

### 1.4 推荐数据集

首选小规模验证：

- DTU：有较成熟几何评测，适合快速验证 Chamfer、F1 和 normal consistency。
- Tanks and Temples：真实采集场景，适合测试鲁棒性。

主实验数据集：

- MatrixCity：适合大规模城市级场景。
- KITTI-360：适合街景和车载视频。
- ScanNet++ 或 ScanNet：适合室内真实视频与复杂几何。

可扩展数据集：

- Mill 19、UrbanScene3D、GauU-Scene、Waymo Open Dataset、nuScenes、ETH3D、Replica。

### 1.5 对比方法

Gaussian 系列：

- 3DGS
- 2DGS
- CityGaussian
- CityGaussianV2
- VastGaussian
- HierarchicalGS
- Mip-Splatting
- Scaffold-GS

表面重建系列：

- SuGaR
- GOF
- GaussianSurfels
- TrimGS
- Neuralangelo
- NeuS

几何基础模型辅助：

- VGGT
- VGGT-Ω
- DUSt3R
- MASt3R
- Depth Anything 系列

### 1.6 评价指标

渲染质量：

- PSNR
- SSIM
- LPIPS

几何质量：

- Chamfer Distance
- Precision
- Recall
- F1-score
- Normal consistency
- Depth RMSE 或 AbsRel

效率：

- 训练时间
- 显存占用
- Gaussian 数量
- 模型大小
- FPS

鲁棒性：

- 稀疏视角下的几何退化程度
- 远距离建筑的完整性
- 低纹理区域的表面稳定性
- 动态物体干扰下的静态重建质量

### 1.7 预期贡献

- 提出一种置信度感知的几何先验使用方式，避免错误单目先验破坏重建。
- 提出几何误差驱动的 Gaussian 增密和裁剪策略，提高 mesh 与点云精度。
- 在真实视频和大场景数据上验证方法不仅提升 PSNR，也提升 Chamfer、F1 和 normal consistency。

### 1.8 主要风险与规避

- 风险：几何先验质量不稳定。
  - 规避：使用置信度加权，不把先验作为硬约束。

- 风险：多种损失导致训练不稳定。
  - 规避：采用分阶段训练，先 photometric 收敛，再逐步增加几何监督权重。

- 风险：大场景实验成本高。
  - 规避：先在 DTU/Tanks and Temples 上验证核心模块，再迁移到 MatrixCity/KITTI-360。

## 2. 方向二：面向生成视频的几何一致性约束三维重建

### 2.1 研究问题

视频生成模型可以生成视觉上连续的视频，但它们通常并不满足真实三维世界的一致性。主要问题包括：

- 同一物体在不同帧中形状、尺度、位置发生漂移。
- 生成视频的相机运动看似合理，但用几何模型估计出的相机和点云无法稳定对齐。
- 直接使用 COLMAP、3DGS 或 2DGS 对生成视频重建，容易出现多层墙面、错位结构、破碎表面和漂浮物。
- World Reconstruction From Inconsistent Views 使用非刚性对齐处理不一致视图，但仍可能出现过度形变、错误对应和局部细节损失。
- FVD、CLIP score 等传统生成指标无法直接说明视频是否能被重建成可探索的三维世界。

### 2.2 核心假设

如果把生成视频视为含有几何噪声和跨帧漂移的观测序列，并在重建过程中显式加入语义、法线、深度和循环一致性约束，就可以把视觉上合理但几何不稳定的视频转化为更稳定的 3D 世界表示。

### 2.3 方法设计

建议方法名：

**GC-WorldRecon：Geometry-Consistent World Reconstruction from Generated Videos**

中文名称：

**面向生成视频的几何一致性约束三维重建**

核心模块：

1. **生成视频几何提升**
   - 对每帧使用 VGGT-Ω、DUSt3R、MASt3R 或 Depth Anything-3 估计深度、相机、法线和点云。
   - 将生成视频转化为带有不确定性的多帧几何观测。

2. **不一致帧检测**
   - 计算相邻帧点云对齐误差、重投影误差和语义区域漂移。
   - 标记几何不可信帧或不可信区域。

3. **语义一致性约束**
   - 对同一语义物体或同一场景部件建立跨帧对应。
   - 要求墙面、地面、桌子、车辆等结构在多帧中保持尺度和位置稳定。

4. **法线/深度一致性约束**
   - 对平面结构引入法线稳定约束，避免墙面或地面被非刚性对齐过度弯曲。
   - 对可靠区域使用深度一致性损失，减少多层表面。

5. **循环一致性约束**
   - 当视频包含环绕、回看或闭环轨迹时，要求最后几帧重建结果与起始区域几何一致。
   - 使用闭环误差作为生成视频三维一致性的评价指标。

6. **质量筛选与重建优化**
   - 对不可信帧降低损失权重，必要时跳过。
   - 对局部几何错误区域，可使用相邻帧补全或扩散模型重新生成局部内容。
   - 最终用 3DGS/2DGS/Gaussian surfel 表示优化可探索三维世界。

### 2.4 推荐数据集

生成世界评测：

- WorldScore：适合评估可控性、视觉质量、动态一致性和世界生成能力。

生成视频来源：

- Wan
- ViewCrafter
- SEVA
- Gen3C
- Voyager
- Genie3
- HY-WorldPlay

可控合成验证：

- Replica
- Habitat
- Kubric
- BlenderProc
- MatrixCity

真实视频辅助：

- RealEstate10K
- ScanNet
- CO3D
- Tanks and Temples

### 2.5 对比方法

生成视频重建：

- World Reconstruction From Inconsistent Views
- COLMAP + 3DGS
- VGGT-Ω + 3DGS/2DGS
- Depth Anything + 2DGS

3D 世界生成：

- WorldExplorer
- Text2Room
- LucidDreamer
- WonderJourney
- WonderWorld

前馈几何：

- VGGT
- VGGT-Ω
- DUSt3R
- MASt3R

视频/世界生成模型：

- ViewCrafter
- SEVA
- Gen3C
- Voyager
- Wan
- Genie3

### 2.6 评价指标

生成世界质量：

- WorldScore controllability
- WorldScore quality
- WorldScore dynamics

三维一致性：

- Cross-view reprojection error
- Cycle trajectory error
- Point cloud alignment error
- Multi-layer surface ratio

渲染质量：

- PSNR
- SSIM
- LPIPS
- FID
- FVD

几何质量：

- Chamfer Distance
- F1-score
- Normal consistency

用户可探索性：

- 新视角渲染是否破碎
- 是否存在多层墙面
- 是否存在漂浮物
- 闭环视角是否能回到同一空间结构

### 2.7 预期贡献

- 提出生成视频三维一致性诊断指标，用于判断视频是否适合重建成 3D 世界。
- 提出语义、法线、深度和循环一致性联合约束，缓解生成视频帧间漂移。
- 在 WorldScore 和合成可控数据上验证生成视频到三维世界重建的质量提升。

### 2.8 主要风险与规避

- 风险：生成视频模型和数据获取成本较高。
  - 规避：优先使用公开生成结果、WorldScore 样例或开源视频生成模型。

- 风险：缺少真实几何 ground truth。
  - 规避：用 Replica、Habitat、Kubric、BlenderProc 生成带真值的可控数据。

- 风险：问题过新，baseline 复现难。
  - 规避：先建立 COLMAP + 3DGS、VGGT-Ω + 3DGS、World Reconstruction From Inconsistent Views 三条主 baseline。

## 3. 推荐落地路线

### 3.1 主论文路线

主方向建议选择方向一：

**基于不确定性几何先验的大场景 Gaussian 表面重建**

原因：

- 能直接对应“让重建精度更高”的目标。
- 可以用成熟数据集和指标证明贡献。
- 方法模块边界清晰，容易做消融实验。

### 3.2 备选创新路线

方向二适合作为：

- 第二阶段研究。
- 论文中的扩展实验。
- 未来工作章节。
- 如果导师希望选题更前沿，可以将其作为主线，但需要接受更高实验风险。

### 3.3 最小可行实验

第一阶段最小实验建议：

- 数据集：DTU + Tanks and Temples。
- Baseline：3DGS、2DGS、SuGaR、CityGaussianV2。
- 模块：先验初始化、置信度几何损失、几何 densification。
- 指标：PSNR、SSIM、LPIPS、Chamfer、F1、normal consistency。

第二阶段扩展实验建议：

- 数据集：MatrixCity + KITTI-360 或 ScanNet++。
- 加入动态 mask、分块训练和大场景效率对比。
- 与 CityGaussian、CityGaussianV2、VastGaussian、HierarchicalGS 对比。

第三阶段生成视频实验建议：

- 数据集：WorldScore + Replica/Habitat 合成视频。
- Baseline：World Reconstruction From Inconsistent Views、VGGT-Ω + 3DGS、COLMAP + 3DGS。
- 指标：cycle error、reprojection error、WorldScore、FVD、LPIPS。

## 4. 论文贡献表达模板

可以将论文贡献写成：

1. 提出一种不确定性感知的几何先验引导 Gaussian 表面重建方法，在真实视频和大场景中提升几何精度。
2. 设计几何误差驱动的 Gaussian 增密与裁剪策略，减少漂浮点、厚壳表面和远距离结构缺失。
3. 构建包含渲染质量、几何精度、效率和鲁棒性的完整实验评测，在多个公开数据集上优于现有方法。

如果选择方向二，可以将贡献写成：

1. 提出一种面向生成视频的三维一致性诊断与修复框架。
2. 引入语义、深度、法线和循环一致性约束，缓解生成视频跨帧几何漂移。
3. 在 WorldScore 和可控合成数据上验证方法能生成更稳定、可探索的三维世界。

## 5. 参考论文

- CityGaussian: Real-time High-quality Large-Scale Scene Rendering with Gaussians.
- CityGaussianV2: Efficient and Geometrically Accurate Reconstruction for Large-Scale Scenes.
- Monocular Normal Estimation via Shading Sequence Estimation.
- World Reconstruction From Inconsistent Views.
- WorldScore: A Unified Evaluation Benchmark for World Generation.
- VGGT-Ω: Visual Geometry Grounded Transformer for Large-Scale 3D Understanding and Reconstruction.
