# Cycling Race Analysis

[English Version](./README.md) | [中文版本](./README_zh.md)

A data analysis project for professional men's road cycling races (2009–2019). This project downloads, cleans, transforms, and analyzes race results from the UCI (Union Cycliste Internationale) official website to classify cyclists by their performance patterns across different terrain profiles.

## Overview

The project collects race data from 12 major professional cycling events — including the three Grand Tours (Tour de France, Giro d'Italia, Vuelta a España), other multi-stage races (Paris-Nice, Tirreno-Adriatico, Critérium du Dauphiné, Tour de Suisse), and five Monuments/Classics (Milano-Sanremo, Ronde van Vlaanderen, Paris-Roubaix, Liège-Bastogne-Liège, Il Lombardia). However, **only the 7 multi-stage races were included into analysis**, excluding the five single-stage Monuments/Classics races.

The core analytical goal is to **cluster cyclists** based on their stage-level performance across **Plain**, **Medium Mountain**, and **High Mountain** terrain, using both ranking and speed-based metrics.

## Data Sources

| Source | Usage |
|--------|-------|
| [UCI DataRide](https://dataride.uci.ch) | Primary race result downloads (`.xlsx`) |
| [ProCyclingStats](https://www.procyclingstats.com) | Stage parcours (route difficulty) scores |
| [La FlammeRouge](https://www.la-flamme-rouge.eu) | Stage meta-data: profiles, lengths, departure/arrival |
| Race official websites & WebArchive | Supplementary data verification |
| Wikipedia, Steephill.tv, YouTube | Profile information for specific races/years |

All meta-data has been cross-validated against multiple sources, with official sources weighted at 2 votes in case of discrepancies.

## Project Structure

```
├── DataAcquire/           # Data downloading modules
│   ├── download.py        # UCI DataRide crawler & ProCyclingStats parser
│   ├── path_gen.py        # File path generation from race meta-data
│   └── global_vars.py     # Path configuration
│
├── DataProcess/           # Data processing & analysis pipeline
│   ├── main.py            # Pipeline entry points
│   ├── check_raw.py       # Raw data quality audit
│   ├── convert_format.py  # .xlsx → .csv conversion
│   ├── cyclists_list.py   # Cyclist registry management
│   ├── races_list.py      # Races meta-data management
│   ├── gen_var.py         # Data tidying, feature extraction & variable generation
│   ├── merge_records.py   # Record merging & meta-data generation
│   ├── statistics.py      # OLS regression analysis
│   ├── plot.py            # Matplotlib visualizations
│   └── log.py             # JSON-based progress logging
│
├── MetaData/              # Reference data
│   ├── races_list.csv     # Master race list with profiles & lengths
│   ├── cyclists_list.csv  # Master cyclist registry
│   └── *.xlsx             # Per-race stage meta-data (from La FlammeRouge)
│
├── RCodes/                # Statistical analysis & visualization (R)
│   ├── main.R             # Clustering analysis workflow
│   ├── kmeans.R           # K-means & spherical k-means clustering
│   ├── plot.R             # ggplot2 figures
│   ├── statistical_tests.R # Normality tests, paired/unpaired difference tests
│   └── basics.R           # Shared R utilities
│
├── README.md              # This file (English)
└── README_zh.md           # Chinese version
```

## Data Processing Pipeline

The pipeline transforms raw UCI downloads into analysis-ready datasets through the following stages:

```
Raw (.xlsx)
    │
    ▼  convert_format.py
Converted_Raw (.csv)
    │
    ▼  gen_var.py (DataTidier)
Converted_Tidied
    │  • Fills missing demographic info (team, country)
    │  • Calculates normalized rank, total time (s), average speed (kph)
    │  • Computes speed relative to winner & median
    │  • Creates individual cyclist JSON records
    │
    ▼  gen_var.py (DataExtracter)
Converted_Extracted
    │  • Builds start lists from FC_GC (General Classification) files
    │  • Extracts rank/time-lag features per race/stage
    │
    ▼  gen_var.py (VarGenerator)
For_Clustering
    │  • Generates derived variables for clustering:
    │    - Stages finished count, GC rank
    │    - Mean/max/SD of stage ranking (all/IRR/TT)
    │    - Stage General Classification metrics
    │    - Normalized time lag statistics
    │
    ▼  merge_records.py
Merged / Cyclist_Meta
    │  • Season-split and pooled cyclist records
    │  • Meta-data by terrain profile & speed quantile
    │  • Stage Classification (SC) & General Classification (GC) summaries
```

### File Naming Convention

Files follow the format: `{Date}_{RaceCode}_{Stage}_{ResultType}_{StageType}`

Example: `20190701_TDF_S19_SC_IRR.csv`

| Field | Description | Example |
|-------|-------------|---------|
| Date | 8-digit date | `20190701` |
| RaceCode | 3-letter race abbreviation | `TDF`, `GDI`, `VUE` |
| Stage | Stage identifier | `S19` (Stage 19), `FC` (Final Classification) |
| Result Type | Type of result | `GC`, `SC`, `SGC` |
| Stage Type | Stage terrain | `IRR` (road race), `ITT`, `TTT` |

## R Analysis

### Clustering (`RCodes/kmeans.R`)

K-means and spherical k-means clustering of cyclists based on their stage performance:

1. **Hopkins statistic** — Tests whether the data has meaningful cluster structure
2. **Optimal k selection** — Elbow method, silhouette coefficient, and gap statistic
3. **Clustering** — Both Euclidean and spherical k-means, with optional vector normalization
4. **Validation** — Silhouette width analysis, visual inspection via PCA

The main analysis clusters Grand Tour riders by their average rank and speed across three terrain profiles (Plain / Medium Mountain / High Mountain), then evaluates whether these clusters generalize to other multi-stage races.

### Statistical Tests (`RCodes/statistical_tests.R`)

- Shapiro-Wilk normality tests
- Paired tests (t-test or Wilcoxon signed-rank) comparing performance across terrains within each cluster
- Unpaired tests (t-test or Mann-Whitney U) comparing clusters and race categories
- Effect size reporting (Cohen's d or correlation r)

### Visualization (`RCodes/plot.R`)

Bar plots and line charts with error bars, plus PCA visualizations, all rendered via ggplot2 with Chinese annotations.

## Requirements

### Python
- Python 3.x
- `requests`, `beautifulsoup4`, `brotli`, `chardet`
- `pandas`, `numpy`
- `xlrd`, `openpyxl`
- `statsmodels`
- `matplotlib`

### R
- R (≥ 3.6 recommended)
- `cluster`, `factoextra`, `skmeans`, `NbClust`
- `tidyverse`, `reshape2`, `Rmisc`, `stringr`
- `car`, `effectsize`, `rcompanion`

## Configuration

Before running the pipeline, configure the data root directory in `DataAcquire/global_vars.py` and `DataProcess/global_vars.py`:

```python
set_value('ROOT', r"D:\Your\Data\Directory")
```

The `ROOT` path expects the following subdirectory structure:
- `Raw/` — Downloaded UCI `.xlsx` files
- `Converted_Raw/` — Converted `.csv` files
- `Converted_Tidied/` — Tidied data
- `Converted_Extracted/` — Extracted features
- `Merged/` — Merged records
- `Cyclist_Meta/` — Cyclist meta-data
- `Cyclist_Records/` — Individual cyclist JSON records
- `For_Clustering/` — Clustering input data
- `MetaData/` — Reference data (races list, cyclists list)

## Known Issues

See [`问题记录.txt`](问题记录.txt) for a comprehensive log of data quality issues, including:

- Missing team information for specific riders/years
- Stages cancelled due to weather or tragedy
- Results voided by post-race doping disqualifications
- TTT data quality limitations from the UCI source

## Note

The structure and database access path has changed relative to when this project was done, hence the web-scraper codes don't work any more without adaptation.