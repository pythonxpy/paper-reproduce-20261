# CityGaussian-UAV 项目导师汇报梳理

整理日期：2026-06-28  
项目题目建议：基于 CityGaussian 重建城市街区的交互式风感知无人机低空飞行仿真与路径规划方法

## 1. 一句话说明这个项目

本项目把 CityGaussian 重建得到的真实感城市街区，从“只能用于渲染观看的 3DGS 场景”进一步转换为“无人机可碰撞检测、可路径规划、可交互飞行的低空仿真环境”，并在其中实现代理风场、风感知 3D A* 路径规划和自动航点跟踪。

更通俗地讲：我们不是只做一个好看的城市重建，而是让无人机真的能在重建出的楼宇之间低空飞行、规划路径、判断碰撞，并记录轨迹。

## 2. 为什么这个方向有意义

传统无人机城市低空路径规划常用三类环境：

1. 规则建筑盒子或 OSM 轮廓拉伸模型；
2. 手工建模的粗糙三维城市模型；
3. CFD 或仿真软件中的理想化计算域。

这些环境几何和视觉真实感有限，很难表现真实城市街区中楼体边缘、道路纹理、复杂遮挡和低空街谷结构。

CityGaussian 的优势是可以从图像数据重建出真实感城市 3D Gaussian 场景。但 CityGaussian 原本是渲染表示，不是导航地图。直接把 Gaussian 点云当障碍物会遇到严重问题：浮动噪声、半透明点、立面边缘和道路噪声都会被误判成硬障碍，导致无人机飞不进街区。

因此，本项目的核心价值是：把 CityGaussian 从视觉重建结果，进一步加工成面向 UAV 低空导航的空间表示。

## 3. 当前系统总体流程

```text
MatrixCity / CityGaussian block 数据
        ↓
CityGaussian 训练与 block_1 / block_2 / block_3 重建
        ↓
R 组区域自适应 Gaussian 结果
        ↓
block_1 + block_2 + block_3 拼接
        ↓
Navigation Layer 构建
  - Gaussian filtering
  - occupancy grid
  - free space
  - clearance field
  - soft risk map
        ↓
代理风场构建
  - 高度风廓线
  - 街谷加速
  - 背风尾流衰减
        ↓
3D A* / wind-aware A* / risk-aware A*
        ↓
CityGaussian viewer 中的 UAV 手动飞行、自动规划、自动跟踪
```

## 4. 当前已经完成的核心工作

### 4.1 CityGaussian 城市街区重建与拼接

已经完成 MatrixCity small city aerial train 中多个 block 的 CityGaussian 重建实验，并构建了 `block_1 + block_2 + block_3` 的联合 viewer。

当前 R 组结果：

| Block | R 组状态 | 说明 |
|---|---|---|
| block_1 | 已完成 | 参与联合 viewer |
| block_2 | 已完成 | 已做原始 / E / R 对比 |
| block_3 | 已完成 | 参与联合 viewer |
| block_1+2+3 | 已完成 | 形成联合城市街区仿真环境 |

R 组的作用不是单纯追求最高 PSNR，而是兼顾视觉质量和导航可用性。此前发现 E 组对楼顶和边界噪声有改善，但地面道路细节变差；R 组的思路是做区域自适应处理，使道路区域和建筑区域分别保留更适合导航和视觉展示的结果。

### 4.2 Navigation Layer：从渲染表示到导航表示

这是项目最重要的技术环节。

CityGaussian 的 3DGS 是 rendering-oriented representation，不是 navigation-oriented map。我们在其后加入一层 Navigation Layer：

- 从 Gaussian 中读取中心坐标、opacity、scale 等信息；
- 过滤低置信度 Gaussian 和漂浮噪声；
- 将点投影到 3D voxel；
- 构建 hard occupancy；
- 构建 free space；
- 构建 clearance field；
- 构建 soft risk map；
- 为路径规划提供碰撞、安全裕度和风险代价。

这个 Navigation Layer 解决的问题是：无人机不能直接在 3DGS 中飞，需要一个明确的 free / occupied / risk / clearance 表示。

### 4.3 UAV 交互式 viewer

当前 viewer 已经支持：

- CityGaussian 城市街区查看；
- UAV 第一视角控制；
- `W/S/A/D/Q/E` 手动移动；
- yaw / pitch 调整；
- occupancy 碰撞检测；
- 轨迹 CSV 保存；
- `block_1+2+3` 联合场景飞行；
- 路径规划控制面板；
- 一键重置。

