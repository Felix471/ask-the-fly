<!-- Copy review: edit the prose under each marker. Keep the marker lines and the '## ' headings;
     scripts/import_copy.py --readme rebuilds README.md and README.zh.md from this file. -->

<!-- section: 1 | file: README.md | context: English README (GitHub landing page) — section '(preamble: title, tagline, language link)' -->
# Ask the Fly
Ask the Fly probes how a connectome-scale fruit-fly brain model responds to taste.

中文说明：[README.zh.md](README.zh.md)

<!-- section: 2 | file: README.md | context: English README (GitHub landing page) — section 'Layout' -->
## Layout
- `scripts/` — extraction and analysis utilities
- `sim/` — simulation code (added in a later phase)
- `data/` — frozen inputs, protocols, and generated results
- `docs/` — project documentation
- `site/` — static front end (no build step, no LLM calls); see docs/site.md
- `vendor/` — gitignored, read-only upstream reference data and code

<!-- section: 3 | file: README.md | context: English README (GitHub landing page) — section 'Attribution and data provenance' -->
## Attribution and data provenance
- FlyWire v783 connectome data: CC BY-NC 4.0.
- Shiu et al. (2024), *Nature*, model code: MIT.
- Eon fly-brain benchmark repository: GPL-2.0; used as read-only reference/data, with no code copied.
- Assets: the 41 dish sprites and the fly sprite sheet (`site/assets/`) are original pixel art generated for this project, released under CC BY 4.0; the code stays MIT. Only the processed sprites are tracked; the raw 1024 px sources in `assets/raw/` are not.
- FlyWire neuron annotations (Schlegel et al. 2024; github.com/flyconnectome/flywire_annotations): CC BY 4.0. Used for the soma positions behind the brain view (`site/data/neurons.json`); the table itself lives in `data/external/` and is not tracked.

<!-- section: 4 | file: README.md | context: English README (GitHub landing page) — section 'Citations' -->
## Citations
Simulation basis (what the scores come from):
- Shiu, P.K., et al. (2024). A Drosophila computational brain model reveals sensorimotor processing. *Nature*. PMC11446845. Model code (MIT): github.com/philshiu/Drosophila_brain_model.
- FlyWire v783 connectome (Dorkenwald et al. 2024; Schlegel et al. 2024), CC BY-NC 4.0.
- Schlegel, P., Yin, Y., Bates, A.S., et al. (2024). Whole-brain annotation and multi-connectome cell typing of Drosophila. *Nature* 634, 139–152. Annotation table (nucleus positions, cell types): CC BY 4.0.

Related work, not part of this simulation (see docs/open_questions.md, OQ-2):
- Berg, S., Beckett, I.R., Costa, M., … Hess, H.F., Rubin, G.M., Jefferis, G.S.X.E. (2026). Sexual dimorphism in the complete Drosophila male central nervous system connectome. *Cell* 189(18), 5504–5526.e15. https://doi.org/10.1016/j.cell.2026.08.015 (MaleCNS; male brain + VNC).
- Tastekin, I., de Haan Vicente, I., Beresford, R.J., Morris, B.J., Beckett, I., Schlegel, P., Gkantia, M., Marin, E.C., Costa, M., Jefferis, G.S.X.E., Ribeiro, C. (2026). The complete gustatory connectome of adult Drosophila reveals how taste guides feeding, foraging, and social behavior. *Cell* 189(18), 5527–5551.e5. https://doi.org/10.1016/j.cell.2026.08.016.

Product copy for provenance: "Scores come from a published female-brain LIF model (Shiu 2024 / FlyWire v783). The September 2026 papers describe a more complete taste wiring diagram that is not part of this simulation."

<!-- section: 5 | file: README.md | context: English README (GitHub landing page) — section 'What you see on screen' -->
## What you see on screen

