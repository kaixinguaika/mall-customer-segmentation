# DESIGN.md — Mall Customer Segmentation（课程答辩，4–5 分钟）

## 0. 需求对齐

| 维度 | 结论 |
|---|---|
| 主题 | 商场客户细分：K-Means 分群 + 有监督分类复现分群 |
| 目标 | 课程项目答辩（Machine Learning, Fall 2026），4–5 分钟，1 分钟 Q&A |
| 受众 | 授课教师 + 同学，具备基础 ML 知识，不需要解释 K-Means 是什么 |
| 页数 | 11 页（封面 1 + 内容 9 + 参考文献 1） |
| 语言 | 幻灯片英文（课程为全英文大纲），演讲者不提词，页面上不放中文 |
| 调性 | 学术、证据驱动、克制；不卖点、不堆砌形容词 |

## 1. 画布与安全区

- 画布 1280×720，padding 上下左右 60px，内容区 1160×600
- 内容页母版：深蓝标题条（x 60–1220，y 60–124，高 64）+ 主体区（y 152–640）+ 页脚（y 670，14px 灰）
- 封面 / 参考文献页不加标题条与页脚

## 2. 配色

| 槽位 | Hex | 用途 |
|---|---|---|
| 主色 | `#1E4FA8` | 标题条、编号、关键数字、图表主序列 |
| 辅色 | `#3D7BD9` / `#E8EFF8` | 次级强调 / 浅底条（结论条、关键观察） |
| 强调 | `#D9534F` | 仅用于"诚实性"关键提示（≤3%） |
| 正文 | `#1A2230` | 主文字 |
| 次文 | `#4A5568` / `#8B97A8` | 说明 / 脚注 |
| 底色 | `#FFFFFF` | 主背景 |
| 分隔线 | `#D6DCE5` | 1px 贯通细线 |

## 3. 字体

- 全篇 Arial（英文 deck，不混入第二族）；巨型数字可用 Arial Bold
- 阶梯：封面主标 60 / 页面主标 34 / 卡片小标 24 / 正文 20 / 表格 16–18 / 脚注 14 / KPI 88

## 4. 视觉母题

- 每页标题条右侧固定「NN · Section name」小字（16px，白 80%）
- 结论句统一放页面底部浅蓝条（`#E8EFF8`，左侧 3px 主色竖条）

## 5. 配图清单

| 文件 | 等级 | 来源 | 内容 | 使用页 |
|---|---|---|---|---|
| `assets/eda_scatter.png` | L1 | 自绘（fig2） | 收入–消费散点，可见五块结构 | P3 |
| `assets/k_selection.png` | L1 | 自绘（fig5） | 肘部法则 + 轮廓系数曲线 | P5 |
| `assets/segments.png` | L1 | 自绘（fig6） | k=5 最终分群散点 + 质心 | P7 |
| `assets/boundary.png` | L2 | 自绘（fig12） | 分类器决策面近似 Voronoi | P9 |

## 6. 逐页规划

| # | 标题 | type | role / rhythm | layout | visual | 要点 |
|---|---|---|---|---|---|---|
| 1 | Mall Customer Segmentation | cover | hero / peak | 封面：主标 + 副标 + 作者信息 | — | 不放数据 |
| 2 | Two questions the mall cannot answer | content | supporting / valley | 信息横幅 + 左右两区（Q1 / Q2） | — | Q1 有几个客群；Q2 新客能否自动归类 |
| 3 | 200 customers, five visible blocks | content | supporting / valley | 左文右图 5:6 | L1 eda_scatter | 收入与消费不相关 r=0.01，结构在联合分布里 |
| 4 | Method: validate before believing | content | supporting / valley | 四阶段流程链 + 公式 | — | EDA → 聚类 → 四指标选 k → 稳定性/多算法 → 分类器 |
| 5 | Three indices agree: k = 5 | content | hero / peak | 上图下三数 | L1 k_selection | 轮廓 0.555、DB 0.572、CH 248.6 |
| 6 | Not an artefact: ARI 0.979 | content | supporting / valley | 左右两区 + 表 | — | 30 次自助抽样；Ward 0.942 / GMM 0.957 / DBSCAN 0.273 及其原因 |
| 7 | Five segments, one map | content | hero / peak | 左图右表 | L1 segments | 5 群规模与均值 |
| 8 | One segment, one action | content | supporting / valley | 五行条目清单（细线分隔） | — | 每群一条动作 + 理由 |
| 9 | Assigning a new customer | content | supporting / valley | 左表右图 | L2 boundary | SVM 97.5% / hold-out 93.3%；仅人口统计 40%，指出循环性 |
| 10 | What this project establishes | content | hero / peak | 三条结论 + 局限 | — | 结论对应 Q1/Q2；诚实列局限 |
| 11 | Key references | content | supporting / valley | 文献条目（细线分隔） | — | 7 条真实文献，方括号编号 |
