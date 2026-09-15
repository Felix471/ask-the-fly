# v1.2 copy and animation review draft

Status: owner review only; no site code or artwork. Speech source: [copy/fly_lines.json](../copy/fly_lines.json). State labels and explanations: [copy/site_strings.json](../copy/site_strings.json), not imported yet.

## Rules

Select the first matching bucket within the supplied v1.2 state; predicates use only sugar/bitter/water/ir94e levels. Select alternative index = share_seed % 3 (non-negative safe integer); alternatives are direct, emotional, action/image. Use the same index in either language. State computation, scores and tie handling are unchanged. tie and eats_first are presentation contexts, not new states.

Ordinal order: none < low < medium < high < very_high where available. Canonicalise water medium to low because the frozen table maps both to the same 60 Hz cell. Bucket 13 interprets other inputs low as <= low. First-match priority intentionally makes bucket 4 precede 5 and bucket 2 precede 3. All emotions, grooming, feeding gestures and thresholds are designed presentation, not measured feelings or validated behaviour. Chinese 鲜 is colloquial, not a scientific definition of Ir94e as umami. README honesty rows await product integration and individual owner approval.

## 中文

| 桶 | 状态 | 直接 | 情绪 | 动作或画面 |
|---|---|---|---|---|
| 1 | eats | 就这个。 | 对上了。 | 嘴已经贴上去了。 |
| 2 | eats | 苦了一下，吃。 | 那一下就算了。 | 咽下去了。 |
| 3 | eats | 那股味先放一边。 | 甜够了就过。 | 勉强进嘴。 |
| 4 | eats | 淡是淡，吃吧。 | 也没什么不行。 | 慢慢抿着。 |
| 5 | eats | 先喝一口。 | 清得很。 | 顺着就下去了。 |
| 6 | eats | 可以。 | 吃着就吃着。 | 停在这儿了。 |
| 7 | mouth_moves | 再近一点……算了。 | 嘴到了，心没到。 | 伸出去又缩回来。 |
| 8 | mouth_moves | 这是什么味。 | 再碰一下看看。 | 凑近了又停住。 |
| 9 | mouth_moves | 差一点点。 | 本来要吃的。 | 嘴边转了一圈。 |
| 10 | proboscis_only | 碰一下就行。 | 点到为止。 | 嘴尖扫过就走。 |
| 11 | no_response | 滚。 | 离远点。 | 这盘别靠近。 |
| 12 | no_response | 这不是给我的。 | 认不出这盘。 | 我不过去。 |
| 13 | no_response | 没东西。 | 不值得停。 | 飞过去了。 |
| 14 | no_response | 算了。 | 没兴趣。 | 看一眼就过。 |
| tie | tie | 你挑。 | 我分不出来。 | 两盘搁一块儿，你说。 |
| eats_first | eats_first | 这盘归我了。 | 我拿走了，剩下给你。 | 先到先得。 |

## English

| Bucket | State | Direct | Emotional | Action/image |
|---|---|---|---|---|
| 1 | eats | This one. | That's the one. | Mouth's already on it. |
| 2 | eats | A sting. Fine. | That flash can go. | Down it goes. |
| 3 | eats | Ignore that other note. | Sweet's enough. | It goes in anyway. |
| 4 | eats | Flat. I'll eat. | It'll do. | Just sipping along. |
| 5 | eats | A sip first. | Clean. | It slides right down. |
| 6 | eats | Fine. | Eating's eating. | I'll stay here. |
| 7 | mouth_moves | Closer… no. | Mouth's there. I'm not. | Out, then back. |
| 8 | mouth_moves | What is that. | One more tap. | In close, then halt. |
| 9 | mouth_moves | Almost. | Was going to. | Circled the rim and left. |
| 10 | proboscis_only | Just a tap. | That's enough. | Brush and gone. |
| 11 | no_response | Out. | Stay back. | Not this plate. |
| 12 | no_response | Not for me. | Don't know this plate. | I'm not going over. |
| 13 | no_response | Nothing here. | Not worth a stop. | Already past it. |
| 14 | no_response | Skip it. | No interest. | Glance and gone. |
| tie | tie | You pick. | Can't tell them apart. | Both sit there. You say. |
| eats_first | eats_first | This plate's mine. | I took mine. Rest is yours. | Got here first. |

## Validation checkpoint

The offline reference resolver and six tests cover all 400 frozen cells, ordered overlaps, all level combinations including water aliases, invalid inputs and deterministic bilingual seed selection. Effective (first-match) bucket counts, IDs 1–14: 8 / 77 / 24 / 8 / 30 / 38 / 40 / 12 / 0 / 4 / 107 / 23 / 8 / 21. Bucket 9 is retained as requested although no current cell reaches it. Raw predicates intentionally overlap; uniqueness is checked after excluding earlier matches. Full Python suite: 338 passed; Node: 67 passed; release validator and copy importer check pass. No site/data or frozen data changes, no artwork, no copy import.

