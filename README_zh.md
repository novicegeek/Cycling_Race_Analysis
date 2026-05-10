# 自行车赛数据分析

[English Version](./README.md) | [中文版本](./README_zh.md)

面向职业公路自行车赛（2009–2019赛季）的数据分析项目。本项目从国际自行车联盟（UCI）官方网站下载比赛结果，经过清洗、转换和分析，根据不同地形特征对车手表现进行分类。

## 概述

本项目收集了12项主要职业公路自行车赛事的数据——包括三大环赛（环法、环意、环西）、多日赛（巴黎-尼斯、第勒尼安-亚得里亚海、多菲内、环瑞士）以及五大古典赛（米兰-圣雷莫、环弗兰德斯、巴黎-鲁贝、列日-巴斯通-列日、环伦巴第），但**最终分析只纳入7项多日赛**，未纳入五大单日古典赛。

核心分析目标是基于车手在**平地**、**中等山地**和**高山**三种地形下的赛段级表现（结合排名和速度指标），对车手进行聚类分析。

## 数据来源

| 来源 | 用途 |
|------|------|
| [UCI DataRide](https://dataride.uci.ch) | 主要比赛结果下载（`.xlsx`） |
| [ProCyclingStats](https://www.procyclingstats.com) | 赛段路线难度评分 |
| [La FlammeRouge](https://www.la-flamme-rouge.eu) | 赛段元数据：地形、里程、起终点 |
| 各赛事官方网站 & WebArchive | 数据补充验证 |
| Wikipedia、Steephill.tv、YouTube | 特定赛事/年份的地形信息 |

所有元数据均经过多源交叉验证，存在出入时官方源计2票、其他源各计1票，以最高票数为准。

## 项目结构

```
├── DataAcquire/           # 数据下载模块
│   ├── download.py        # UCI DataRide爬虫 & ProCyclingStats解析器
│   ├── path_gen.py        # 根据赛事元数据生成文件路径
│   └── global_vars.py     # 路径配置
│
├── DataProcess/           # 数据处理与分析管线
│   ├── main.py            # 管线入口
│   ├── check_raw.py       # 原始数据质量审计
│   ├── convert_format.py  # .xlsx → .csv 格式转换
│   ├── cyclists_list.py   # 车手注册表管理
│   ├── races_list.py      # 赛事元数据管理
│   ├── gen_var.py         # 数据整理、特征提取与变量生成
│   ├── merge_records.py   # 记录合并与元数据生成
│   ├── statistics.py      # OLS回归分析
│   ├── plot.py            # Matplotlib可视化
│   └── log.py             # 基于JSON的进度日志
│
├── MetaData/              # 参考数据
│   ├── races_list.csv     # 赛事主列表（含地形与里程）
│   ├── cyclists_list.csv  # 车手注册主表
│   └── *.xlsx             # 各赛事赛段元数据（来源：La FlammeRouge）
│
├── RCodes/                # 统计分析 & 可视化（R语言）
│   ├── main.R             # 聚类分析工作流
│   ├── kmeans.R           # K-means & 球形k-means聚类
│   ├── plot.R             # ggplot2图表
│   ├── statistical_tests.R # 正态性检验、配对/非配对差异检验
│   └── basics.R           # R共享工具函数
│
├── README.md              # 英文版说明
└── README_zh.md           # 本文件（中文版）
```

## 数据处理管线

原始UCI下载文件经过以下阶段转换为可供分析的数据集：

```
Raw (.xlsx)
    │
    ▼  convert_format.py
Converted_Raw (.csv)
    │
    ▼  gen_var.py (DataTidier)
Converted_Tidied
    │  • 填补缺失的人口学信息（车队、国家）
    │  • 计算标准化排名、总用时（秒）、平均速度（kph）
    │  • 计算相对于冠军和中位数的速度比
    │  • 为每位车手创建JSON记录文件
    │
    ▼  gen_var.py (DataExtracter)
Converted_Extracted
    │  • 从FC_GC（总成绩）文件构建出发名单
    │  • 提取每场比赛/赛段的排名与时间差特征
    │
    ▼  gen_var.py (VarGenerator)
For_Clustering
    │  • 生成用于聚类的衍生变量：
    │    - 完赛场次数、GC总排名
    │    - 赛段排名的均值/最优值/标准差（全部/IRR/TT）
    │    - 赛段总成绩（SGC）相关指标
    │    - 标准化时间差统计量
    │
    ▼  merge_records.py
Merged / Cyclist_Meta
    │  • 按赛季拆分和合并的车手记录
    │  • 按地形类型与速度分位数汇总的元数据
    │  • 赛段成绩（SC）与总成绩（GC）汇总
```

### 文件命名规则

文件格式：`{日期}_{赛事代码}_{赛段}_{结果类型}_{赛段类型}`

示例：`20190701_TDF_S19_SC_IRR.csv`

| 字段 | 说明 | 示例 |
|------|------|------|
| Date | 8位日期 | `20190701` |
| RaceCode | 3字母赛事缩写 | `TDF`, `GDI`, `VUE` |
| Stage | 赛段标识 | `S19`（第19赛段）、`FC`（总排名） |
| Result Type | 结果类型 | `GC`（总成绩）、`SC`（赛段成绩）、`SGC`（赛段总成绩） |
| Stage Type | 赛段类型 | `IRR`（公路赛）、`ITT`（个人计时赛）、`TTT`（团体计时赛） |

## R语言分析

### 聚类分析 (`RCodes/kmeans.R`)

基于车手赛段表现的K-means和球形K-means聚类：

1. **Hopkins统计量** — 检验数据是否具有有意义的聚类结构
2. **最优k值选择** — 肘部法则、轮廓系数和Gap统计量
3. **聚类** — 欧氏距离和余弦距离K-means，支持可选向量归一化
4. **验证** — 轮廓宽度分析、PCA可视化检查

主要分析对三大环赛车手按三种地形（平地/中等山地/高山）的平均排名和速度进行聚类，然后评估聚类结果是否能推广到其他多日赛。

### 统计检验 (`RCodes/statistical_tests.R`)

- Shapiro-Wilk正态性检验
- 配对检验（t检验或Wilcoxon符号秩检验）：比较同一聚类内不同地形的表现差异
- 非配对检验（t检验或Mann-Whitney U检验）：比较不同聚类和不同赛事类别
- 效应量报告（Cohen's d或相关系数r）

### 可视化 (`RCodes/plot.R`)

条形图和折线图（含误差线），以及PCA散点图，均通过ggplot2渲染，包含中文注释。

## 运行环境要求

### Python
- Python 3.x
- `requests`, `beautifulsoup4`, `brotli`, `chardet`
- `pandas`, `numpy`
- `xlrd`, `openpyxl`
- `statsmodels`
- `matplotlib`

### R
- R（建议 ≥ 3.6）
- `cluster`, `factoextra`, `skmeans`, `NbClust`
- `tidyverse`, `reshape2`, `Rmisc`, `stringr`
- `car`, `effectsize`, `rcompanion`

## 配置

运行前，需在 `DataAcquire/global_vars.py` 和 `DataProcess/global_vars.py` 中设置数据根目录：

```python
set_value('ROOT', r"D:\Your\Data\Directory")
```

`ROOT` 路径下需包含以下子目录：
- `Raw/` — 下载的UCI `.xlsx` 文件
- `Converted_Raw/` — 转换后的 `.csv` 文件
- `Converted_Tidied/` — 整理后的数据
- `Converted_Extracted/` — 提取的特征数据
- `Merged/` — 合并记录
- `Cyclist_Meta/` — 车手元数据
- `Cyclist_Records/` — 车手个人JSON记录
- `For_Clustering/` — 聚类输入数据
- `MetaData/` — 参考数据（赛事列表、车手列表）

## 已知问题

详见 [`问题记录.txt`](问题记录.txt)，涵盖以下数据质量问题：

- 特定车手/年份的车队信息缺失
- 因天气或悲剧事件取消的赛段
- 赛后兴奋剂违规导致成绩作废
- UCI源文件中TTT数据质量问题

## 说明

UCI官方网站的结构和数据库访问路径与本项目完成时相比已发生变化，故爬虫部分的代码需要改编才可继续使用。