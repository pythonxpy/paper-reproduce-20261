# 实验矩阵

## 1. 方向一主实验：真实视频/真实采集三维重建

### 1.1 主实验设置

| 实验组 | 方法 | 几何先验 | 置信度加权 | 几何 densification | 动态 mask | 目标 |
|---|---|---|---|---|---|---|
| B1 | 3DGS | 无 | 无 | 原始策略 | 无 | 基础渲染 baseline |
| B2 | 2DGS | 无 | 无 | 原始策略 | 无 | 表面 Gaussian baseline |
| B3 | CityGaussianV2 | 无 | 无 | 大场景策略 | 可选 | 大场景 baseline |
| O1 | Ours-init | 有 | 无 | 原始策略 | 无 | 验证几何初始化作用 |
| O2 | Ours-conf | 有 | 有 | 原始策略 | 无 | 验证置信度监督作用 |
| O3 | Ours-densify | 有 | 有 | 有 | 无 | 验证几何增密作用 |
| O4 | Full model | 有 | 有 | 有 | 有 | 完整方法 |

### 1.2 数据集安排

| 阶段 | 数据集 | 场景类型 | 主要目的 | 是否需要真值几何 |
|---|---|---|---|---|
| 快速验证 | DTU | 物体/小场景 | 验证 Chamfer 和 F1 | 是 |
| 鲁棒性验证 | Tanks and Temples | 真实采集 | 验证真实图像稳定性 | 部分有 |
| 室内扩展 | ScanNet/ScanNet++ | 室内视频 | 验证动态和低纹理区域 | 是 |
| 大场景扩展 | MatrixCity | 城市合成 | 验证大场景几何完整性 | 是 |
| 街景扩展 | KITTI-360 | 车载街景 | 验证长轨迹和远距离结构 | 部分有 |

### 1.3 指标表格模板

| 方法 | 数据集 | PSNR ↑ | SSIM ↑ | LPIPS ↓ | Chamfer ↓ | Precision ↑ | Recall ↑ | F1 ↑ | Normal Consistency ↑ | Train Time ↓ | FPS ↑ |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 3DGS | DTU |  |  |  |  |  |  |  |  |  |  |
| 2DGS | DTU |  |  |  |  |  |  |  |  |  |  |
| CityGaussianV2 | DTU |  |  |  |  |  |  |  |  |  |  |
| Ours | DTU |  |  |  |  |  |  |  |  |  |  |

## 2. 方向一消融实验

### 2.1 模块消融

| 消融项 | 去掉的模块 | 预期现象 |
|---|---|---|
| w/o prior init | 几何先验初始化 | 收敛变慢，稀疏视角几何变差 |
| w/o confidence | 置信度加权 | 错误深度/法线先验导致局部几何下降 |
| w/o normal loss | 法线一致性 | 平面和边界表面更粗糙 |
| w/o depth loss | 深度一致性 | 厚壳和漂浮点增多 |
| w/o geometric densification | 几何误差驱动增密 | 边缘、薄结构和远距离结构不完整 |
| w/o dynamic mask | 动态区域过滤 | 车辆、行人等动态区域污染静态场景 |

### 2.2 鲁棒性实验

| 实验 | 设置 | 观察指标 |
|---|---|---|
| 稀疏视角 | 使用 25%、50%、75% 训练视角 | Chamfer、F1、LPIPS |
| 远距离结构 | 单独统计远距离建筑或背景区域 | Recall、F1 |
| 低纹理区域 | 墙面、地面、天空边缘 | Normal consistency |
| 动态干扰 | 保留/去除动态物体 mask | 几何噪声、漂浮点数量 |
| 先验噪声 | 人为扰动深度/法线 | 置信度机制稳定性 |

## 3. 方向二主实验：生成视频三维一致性

### 3.1 主实验设置

| 实验组 | 输入 | 几何提升 | 一致性约束 | 质量筛选 | 输出 |
|---|---|---|---|---|---|
| B1 | 生成视频 | COLMAP | 无 | 无 | 3DGS |
| B2 | 生成视频 | VGGT-Ω | 无 | 无 | 3DGS/2DGS |
| B3 | 生成视频 | World Reconstruction From Inconsistent Views | 非刚性对齐 | 无 | 3D world |
| O1 | 生成视频 | VGGT-Ω/DUSt3R | 深度+法线 | 无 | 3DGS/2DGS |
| O2 | 生成视频 | VGGT-Ω/DUSt3R | 深度+法线+语义 | 有 | 3DGS/2DGS |
| O3 | 生成视频 | VGGT-Ω/DUSt3R | 深度+法线+语义+循环 | 有 | 3DGS/2DGS |

### 3.2 数据集安排

| 数据集 | 类型 | 用途 |
|---|---|---|
| WorldScore | 生成世界评测 | 主评测数据 |
| Replica/Habitat | 合成室内 | 有真值几何，适合可控验证 |
| Kubric/BlenderProc | 合成视频 | 评估动态和遮挡 |
| MatrixCity | 合成城市 | 评估大场景闭环一致性 |
| RealEstate10K | 真实视频 | 验证真实视频泛化 |

### 3.3 指标表格模板

| 方法 | 数据集 | Reprojection Error ↓ | Cycle Error ↓ | Point Alignment Error ↓ | Multi-layer Ratio ↓ | PSNR ↑ | LPIPS ↓ | FVD ↓ | WorldScore ↑ |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| COLMAP + 3DGS | WorldScore |  |  |  |  |  |  |  |  |
| VGGT-Ω + 3DGS | WorldScore |  |  |  |  |  |  |  |  |
| Inconsistent Views | WorldScore |  |  |  |  |  |  |  |  |
| Ours | WorldScore |  |  |  |  |  |  |  |  |

## 4. 预期结果描述模板

方向一预期结果：

- 在 DTU 和 Tanks and Temples 上，完整方法应在 Chamfer、F1 和 normal consistency 上优于 3DGS、2DGS 和 CityGaussianV2。
- 在 MatrixCity 或 KITTI-360 上，完整方法应减少远距离结构缺失和漂浮点。
- 消融实验中，去掉置信度加权后，错误先验区域的几何质量应明显下降。

方向二预期结果：

- 相比直接使用 COLMAP + 3DGS，方法应降低生成视频的重投影误差和点云对齐误差。
- 相比只做非刚性对齐，加入语义、法线和循环约束后应减少过度形变。
- 在闭环视频中，cycle error 应明显降低，新视角渲染破碎程度减少。

## 5. 建议时间线

| 周期 | 任务 | 产出 |
|---|---|---|
| 第 1-2 周 | 复现 3DGS/2DGS 基线，跑通 DTU 或 Tanks and Temples | baseline 指标表 |
| 第 3-4 周 | 接入深度/法线/VGGT-Ω 先验 | 先验可视化和初始化实验 |
| 第 5-6 周 | 实现置信度加权几何损失 | 消融实验 O1/O2 |
| 第 7-8 周 | 实现几何 densification 和 pruning | 完整模型初版 |
| 第 9-10 周 | 扩展到 MatrixCity/KITTI-360/ScanNet++ | 大场景结果 |
| 第 11-12 周 | 整理消融、可视化和论文图表 | 开题/论文初稿 |