当前可用 viewer：

| Viewer | 本地地址 | 用途 |
|---|---|---|
| R 组 block_1+2+3 普通 viewer | `http://127.0.0.1:8091/` | 展示联合城市街区和手动 UAV 控制 |
| R 组 block_1+2+3 路径规划 viewer | `http://127.0.0.1:8093/` | 展示风感知 A*、自动飞行、重置 |

### 4.4 自主路径规划与自动飞行

当前路径规划 viewer 支持三种模式：

| 模式 | 含义 |
|---|---|
| No wind A* | 只考虑 occupancy 碰撞和几何路径 |
| Wind-aware A* | 在 A* 代价中加入风场影响 |
| Wind + risk/clearance A* | 同时考虑风场、风险区域和障碍物净空 |

控制面板支持：

- 选择目标点；
- 自定义目标坐标；
- 设置风速；
- 设置风向；
- 点击 `Plan A to B` 规划路径；
- 点击 `Execute` 自动跟踪路径；
- 点击 `Pause / manual takeover` 人工接管；
- 点击 `Reset flight / clear plan` 一键清空路径并从新目标选择开始。

一键重置已完成：

- 暂停自动飞行；
- 清空当前规划路径；
- 清掉 autopilot；
- 隐藏旧路径点和目标点；
- UAV 回到初始低空街道起点；
- 清空轨迹历史；
- 重新选择目标后可再次规划。

## 5. 已有实验与关键结论

### 5.1 Occupancy 参数消融

实验关注 opacity threshold 和 dilation radius 对可飞空间的影响。

主要结论：

- UAV 飞不进楼间街道，最直接原因通常不是 A* 错，而是 occupancy / collision layer 太保守；
- safety dilation 对低空街道连通性影响最大；
- dilation 过大会把楼体边界向外扩张，窄街直接被封死；
- opacity threshold 有影响，但不如安全膨胀半径敏感；
- 因此论文中应强调：3DGS 到 UAV map 的转换必须是 navigation-aware，而不能简单 voxelize。

可展示文件：

- `citygaussian_uav_outputs/occupancy_ablation_v1/free_ratio_3d.png`
- `citygaussian_uav_outputs/occupancy_ablation_v1/z0.41_free_ratio.png`
- `citygaussian_uav_outputs/occupancy_ablation_v1/z0.56_largest_ratio.png`

### 5.2 SplatNav-inspired cleaning / Navigation Layer

借鉴 SplatNav 的思想，我们不是直接把所有 Gaussian 当障碍，而是做 confidence filtering、局部支持过滤、连通域清理，并输出 soft risk 与 clearance。

主要结论：

- 原始渲染用 3DGS 和 UAV 导航地图之间存在表示鸿沟；
- Gaussian floaters 和半透明噪声会造成虚假障碍；
- cleaned hard occupancy 能减少误占据；
- soft risk / clearance 让路径规划从“粗暴膨胀障碍物”转向“代价约束”，更适合窄街低空飞行。

可展示文件：

- `citygaussian_uav_outputs/nav_layer_eval_v2/navigation_layer_comparison.png`
- `citygaussian_uav_outputs/nav_layer_eval_v2/navigation_layer_summary.csv`
- `citygaussian_uav_outputs/splatnav_cleaning_ablation/cleaning_ablation_summary.csv`

### 5.3 多风向 / 多风速统计实验

当前已经做了代理风场下的多风向、多风速实验。

实验设置：

- 固定低空高度；
- 多个风向；
- 多个 base speed；
- 比较 baseline A* 与 wind-aware A*。

主要结论：

- 风感知路径规划不是单纯追求最短路径；
- 在高横风风险场景中，wind-aware A* 会选择更长路径来降低横风暴露；
- 高横风场景中横风降低效果更明显；
- 路径长度和飞行时间会增加，这是安全性与效率之间的权衡；
- 不应宣称所有风况下都降低横风，而应表述为：在高横风风险场景中更有效。

可展示文件：

- `citygaussian_uav_outputs/multi_wind_2d_cross_priority_v1/crosswind_reduction_by_wind.png`
- `citygaussian_uav_outputs/multi_wind_2d_cross_priority_v1/multi_wind_stats.csv`

