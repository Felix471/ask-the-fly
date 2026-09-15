# v1.2 copy and animation review draft

Status: owner review only; no site code or artwork. Speech source: [copy/fly_lines.json](../copy/fly_lines.json). State labels and explanations: [copy/site_strings.json](../copy/site_strings.json), not imported yet.

## Rules

Select the first matching bucket within the supplied v1.2 state; predicates use only sugar/bitter/water/ir94e levels. Select alternative index = share_seed % 3 (non-negative safe integer); alternatives are direct, emotional, action/image. Use the same index in either language. State computation, scores and tie handling are unchanged. tie and eats_first are presentation contexts, not new states.

Ordinal order: none < low < medium < high < very_high where available. Canonicalise water medium to low because the frozen table maps both to the same 60 Hz cell. Bucket 13 interprets other inputs low as <= low. First-match priority intentionally makes bucket 4 precede 5 and bucket 2 precede 3. All emotions, grooming, feeding gestures and thresholds are designed presentation, not measured feelings or validated behaviour. Chinese 鲜 is colloquial, not a scientific definition of Ir94e as umami. README honesty rows await product integration and individual owner approval.

## 中文

| 桶 | 状态 | 直接 | 情绪 | 动作或画面 |
|---|---|---|---|---|
| 1 | eats | 就要这个。 | 甜得正好！ | 这口我先吃。 |
| 2 | eats | 有点苦，也吃。 | 苦归苦，甜就行。 | 皱下脸，接着吃。 |
| 3 | eats | 这鲜味，勉强吃。 | 算了，甜就放过。 | 躲一下，再吃口。 |
| 4 | eats | 淡点也吃。 | 没惊喜，也行。 | 慢慢吃两口。 |
| 5 | eats | 先喝一口。 | 这口水来得好！ | 凑过去，喝个够。 |
| 6 | eats | 就吃这个。 | 行，还不错。 | 凑近吃一口。 |
| 7 | mouth_moves | 想吃，又不敢吃。 | 真馋，可是好苦。 | 嘴都动了，还犹豫。 |
| 8 | mouth_moves | 这味儿，拿不准。 | 怪了，到底吃不吃？ | 凑近了，又退半步。 |
| 9 | mouth_moves | 差点就吃了。 | 可惜，就差一点。 | 凑到嘴边，又停了。 |
| 10 | proboscis_only | 碰一下就好。 | 也就碰一下。 | 伸一下，收回来。 |
| 11 | no_response | 不吃。 | 呸。 | 扭头，离远点。 |
| 12 | no_response | 这不是我的饭。 | 光鲜不甜，不要。 | 推远点，不是我的。 |
| 13 | no_response | 没味儿，不吃。 | 白来一趟。 | 当没看见，飞走。 |
| 14 | no_response | 不太想吃。 | 提不起劲。 | 看一眼，走了。 |
| tie | tie | 分不出，你挑。 | 都差不多，随你。 | 往旁边一让，你来。 |
| eats_first | eats_first | 这盘我的，剩下归你。 | 我挑好了，你吃剩下。 | 抱走这盘，你慢挑。 |

## English

| Bucket | State | Direct | Emotional | Action/image |
|---|---|---|---|---|
| 1 | eats | This one. Definitely. | Now that's sweet! | Out of my way. First bite's mine. |
| 2 | eats | Bitter. Still having it. | Sweet enough to forgive. | A wince. Another bite. |
| 3 | eats | That taste. I'll allow it. | Saved by the sweet part. | Lean away. Sneak a bite. |
| 4 | eats | Bland. It'll do. | Nothing special. Fine. | A couple of quiet bites. |
| 5 | eats | A sip first. | Just the drink I wanted! | Scoot over. I'm drinking. |
| 6 | eats | This will do. | Yeah, I like it. | Closer. One bite. |
| 7 | mouth_moves | I want it. I don't dare. | So tempting. So bitter. | Mouth's ready. I'm not. |
| 8 | mouth_moves | Can't quite place it. | What is that? Do I want it? | Closer… no, back a bit. |
| 9 | mouth_moves | Almost took a bite. | So close. What a shame. | Right at my mouth. Then I stop. |
| 10 | proboscis_only | Just a touch. | Only a little tap. | Reach out. Pull back. |
| 11 | no_response | No. | Bleh. | Turn away. Keep it away. |
| 12 | no_response | That's not my food. | All that taste, no sweet? No. | Push it away. Not mine. |
| 13 | no_response | No taste. No bite. | Well, that was a wasted trip. | Didn't see a thing. Off I go. |
| 14 | no_response | Not interested. | Can't get excited about it. | One glance. Moving on. |
| tie | tie | Can't choose. Your call. | Either works. Suit yourself. | I'll step aside. You pick. |
| eats_first | eats_first | Mine. The rest are yours. | I've picked. Help yourself to the rest. | Taking this one. Take your time. |

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
