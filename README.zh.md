# 问问果蝇（Ask the Fly）

Ask the Fly 用一个连接组尺度的果蝇全脑模型，测试它对味道的反应，然后拿这个反应来替你选菜。

English: [README.md](README.md)

## 目录结构
- `scripts/` — 数据提取与分析脚本
- `sim/` — 仿真代码
- `data/` — 冻结的输入、协议与生成结果
- `docs/` — 项目文档
- `site/` — 静态前端（无构建步骤，不调用 LLM）；见 docs/site.md
- `vendor/` — 已 gitignore，只读的上游参考数据与代码

## 署名与数据来源
- FlyWire v783 连接组数据：CC BY-NC 4.0。
- Shiu 等（2024），*Nature*，模型代码：MIT。
- Eon fly-brain 基准仓库：GPL-2.0；仅作只读参考/数据使用，未复制任何代码。

## 引用
仿真基础（分数从哪里来）：
- Shiu, P.K., et al. (2024). A Drosophila computational brain model reveals sensorimotor processing. *Nature*. PMC11446845. 模型代码（MIT）：github.com/philshiu/Drosophila_brain_model。
- FlyWire v783 连接组（Dorkenwald et al. 2024；Schlegel et al. 2024），CC BY-NC 4.0。

相关工作，不属于本仿真（见 docs/open_questions.md，OQ-2）：
- Berg, S., Beckett, I.R., Costa, M., … Hess, H.F., Rubin, G.M., Jefferis, G.S.X.E. (2026). Sexual dimorphism in the complete Drosophila male central nervous system connectome. *Cell* 189(18), 5504–5526.e15. https://doi.org/10.1016/j.cell.2026.08.015（MaleCNS；雄性脑 + 腹神经索）。
- Tastekin, I., de Haan Vicente, I., Beresford, R.J., Morris, B.J., Beckett, I., Schlegel, P., Gkantia, M., Marin, E.C., Costa, M., Jefferis, G.S.X.E., Ribeiro, C. (2026). The complete gustatory connectome of adult Drosophila reveals how taste guides feeding, foraging, and social behavior. *Cell* 189(18), 5527–5551.e5. https://doi.org/10.1016/j.cell.2026.08.016。

产品页的来源说明："分数来自已发表的雌性果蝇脑 LIF 模型（Shiu 2024 / FlyWire v783）。2026 年 9 月的两篇论文描述了更完整的味觉接线图，但不在本仿真之内。"

## 诚实声明：这个仿真做了什么、没做什么
| 说法 | 状态 | 依据 |
|---|---|---|
| 分数来自已发表的雌性果蝇脑 LIF 模型，运行在 FlyWire v783 上 | 是 | Shiu et al. 2024；docs/phase0_report.md |
| 糖驱动、苦抑制、以 MN9 作为伸喙读数 | 已复现（方向） | docs/phase0_report.md，门槛 A–D |
| 模型有自发活动 | **否** —— 基线按构造为 0 Hz | Shiu 2024 Methods；我们的条件 D |
| 表达了去抑制（富集的 LB3 → Quasimodo → MN 回路） | **否** —— 基础放电为零，没有可释放的持续性抑制；v1 只包含前馈的 Clavicle 通路 | Tastekin et al. 2026，图 6I/6J、图 S17；docs/open_questions.md OQ-3 |
| 覆盖完整的进食序列 | **否** —— 真实进食是一串检查点：足部刚毛 → 唇瓣刚毛 → 味觉钉 → 咽。本仿真只覆盖唇瓣刚毛这一站。 | Tastekin et al. 2026，讨论部分 "Sequential checkpoints and action control" |
| 水在模型里是独立的味觉品质 | **否** —— 在这个模型里水是第二种食欲驱动，主要帮弱糖加分（糖 40 Hz + 水 40 Hz 得到 24 Hz MN9，单独糖只有 4 Hz；糖 200 Hz 时只多 7%）。所以湿的咸菜会赢过干的。这是连接组模型的性质，不是我们写的规则。 | docs/phase1_characterization.md，糖 × 水 |
| 使用了 2026 年 9 月的完整味觉接线（MaleCNS） | **否** —— 另一只动物，不在本仿真内 | docs/open_questions.md，v3 note |