### 5.4 低空楼间飞行视频

已经生成 15 秒左右的低空楼间飞行展示视频。

可展示文件：

- `citygaussian_uav_outputs/showcase_low_altitude_v2/low_altitude_between_buildings_15s.mp4`
- `citygaussian_uav_outputs/showcase_low_altitude_v2/0000.png`
- `citygaussian_uav_outputs/showcase_low_altitude_v2/0035.png`
- `citygaussian_uav_outputs/showcase_low_altitude_v2/0075.png`
- `citygaussian_uav_outputs/showcase_low_altitude_v2/0115.png`
- `citygaussian_uav_outputs/showcase_low_altitude_v2/0149.png`

这个视频适合在导师汇报时作为“项目已经能跑起来”的直观证据。

## 6. 当前论文贡献点建议

### 贡献 1：CityGaussian 城市街区用于 UAV 低空仿真

把真实感 3D Gaussian 城市重建结果用于低空 UAV 交互飞行和路径规划，而不是只用于视觉渲染。

建议表述：

> We introduce a CityGaussian-based urban block representation for low-altitude UAV flight simulation, enabling visually realistic and spatially complex navigation experiments in reconstructed city environments.

### 贡献 2：面向导航的 Gaussian-to-Navigation-Layer 转换

提出从渲染用 Gaussian 场景到导航用 occupancy / risk / clearance 表示的转换流程，缓解 floaters 和误占据问题。

建议表述：

> We construct a navigation-oriented layer from rendering-oriented Gaussian scenes, including cleaned occupancy, soft risk, and clearance fields for UAV collision checking and path planning.

### 贡献 3：代理风场与风感知 3D A*

构建轻量级代理风场，并将风场代价、横风风险、净空风险引入 A* 路径规划。

建议表述：

> We integrate an empirical proxy wind field with 3D A* planning, allowing the planner to balance path length, crosswind exposure, and obstacle clearance.

### 贡献 4：交互式 UAV viewer 与自动飞行闭环

实现可操作的 CityGaussian-UAV viewer，包括手动飞行、碰撞检测、路径规划、自动跟踪、人工接管和轨迹保存。

建议表述：

> We develop an interactive UAV simulation prototype that supports manual control, wind-aware planning, autonomous waypoint tracking, collision checking, and trajectory logging in a reconstructed Gaussian city scene.

## 7. 向导师汇报时的推荐讲法

### 7.1 3 分钟版本

1. 我们原来的 CFD-A* 路线比较依赖 Fluent 和粗糙城市模型，现在调整为 CityGaussian 重建城市街区中的低空 UAV 风感知仿真与路径规划。
2. CityGaussian 负责提供更真实的城市几何和视觉环境，但它不能直接用于导航，因为 3DGS 是渲染表示，会有 floaters 和误占据。
3. 我们增加了 Navigation Layer，把 Gaussian 转成 occupancy、free space、risk 和 clearance。
4. 在此基础上实现了 UAV viewer、手动飞行、碰撞检测、风感知 A*、自动飞行和轨迹记录。
5. 当前已经完成 block_1+2+3 联合场景、R 组重建结果、路径规划 viewer 和多风向实验。
6. 下一步是补充系统性对比实验和论文写作。

### 7.2 10 分钟版本

建议结构：

1. 研究背景：城市低空 UAV 需要真实仿真环境；
2. 问题：传统城市模型太粗，CityGaussian 虽真实但不是导航地图；
3. 核心方法：CityGaussian + Navigation Layer + proxy wind field + wind-aware A*；
4. 实验平台：block_1+2+3 R 组联合 viewer；
5. 实验结果：occupancy 消融、navigation layer 对比、多风向风感知实验、低空飞行视频；
6. 当前创新点；
7. 不足与下一步。

## 8. 现场演示顺序

建议先打开普通 R 组 viewer，再打开路径规划 viewer。

### 8.1 展示城市街区

打开：

```text
http://127.0.0.1:8091/
```

讲法：

- 这是 R 组 block_1+2+3 拼接后的 CityGaussian 城市街区；
- 场景来自 MatrixCity small city aerial train；
- 不再是规则建筑盒子，而是真实感 3D Gaussian 城市环境。

### 8.2 展示路径规划与飞控

打开：

```text
http://127.0.0.1:8093/
```

演示步骤：

