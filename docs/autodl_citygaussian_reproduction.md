# AutoDL 复现 CityGaussian / CityGaussianV2 指南

本文档用于在 AutoDL 上复现 CityGaussianV2 和 CityGaussian V1。建议先复现 V2，再复现 V1。

官方仓库：

- CityGaussian 系列官方仓库：https://github.com/Linketic/CityGaussian
- CityGaussianV2 项目页：https://dekuliutesla.github.io/CityGaussianV2/
- CityGaussian V1 项目页：https://dekuliutesla.github.io/citygs/

## 1. AutoDL 机器建议

最小 smoke test：

- GPU：RTX 4090 24GB
- 镜像：Ubuntu 20.04/22.04 + CUDA 11.8
- 磁盘：80GB 以上

正式训练：

- GPU：RTX 4090 24GB 可做小规模场景。
- GPU：A6000 48GB 或多卡更适合大场景。
- 磁盘：200GB 以上更稳。

## 2. 一键准备环境

在 AutoDL 终端中执行：

```bash
cd ~
git clone https://github.com/pythonxpy/paper-reproduce-20261.git
cd paper-reproduce-20261
bash scripts/autodl_setup_citygaussian.sh
```

默认行为：

- 克隆官方仓库到 `~/paper-reproduce-20261/third_party/CityGaussian`。
- 创建 conda 环境 `gspl`。
- 使用 Python 3.9。
- 按官方文档安装 PyTorch 2.0.1 CUDA 11.8 依赖。
- 安装 `requirements.txt` 和 `requirements/CityGS.txt`。
- 检查 PyTorch 和 CUDA。

如果你的 AutoDL 镜像不是 CUDA 11.8，请先执行：

```bash
nvcc --version
nvidia-smi
```

再决定是否修改脚本。当前脚本按官方文档默认使用 `requirements/pyt201_cu118.txt`。

## 3. CityGaussianV2 smoke test

环境安装完成后执行：

```bash
cd ~/paper-reproduce-20261
bash scripts/run_citygaussian_v2_smoke.sh
```

这个脚本不会训练大模型，只检查：

- 官方仓库主分支可用。
- `main.py` 存在。
- V2 配置文件存在。
- partition、parallel training、merge、mesh extraction 脚本存在。
- PyTorch 和 CUDA 可用。

通过 smoke test 后，再准备数据并训练。

## 4. CityGaussian V1 smoke test

执行：

```bash
cd ~/paper-reproduce-20261
bash scripts/run_citygaussian_v1_smoke.sh
```

说明：

- 官方 README 写明 V1 原始代码在 `V1-Original` 分支。
- 脚本会优先 checkout `V1-Original`。
- 如果远端分支名是 `V1-original`，脚本会自动 fallback。

## 5. 数据准备

官方文档推荐使用作者提供的 COLMAP 结果。目录结构大致如下：

```text
CityGaussian/
  data/
    colmap_results/
      matrix_city_aerial/
        train/sparse/0/
        test/sparse/0/
      matrix_city_street/
      building/
      residence/
      rubble/
      sciart/
```

对于自定义数据，官方期望结构为：

```text
data/your_scene/
  images/
  sparse/0/
    cameras.bin
    images.bin
    points3D.bin
```

如果要做几何评测，还需要：

```text
data/geometry_gt/your_scene/
  your_gt_pcd.ply
  your_gt_pcd.json
  transform.txt
```

建议第一轮不要直接下载超大数据。先选择官方提供的小场景或一个已经有 COLMAP 的场景，目标是先跑通训练链路。

## 6. V2 正式训练流程

进入官方仓库：

```bash
conda activate gspl
cd ~/paper-reproduce-20261/third_party/CityGaussian
git checkout main
```

官方 V2 流程分为四步：

```bash
python main.py fit \
  --config configs/citygsv2_lfls_sh2_trim.yaml \
  -n citygsv2_lfls_sh2_trim

python utils/partition_citygs.py \
  --config_path configs/citygsv2_lfls_sh2_trim.yaml \
  --force

python utils/train_citygs_partitions.py \
  -n citygsv2_lfls_sh2_trim

python utils/merge_citygs_ckpts.py \
  outputs/citygsv2_lfls_sh2_trim
```

渲染测试：

```bash
python main.py test \
  --config outputs/citygsv2_lfls_sh2_trim/config.yaml \
  --save_val \
  --test_speed
```

Mesh 提取和几何评测：

```bash
python utils/gs2d_mesh_extraction.py \
  outputs/citygsv2_lfls_sh2_trim \
  --voxel_size 0.02 \
  --sdf_trunc 0.08 \
  --depth_trunc 10.0

python tools/eval_tnt/run.py \
  --scene your_gt_pcd \
  --dataset-dir data/geometry_gt/your_scene \
  --transform-path data/geometry_gt/your_scene/transform.txt \
  --ply-path outputs/citygsv2_lfls_sh2_trim/fuse_post.ply
```

参数 `voxel_size`、`sdf_trunc`、`depth_trunc` 需要按场景尺度调整。

## 7. V1 复现流程

进入 V1 分支：

```bash
conda activate gspl
cd ~/paper-reproduce-20261/third_party/CityGaussian
git checkout V1-Original
```

然后查看该分支 README 和 scripts：

```bash
ls
find scripts -maxdepth 2 -type f | sort | head -n 50
```

V1 与 V2 的配置和命令可能不同，不建议直接套用 V2 命令。复现论文时，V1 主要作为 baseline，优先跑官方给出的脚本或 checkpoint。

## 8. 论文实验建议

先做 V2：

- 主分支维护更活跃。
- 有 2DGS-style mesh extraction。
- 更贴近我们的论文一“几何精度提升”目标。

再做 V1：

- 作为 ECCV 2024 CityGaussian baseline。
- 用于比较 V1 到 V2 的几何精度变化。

建议记录：

- commit id。
- conda env。
- CUDA/PyTorch 版本。
- 数据集和场景。
- config 文件。
- 输出目录。
- PSNR、SSIM、LPIPS。
- Precision、Recall、F1。
- GPU 显存和训练耗时。

## 9. 常见问题

### OOM

处理顺序：

1. 降低图片分辨率。
2. 减小 `max_cache_num`。
3. 提高 pruning 强度。
4. 先跑更小场景。

### COLMAP 太慢

优先使用官方提供的 COLMAP 结果。大场景从零跑 COLMAP 会非常慢，而且失败率更高。

### V1 分支安装失败

不要和 V2 强行共用所有命令。可以为 V1 单独创建环境：

```bash
conda create -y -n citygs_v1 python=3.9 pip
```

然后按 V1 分支 README 安装。

### GitHub 网络不稳定

AutoDL 有时访问 GitHub 或 Hugging Face 不稳定。可以：

- 多试几次。
- 使用 AutoDL 学术资源加速。
- 在本地下载后上传到 AutoDL 数据盘。
- 使用 Hugging Face 镜像或 `hf_transfer`。

## 10. 当前最小任务

第一天只完成这三件事：

```bash
bash scripts/autodl_setup_citygaussian.sh
bash scripts/run_citygaussian_v2_smoke.sh
bash scripts/run_citygaussian_v1_smoke.sh
```

如果这三步通过，再开始下载数据和训练。
