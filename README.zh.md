# 问问果蝇（Ask the Fly）

不知道吃什么时，就丢几道菜进来，让一个果蝇脑模型替你选一道。

English: [README.md](README.md)

在线试用：https://felix471.github.io/ask-the-fly/

![丢进三道菜，果蝇选一道](docs/media/demo-zh.gif)

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
- 素材：41 张菜品像素图和果蝇精灵图（`site/assets/`）是为本项目生成的原创像素画，以 CC BY 4.0 发布；代码仍为 MIT。仓库只跟踪处理后的精灵图，`assets/raw/` 里的 1024 px 原图不入库。
- FlyWire 神经元注释表（Schlegel 等 2024；github.com/flyconnectome/flywire_annotations）：CC BY 4.0。
- 分享卡二维码：qrcode-generator 2.0.4（Kazuhiko Arase），MIT，原样放在 `site/vendor/qrcode-generator/`，附许可证。
- 脑图里的神经髓轮廓：JFRC2NP 神经髓表面（Ito 等 2014 命名法）经变换到 FlyWire 空间，取自 fafbseg-py 的数据目录（github.com/navis-org/fafbseg-py，GPL-3.0；仅作数据使用，未复制代码），由 `scripts/export_neuropils.py` 投影到二维。网格压缩包放在 `data/external/`，不入库。
- 已命名的 SEZ 神经元（`data/named_neurons.json`）：ID 来自 Shiu 等 2024 随论文图表代码发布的 SEZ 神经元字典（MIT），DNg103 来自 FlyWire 注释表；Quasimodo、Scapula、GNG016 和 GNG510 在两个来源里都没有 FlyWire v783 对应，文件里如实记录。用于脑图的胞体位置（`site/data/neurons.json`）；表格本身放在 `data/external/`，不入库。

## 引用
仿真基础（分数从哪里来）：
- Shiu, P.K., et al. (2024). A Drosophila computational brain model reveals sensorimotor processing. *Nature*. PMC11446845. 模型代码（MIT）：github.com/philshiu/Drosophila_brain_model。
- FlyWire v783 连接组（Dorkenwald et al. 2024；Schlegel et al. 2024），CC BY-NC 4.0。
- Schlegel, P., Yin, Y., Bates, A.S., et al. (2024). Whole-brain annotation and multi-connectome cell typing of Drosophila. *Nature* 634, 139–152. 注释表（细胞核位置、细胞类型）：CC BY 4.0。

相关工作，不属于本仿真（见 docs/open_questions.md，OQ-2）：
- Berg, S., Beckett, I.R., Costa, M., … Hess, H.F., Rubin, G.M., Jefferis, G.S.X.E. (2026). Sexual dimorphism in the complete Drosophila male central nervous system connectome. *Cell* 189(18), 5504–5526.e15. https://doi.org/10.1016/j.cell.2026.08.015（MaleCNS；雄性脑 + 腹神经索）。
- Tastekin, I., de Haan Vicente, I., Beresford, R.J., Morris, B.J., Beckett, I., Schlegel, P., Gkantia, M., Marin, E.C., Costa, M., Jefferis, G.S.X.E., Ribeiro, C. (2026). The complete gustatory connectome of adult Drosophila reveals how taste guides feeding, foraging, and social behavior. *Cell* 189(18), 5527–5551.e5. https://doi.org/10.1016/j.cell.2026.08.016。

产品页的来源说明："分数来自已发表的雌性果蝇脑 LIF 模型（Shiu 2024 / FlyWire v783）。2026 年 9 月的两篇论文描述了更完整的味觉接线图，但不在本仿真之内。"

## 屏幕上看到的是什么