在这个模型里，微量的水只在帮糖时才被看见；只有食物基本是水时，果蝇才注意到水。因此查找网格把水的"低"和"中"放进同一个格子（60 Hz）：固定路径复核（docs/fixed_path_recheck.md）在任何一条曲线上都分不开它们。

产品口号："它只管第一口。"

## 复现 Phase 0 曲线

Phase 0 用论文的 LIF 模型（Brian2）在 FlyWire v783 上复现 Shiu 2024 的糖/苦 → MN9 结果。除编译器工具链外，所需的一切都在仓库里。

**环境。** 正式运行使用 Brian2 2.9.0 的 Cython 代码生成目标，需要 C++ 编译器。我们在 WSL2 Ubuntu 里的 conda 环境 `flybrain` 中运行（规格见 `env/flybrain.yml`，精确导出见 `env/flybrain-lock.yml`）；细节与坑见 `docs/environment.md`。没有 `cl.exe` 的原生 Windows 会在代码生成阶段失败。

**输入（冻结、已跟踪）。** `data/2025_Connectivity_783.parquet`（v783 连接矩阵）、`data/cells.json`（GRN 与 MN9 的 root ID）、`data/stim_protocol.json`（频率、试验次数、读数 = 左侧 MN9）。报告会记录生成它时协议文件与细胞文件的 SHA-256。

**运行。**

```
# 在 Linux / WSL2 的仓库目录下
conda run -n flybrain --no-capture-output python scripts/run_phase0.py --stage smoke --target numpy   # 流程检查，不需要编译器
conda run -n flybrain --no-capture-output python scripts/run_phase0.py --stage full --n-proc 14       # 540 次试验，14 个进程约 4 分钟（每个约 3 GB 内存）
conda run -n flybrain --no-capture-output python scripts/phase0_report.py                              # 重新生成 docs/phase0_report.md
```

在 Windows 命令行里，同样的命令写成 `wsl -e bash -lc 'cd /mnt/d/<repo> && ~/miniforge3/bin/conda run -n flybrain --no-capture-output python scripts/run_phase0.py --stage full'`。

**应该看到的结果**（左侧 MN9，30 次 1 秒试验的均值；不同随机流之间有几 Hz 的波动）：

| 门槛 | 条件 | 预期（Hz） |
|---|---|---:|
| A | 糖 25 / 50 / 100 / 200 Hz | ≈ 0 / 17 / 67 / 92 |
| B | 糖 200 Hz + 苦 0 / 25 / 50 / 100 / 200 Hz | ≈ 93 / 79 / 70 / 28 / 1 |
| C | 只有苦，任何频率 | 0 |
| D | 无刺激 | 0 |

门槛只看方向（A 上升、B 下降、C 和 D 保持为零）；绝对值与论文不同，因为论文在 v630 上标定了 `w_syn`，而我们原样运行 v783。两次不同随机流的完整运行在糖 100 Hz 处分别得到 67.2 和 67.3 Hz（`docs/phase0_report.md`、`docs/fixed_path_recheck.md`）。

**Phase 0 之后。** `scripts/run_phase1.py` 生成 `docs/phase1_characterization.md` 里的单通道与成对曲线；`scripts/run_grid.py --stage full` 运行 400 格的查找网格（14 个进程约 80 分钟），`scripts/build_lookup.py` 把它转成 `data/lookup_table.json`，这是网站唯一读取的文件。

## 如何申请加一道菜

网站只认识 `data/dishes.json` 里的菜。如果它回答"果蝇还没尝过这个"：

1. 点那一行的 **报上去**。它会在 https://github.com/Felix471/ask-the-fly/issues/new 打开一个预填了你输入名称的 issue。补上中文名、英文名，以及一句话说明这是什么菜。（也可以手动开 issue，填同样四项。）
2. 我们用 LLM 编码器（`encoder/encode.py`，提示词 `encode_v2.1`）在两种语言下各编码六次，再按 `docs/encoder.md` 里的跨语言仲裁规则合并。相差两级以上的分歧会标为 `needs_review`，由人工裁定。
3. 不需要重新仿真：三个等级（糖、苦、水）直接落到预先算好的 400 格网格上。下一次部署后，这道菜就会出现在词典和网站里。

一个名字对应多道菜的（比如 "biscuit"），会按 `data/ambiguous_names.json` 拆成多个条目；如果你的菜属于这种情况，请在 issue 里说明。