- **Replay pack.** For each of the 400 lookup-grid cells we ran one extra 1 s trial of the same Brian2 model with the spike monitor on the whole network, seed fixed and recorded, and stored every spike (`site/data/replay/<cell>.bin`, provenance in each file's header: cell, levels, Hz, seed, commit, protocol hash). `scripts/run_replay.py` produces it.
- **Brain view is a replay, not a simulation.** The dark panel draws 29,326 neurons at their FlyWire soma positions (anterior view; Schlegel et al. 2024 annotations) and flashes the neurons that spiked, at the recorded times, over 1 s. Sugar, bitter, water and Ir94e inputs and MN9 have their own colours; the counter ticks with each recorded left-MN9 spike and ends on that trial's count. The caption names the cell being replayed. Nothing is simulated in the browser.
- **The fly is an animation over real numbers.** The fly visiting plates, landing, and extending its proboscis is scripted from the decision: plates are ranked by the lookup table's mean MN9 rate (30 trials per cell), the replay shown on each plate is that dish's cell, and the proboscis plays on the highest-ranked plate (or the lowest, for "do the opposite"). Equal cells tie exactly and the fly hovers.
- **Levels come from an LLM, scores from the connectome.** Each dish's sugar/bitter/water levels were estimated by the encoder and reviewed (`data/dishes.json`); those levels select a precomputed grid cell. The share card says so on its front.

<!-- section: 6 | file: README.md | context: English README (GitHub landing page) — section 'Honesty: what this simulation does and does not do' -->
## Honesty: what this simulation does and does not do
| Claim | Status | Source |
|---|---|---|
| Scores come from a published female-brain LIF model on FlyWire v783 | yes | Shiu et al. 2024; docs/phase0_report.md |
| Sugar drives, bitter suppresses, MN9 as the proboscis-extension readout | reproduced (directions) | docs/phase0_report.md, gates A–D |
| The model has spontaneous activity | **no** — baseline is 0 Hz by construction | Shiu 2024 Methods; our condition D |
| Disinhibition (the enriched LB3 → Quasimodo → MN motif) is expressed | **no** — zero basal firing means there is no tonic inhibition to release; v1 captures the feedforward Clavicle path only | Tastekin et al. 2026, Fig 6I/6J, Fig S17; docs/open_questions.md OQ-3 |
| Covers the whole feeding sequence | **no** — real feeding is a chain of checkpoints: leg bristles → labellar bristles → taste pegs → pharynx. This simulation covers the labellar-bristle checkpoint only. | Tastekin et al. 2026, Discussion, "Sequential checkpoints and action control" |
| Water is a separate taste quality in the model | **no** — in this model water acts as a second appetitive drive that mainly boosts weak sugar (sugar 40 Hz + water 40 Hz gives 24 Hz MN9 vs 4 Hz alone; at sugar 200 Hz it adds 7%). That is why a wet savory dish outranks a dry one. This is a property of the connectome model, not a rule we wrote. | docs/phase1_characterization.md, sugar × water |
| Uses the September 2026 complete gustatory wiring (MaleCNS) | **no** — a different animal, not part of this simulation | docs/open_questions.md, v3 note |
| The brain view shows a live simulation | **no** — it replays one recorded 1 s trial per grid cell (fixed seed) from the same model; positions are FlyWire soma coordinates, activity is the recorded spike times | docs/site.md, `site/data/replay/` headers |
| The fly animation is measured behaviour | **no** — it is a scripted animation driven by the lookup table's MN9 means and the recorded replays; the model has no body, legs or proboscis, only MN9 firing | docs/site.md |
| The fly's ranking is a live computation | **no** — a 400-cell lookup table precomputed from 30 trials per cell (`data/lookup_table.json`); the page only reads it | docs/grid_provenance.md |

In this model weak water is only visible as a helper to sugar; the fly notices water when the food is mostly water. The lookup grid therefore gives water "low" and "medium" the same cell (60 Hz): the fixed-path recheck (docs/fixed_path_recheck.md) could not separate them on any curve.

Product line: "It only does the first bite."

<!-- section: 7 | file: README.md | context: English README (GitHub landing page) — section 'Reproduce the Phase 0 curves' -->
## Reproduce the Phase 0 curves

Phase 0 reproduces the Shiu 2024 sugar/bitter → MN9 result on FlyWire v783 with the paper's LIF model in Brian2. Everything needed is in the repo except the compiler toolchain.

**Environment.** Gated runs use Brian2 2.9.0 with the Cython code-generation target, which needs a C++ compiler. We run them in WSL2 Ubuntu inside a conda env named `flybrain` (spec in `env/flybrain.yml`, exact export in `env/flybrain-lock.yml`); details and pitfalls are in `docs/environment.md`. Native Windows without `cl.exe` will fail at code generation.

**Inputs (frozen, tracked).** `data/2025_Connectivity_783.parquet` (v783 connectivity), `data/cells.json` (GRN and MN9 root IDs), `data/stim_protocol.json` (frequencies, trial count, readout = left MN9). The report records the SHA-256 of the protocol and cell files it was produced from.

**Run.**

```
# from Linux / WSL2, inside the repo
conda run -n flybrain --no-capture-output python scripts/run_phase0.py --stage smoke --target numpy   # pipeline check, no compiler needed
conda run -n flybrain --no-capture-output python scripts/run_phase0.py --stage full --n-proc 14       # 540 trials, ~4 min on 14 workers (~3 GB RAM each)
conda run -n flybrain --no-capture-output python scripts/phase0_report.py                              # regenerates docs/phase0_report.md
```

From a Windows shell the same commands run as `wsl -e bash -lc 'cd /mnt/d/<repo> && ~/miniforge3/bin/conda run -n flybrain --no-capture-output python scripts/run_phase0.py --stage full'`.

**What you should see** (left MN9, mean over 30 one-second trials; run-to-run noise is a few Hz because the Poisson stimulus stream differs):

| Gate | Condition | Expected (Hz) |
|---|---|---:|
| A | sugar 25 / 50 / 100 / 200 Hz | ≈ 0 / 17 / 67 / 92 |
| B | sugar 200 Hz + bitter 0 / 25 / 50 / 100 / 200 Hz | ≈ 93 / 79 / 70 / 28 / 1 |
| C | bitter alone, any rate | 0 |
| D | no stimulus | 0 |

The gates are directional (A rises, B falls, C and D stay at zero); absolute values differ from the paper because it calibrated `w_syn` on v630 and we run v783 unchanged. Two full runs on different random streams gave 67.2 and 67.3 Hz at sugar 100 Hz (`docs/phase0_report.md`, `docs/fixed_path_recheck.md`).

**Beyond Phase 0.** `scripts/run_phase1.py` produces the single-channel and pairwise curves in `docs/phase1_characterization.md`; `scripts/run_grid.py --stage full` runs the 400-cell lookup grid (about 80 minutes on 14 workers) and `scripts/build_lookup.py` turns it into `data/lookup_table.json`, the only file the site reads.

<!-- section: 8 | file: README.md | context: English README (GitHub landing page) — section 'How to request a dish' -->
## How to request a dish

The site only knows dishes in `data/dishes.json`. If it answers "the fly hasn't tasted this yet":

1. Press **Report it** on that line. It opens a prefilled issue at https://github.com/Felix471/ask-the-fly/issues/new with the name you typed. Add the Chinese name, the English name, and one line on what the dish is. (You can also open the issue by hand with the same four fields.)
2. We encode the dish with the LLM encoder (`encoder/encode.py`, prompt `encode_v2.1`) in both languages, six repeats each, and merge with the cross-language arbitration rules in `docs/encoder.md`. Disagreements two levels apart are marked `needs_review` and resolved by hand.
3. No simulation is needed: the three levels (sugar, bitter, water) map onto the precomputed 400-cell grid. The dish appears in the dictionary and on the site at the next deploy.

Names that mean more than one dish (for example "biscuit") are split into separate entries via `data/ambiguous_names.json`; say so in the issue if your dish is one of those.

<!-- section: 1 | file: README.zh.md | context: Chinese README (mirror of the English one) — section '(preamble: title, tagline, language link)' -->
# 问问果蝇（Ask the Fly）

Ask the Fly 用一个连接组尺度的果蝇全脑模型，测试它对味道的反应，然后拿这个反应来替你选菜。

English: [README.md](README.md)

<!-- section: 2 | file: README.zh.md | context: Chinese README (mirror of the English one) — section '目录结构' -->
## 目录结构
- `scripts/` — 数据提取与分析脚本
- `sim/` — 仿真代码
- `data/` — 冻结的输入、协议与生成结果
- `docs/` — 项目文档
- `site/` — 静态前端（无构建步骤，不调用 LLM）；见 docs/site.md
- `vendor/` — 已 gitignore，只读的上游参考数据与代码

<!-- section: 3 | file: README.zh.md | context: Chinese README (mirror of the English one) — section '署名与数据来源' -->
## 署名与数据来源
- FlyWire v783 连接组数据：CC BY-NC 4.0。
- Shiu 等（2024），*Nature*，模型代码：MIT。
- Eon fly-brain 基准仓库：GPL-2.0；仅作只读参考/数据使用，未复制任何代码。
- 素材：41 张菜品像素图和果蝇精灵图（`site/assets/`）是为本项目生成的原创像素画，以 CC BY 4.0 发布；代码仍为 MIT。仓库只跟踪处理后的精灵图，`assets/raw/` 里的 1024 px 原图不入库。
- FlyWire 神经元注释表（Schlegel 等 2024；github.com/flyconnectome/flywire_annotations）：CC BY 4.0。用于脑图的胞体位置（`site/data/neurons.json`）；表格本身放在 `data/external/`，不入库。

<!-- section: 4 | file: README.zh.md | context: Chinese README (mirror of the English one) — section '引用' -->
## 引用
仿真基础（分数从哪里来）：
- Shiu, P.K., et al. (2024). A Drosophila computational brain model reveals sensorimotor processing. *Nature*. PMC11446845. 模型代码（MIT）：github.com/philshiu/Drosophila_brain_model。
- FlyWire v783 连接组（Dorkenwald et al. 2024；Schlegel et al. 2024），CC BY-NC 4.0。
- Schlegel, P., Yin, Y., Bates, A.S., et al. (2024). Whole-brain annotation and multi-connectome cell typing of Drosophila. *Nature* 634, 139–152. 注释表（细胞核位置、细胞类型）：CC BY 4.0。

相关工作，不属于本仿真（见 docs/open_questions.md，OQ-2）：
- Berg, S., Beckett, I.R., Costa, M., … Hess, H.F., Rubin, G.M., Jefferis, G.S.X.E. (2026). Sexual dimorphism in the complete Drosophila male central nervous system connectome. *Cell* 189(18), 5504–5526.e15. https://doi.org/10.1016/j.cell.2026.08.015（MaleCNS；雄性脑 + 腹神经索）。
- Tastekin, I., de Haan Vicente, I., Beresford, R.J., Morris, B.J., Beckett, I., Schlegel, P., Gkantia, M., Marin, E.C., Costa, M., Jefferis, G.S.X.E., Ribeiro, C. (2026). The complete gustatory connectome of adult Drosophila reveals how taste guides feeding, foraging, and social behavior. *Cell* 189(18), 5527–5551.e5. https://doi.org/10.1016/j.cell.2026.08.016。

产品页的来源说明："分数来自已发表的雌性果蝇脑 LIF 模型（Shiu 2024 / FlyWire v783）。2026 年 9 月的两篇论文描述了更完整的味觉接线图，但不在本仿真之内。"

<!-- section: 5 | file: README.zh.md | context: Chinese README (mirror of the English one) — section '屏幕上看到的是什么' -->
## 屏幕上看到的是什么

- **回放包。** 对查找网格的 400 个格子，我们各自用同一个 Brian2 模型额外跑了一次 1 秒试验，全网络挂上放电监视器，随机种子固定并记录，把每一个 spike 存下来（`site/data/replay/<cell>.bin`，每个文件头里都有来源：格子、等级、Hz、种子、commit、协议哈希）。由 `scripts/run_replay.py` 生成。
- **脑图是回放，不是仿真。** 深色面板按 FlyWire 的胞体坐标（前视图；Schlegel 等 2024 注释表）画出 29,326 个神经元，并在记录到的时刻让放电的神经元闪一下，持续 1 秒。甜、苦、水、Ir94e 的输入和 MN9 各有颜色；计数器随每一个记录到的左侧 MN9 spike 递增，最后停在那次试验的数目上。说明文字写明正在回放哪个格子。浏览器里没有任何仿真。
- **果蝇是叠在真实数字上的动画。** 果蝇挨盘子飞、落下、伸口器，都是按决策脚本化的：盘子按查找表的 MN9 平均放电率（每格 30 次试验）排序，每个盘子上播放的是那道菜对应格子的回放，口器在排名最高的盘子上伸出（"反着来"时是最低的）。同一格子的菜严格并列，果蝇悬在中间。
- **等级来自 LLM，分数来自连接组。** 每道菜的甜/苦/水等级由编码器估算并经过审核（`data/dishes.json`）；等级选中一个预先算好的格子。分享卡的正面写着这一点。

<!-- section: 6 | file: README.zh.md | context: Chinese README (mirror of the English one) — section '诚实声明：这个仿真做了什么、没做什么' -->
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
| 脑图是实时仿真 | **否** —— 它回放每个格子一次记录好的 1 秒试验（固定种子），来自同一个模型；位置是 FlyWire 胞体坐标，活动是记录到的放电时刻 | docs/site.md，`site/data/replay/` 文件头 |
| 果蝇动画是测得的行为 | **否** —— 它是由查找表的 MN9 均值和记录回放驱动的脚本动画；模型没有身体、腿或口器，只有 MN9 放电 | docs/site.md |
| 果蝇的排名是实时计算 | **否** —— 一张预先算好的 400 格查找表（每格 30 次试验，`data/lookup_table.json`）；页面只是读取它 | docs/grid_provenance.md |

在这个模型里，微量的水只在帮糖时才被看见；只有食物基本是水时，果蝇才注意到水。因此查找网格把水的"低"和"中"放进同一个格子（60 Hz）：固定路径复核（docs/fixed_path_recheck.md）在任何一条曲线上都分不开它们。

产品口号："它只管第一口。"

<!-- section: 7 | file: README.zh.md | context: Chinese README (mirror of the English one) — section '复现 Phase 0 曲线' -->
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

<!-- section: 8 | file: README.zh.md | context: Chinese README (mirror of the English one) — section '如何申请加一道菜' -->
## 如何申请加一道菜

网站只认识 `data/dishes.json` 里的菜。如果它回答"果蝇还没尝过这个"：

1. 点那一行的 **报上去**。它会在 https://github.com/Felix471/ask-the-fly/issues/new 打开一个预填了你输入名称的 issue。补上中文名、英文名，以及一句话说明这是什么菜。（也可以手动开 issue，填同样四项。）
2. 我们用 LLM 编码器（`encoder/encode.py`，提示词 `encode_v2.1`）在两种语言下各编码六次，再按 `docs/encoder.md` 里的跨语言仲裁规则合并。相差两级以上的分歧会标为 `needs_review`，由人工裁定。
3. 不需要重新仿真：三个等级（糖、苦、水）直接落到预先算好的 400 格网格上。下一次部署后，这道菜就会出现在词典和网站里。

一个名字对应多道菜的（比如 "biscuit"），会按 `data/ambiguous_names.json` 拆成多个条目；如果你的菜属于这种情况，请在 issue 里说明。