1. 点 `Reset flight / clear plan`；
2. 选 `Goal preset = Block 3 street`；
3. 选 `Planning mode = Wind + risk/clearance A*`；
4. 点 `Plan A to B`；
5. 看路径和指标；
6. 点 `Execute`；
7. 点 `Pause / manual takeover`；
8. 用 `W/S/A/D/Q/E` 简单手动接管；
9. 点 `Save Trajectory`。

### 8.3 展示视频

展示：

```text
citygaussian_uav_outputs/showcase_low_altitude_v2/low_altitude_between_buildings_15s.mp4
```

讲法：

- 这不是楼顶上空飞行，也不是街区外围飞行；
- 是在楼宇之间的街道低空区域飞行；
- 可以作为论文补充视频和答辩展示材料。

## 9. 导师可能会问的问题与回答

### Q1：你这个风场是真实 CFD 吗？

不是。当前是 proxy wind field，即代理风场。它包含高度风廓线、街谷加速、背风尾流衰减等经验规则。本文目前定位不是替代 CFD，而是构建一个轻量、可复现、能与 CityGaussian 快速结合的风感知路径规划验证框架。

更稳妥回答：

> 目前风场是经验代理模型，主要用于验证风感知路径规划机制。后续可以接入 CFD 或实测风场作为更高精度输入，但本文重点在 CityGaussian 场景到 UAV 可导航仿真环境的转换和路径规划闭环。

### Q2：CityGaussian 和路径规划之间的创新在哪里？

创新不在于单独提出一个新的 A*，而在于把渲染用 3DGS 城市场景转换为导航可用地图，并在真实感城市街区中实现 UAV 交互飞行和风感知规划。

### Q3：为什么不直接把 Gaussian 点当障碍？

因为 3DGS 中存在 floaters、半透明点、边缘噪声和重建伪影。直接 voxelize 会把街道错误占据，导致无人机飞不进楼间低空区域。所以必须构建 Navigation Layer。

### Q4：R 组相对于原始和 E 组的意义是什么？

E 组深度初始化对楼顶和边界噪声有改善，但地面道路细节可能变差；原始组道路细节好但噪声和边界问题明显。R 组强调区域自适应：不同区域采用更适合导航和视觉质量的处理策略。

### Q5：论文应该投哪个方向？

建议偏计算机视觉 + 机器人仿真 / 智能交通 / UAV 路径规划交叉方向。不要强调真实 CFD，而强调：

- 3DGS-based urban simulation；
- navigation-oriented Gaussian scene processing；
- wind-aware UAV path planning；
- interactive UAV simulation in reconstructed urban scenes。

## 10. 目前还需要补强的部分

1. 更系统的 block_1+2+3 路径规划统计；
2. 原始 / E / R 在导航指标上的定量比较；
3. 多起点、多终点、多风向、多风速实验；
4. viewer 自动规划路径截图；
5. 论文方法图和实验框架图；
6. 最终论文中对 proxy wind field 的边界说明。

## 11. 论文结构建议

1. Introduction
   - 城市低空 UAV 仿真需求；
   - 传统模型不足；
   - 3DGS 城市重建的机会；
   - 3DGS 不能直接导航的问题；
   - 本文贡献。

2. Related Work
   - UAV path planning；
   - 3D Gaussian Splatting / CityGaussian；
   - 3DGS navigation / SplatNav；
   - wind-aware planning。

3. Method
   - CityGaussian urban block reconstruction；
   - Navigation Layer construction；
   - proxy wind field；
   - wind-aware / risk-aware 3D A*；
   - interactive UAV control and autopilot。

4. Experiments
   - scene setup；
   - navigation layer ablation；
   - original / E / R comparison；
   - wind-aware planning comparison；
   - interactive viewer demonstration。

5. Discussion
   - 3DGS rendering representation vs navigation representation；
   - proxy wind field limitation；
   - real UAV deployment gap；
   - future CFD / real wind extension。

6. Conclusion

## 12. 下午汇报时的重点结论

可以最后用三句话收束：

1. CityGaussian 可以把城市街区从粗糙几何模型升级为真实感低空 UAV 仿真环境。
2. 3DGS 不能直接用于 UAV 导航，必须经过 navigation-oriented occupancy / risk / clearance 转换。
3. 在该导航层上，代理风场和风感知 A* 可以形成完整的低空 UAV 路径规划与交互飞行闭环。