## Animation plan — not executed

### Source and production method

The local source is `assets/raw/fly/fly.png`, a 3×3 sheet: idle_1–2, fly_1–4, land_1, proboscis_1–2. `proboscis_3` reuses land_1. Dish originals are `assets/raw/<slug>.png`. See [asset provenance](assets.md) and [prep_assets.py](../scripts/prep_assets.py). Existing fly sprites are 48×48, facing right; dishes are 96×96. No dish redraw is proposed.

For approved new poses, reference-edit the original fly sheet, keeping body proportions, outline, eyes, legs and colours; generate only the changed mouth/front-leg poses on transparent, equal-size canvases. Archive reference, prompt and generator/version alongside new raw files. The existing processing provenance is known; the original image-generation model/prompt is not established by these files, so do not claim an exact generator match. Review a contact sheet against the existing fly before processing final frames.

Use the same pipeline: existing alpha or corner flood-fill (tolerance 24), nearest-neighbour reduction, shared 32-colour palette and RGBA PNG. Current CLI limitations matter: fly processing learns a new batch palette even with --palette-from; it crops each frame independently, writes directly to site/assets/fly, and its sheet frame counts are fixed. A later approved implementation must add a staged output path, fixed existing-fly palette, common bounding box/anchor and new frame definitions before running it. Do not run it as-is and overwrite shipped sprites. Keep old frames byte-identical.

### Main fly frame list and timing (designed, provisional)

| State | Frames | Planned sequence |
|---|---|---|
| eats | Existing land_1, proboscis_1–3 | Extend, hold, retract; reuse current visual vocabulary. No new main-body frames. |
| mouth_moves | New mouth_moves_1–4: closed/lean in; small mouth opening; slightly wider opening with head pause; close/lean back | 180/180/240/220 ms; at most two cycles, then settle. No full proboscis extension. Bitter bucket pauses mid-approach to express conflict; amino-acid bucket approaches then withdraws in puzzlement, without a disgust gesture. |
| proboscis_only | Existing proboscis_1, proboscis_2, proboscis_3 | 120/80/160 ms: extend, brief contact, retract once; no mouth-motion loop. Re-time only, no new main-body art. |
| no_response | New groom_1–4: front legs lift; meet; rub one way; rub back; existing land/fly frames | Lift 180 ms; meet 120 ms; rub 3/4 twice at 140 ms/frame; lower using frame 1 then land_1; depart. Mouth stays closed. Bitter caption gets a short recoil using existing pose/position before grooming; tasteless bucket gets no approach hold. Grooming is a designed action, not a neuronal inference. |

All new frames share body/foot anchors; later per-plate rendering must not change plate-row geometry. Differences between voice buckets use holds/position only unless separately approved, not fourteen separate sprite sets. Tie and eats-first reuse existing movement and do not invent a fifth state.

### Mouth-part inset per state

Use a consistent, clearly labelled illustrative side-view crop of the same fly, not a new anatomical illustration. Plan a 64×64 source-pixel inset rendered at integer scale, with the same mouth anchor throughout. Source edits start from the original high-resolution sheet (not an AI upsample of the 48×48 export), then use the same palette/downsampling pipeline. Add no pumping/CEM or swallowing depiction. Animation cadence is designed, not replay-spike timing.

| State | Inset frames | Motion |
|---|---|---|
| eats | inset_eats_1–4: closed; extending; extended/open; extended/close | Extend then small open/close cycle; retract to closed at end. |
| mouth_moves | inset_mouth_moves_1–3: closed; small opening; larger opening | 1→2→3→2→1, with a hesitation hold; proboscis not fully extended. |
| proboscis_only | inset_proboscis_only_1–3: closed; partial extension; full extension | 1→2→3→2→1, brief single contact, no open/close cycle; aligned to main-body re-timing. |
| no_response | inset_no_response_1: closed | Static closed mouth while the main fly grooms; do not suggest the whole fly is motionless. |

Eleven inset frames and eight new main-body frames are proposed; unchanged/reusable images need not be independently generated. Reduced motion uses one representative static pose per state and a static inset, with the text/readouts carrying the distinction. Acceptance checks after approval: style match, palette and alpha, fixed anchors/no jitter, clear distinctions at native size, integer-scale insets, narrow widths, reduced motion, and no third-party runtime requests. No art or implementation has started.