- **一段真实仿真结果的回放。** 深色脑图会按照 FlyWire 的胞体坐标画出 29,326 个神经元，然后播放当前味觉条件下预先记录好的一秒放电。画面里的每一次闪烁，都对应 Brian2 模型实际记录到的 spike；这里展示的是回放，并不是在浏览器里现场跑仿真。
- **果蝇动画由模型结果来驱动。** 它会挨个去尝每个盘子，最后飞向 MN9 平均反应最强的那一道；如果点“反着来”，就会改选反应最弱的一道。结果完全相同的菜会并列。
- **LLM 负责把菜转成味觉输入，连接组模型负责算出脑反应。** 编码器会先估算每道菜的甜、苦、水三个等级（`data/dishes.json`），然后再用这三个等级去查预先算好的 400 格结果表。
- **这些结果都可以复现。** 每个回放文件里都会保存对应的条件、刺激等级、随机种子、commit 和协议哈希，并由 `scripts/run_replay.py` 统一生成。

## 这个模型能说明什么，又不能说明什么
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

## 复现 Phase 0 曲线

Phase 0 使用论文里的 LIF 模型（Brian2），在 FlyWire v783 上复现 Shiu 2024 的糖/苦 → MN9 结果。除了编译器工具链以外，运行所需要的内容都已经放在仓库里。

**环境。** 正式运行时使用 Brian2 2.9.0 的 Cython 代码生成目标，因此需要一个 C++ 编译器。我们是在 WSL2 Ubuntu 里的 conda 环境 `flybrain` 中运行的（环境规格见 `env/flybrain.yml`，精确导出见 `env/flybrain-lock.yml`）；具体配置和踩坑记录都写在 `docs/environment.md` 里。如果直接在没有 `cl.exe` 的原生 Windows 环境中运行，就会在代码生成阶段失败。

**输入（冻结、已跟踪）。** 包括 `data/2025_Connectivity_783.parquet`（v783 连接矩阵）、`data/cells.json`（GRN 与 MN9 的 root ID）以及 `data/stim_protocol.json`（频率、试验次数、读数 = 左侧 MN9）。生成报告时，也会把当时使用的协议文件和细胞文件的 SHA-256 一并记录下来。

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

这些门槛主要看的是变化方向（A 上升、B 下降，C 和 D 保持为零），而不是要求绝对数值和论文完全一致。之所以会有数值差异，是因为论文是在 v630 上标定 `w_syn` 的，而这里直接沿用了同一参数去运行 v783。两次使用不同随机流的完整运行，在糖 100 Hz 这一点分别得到 67.2 和 67.3 Hz（`docs/phase0_report.md`、`docs/fixed_path_recheck.md`）。

**Phase 0 之后。** `scripts/run_phase1.py` 会生成 `docs/phase1_characterization.md` 里的单通道和成对曲线；`scripts/run_grid.py --stage full` 会跑完整的 400 格查找网格（14 个进程大约需要 80 分钟），然后由 `scripts/build_lookup.py` 把结果整理成 `data/lookup_table.json`。网站实际读取的就是这一份查找表。

## 如何申请加一道菜

网站目前只认识 `data/dishes.json` 里已经收录的菜。如果页面提示“果蝇还没吃过这道菜”：

1. 点那一行的 **提交这道菜**。页面会打开一个已经预填了你所输入名称的 GitHub issue。再补上中文名、英文名，以及一句话说明这是什么菜就可以了。（你也可以手动新建 issue，填写同样的四项内容。）
2. 我们会用 LLM 编码器（`encoder/encode.py`，提示词 `encode_v2.2`）分别在两种语言下各编码六次，然后再按照 `docs/encoder.md` 里的跨语言仲裁规则合并结果。如果两边的判断相差两级以上，就会标记为 `needs_review`，再由人工进行裁定。
3. 不需要重新跑仿真。甜、苦、水这三个等级会直接映射到预先算好的 400 格网格里。等到下一次部署之后，这道菜就会出现在词典和网站上。

如果一个名字可能对应不止一道菜（比如 “biscuit”），就会按照 `data/ambiguous_names.json` 拆成多个条目。如果你提交的菜属于这种情况，请在 issue 里顺便说明。
