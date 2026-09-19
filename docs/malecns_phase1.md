<!-- male-v1-phase1:begin -->
# Male-v1 Phase 1 characterisation

Completed UTC: 2026-09-19T04:17:09.549860+00:00; Brian2 2.9.0 / cython; workers 16; 35 conditions × 30 = 1,050 trials; seeds 20260910–20260939 shared across conditions; wall 655.229 s; peak worker RSS 1.031929 GiB.

MaleCNS v1.0 whole CNS, M1i >=5-synapse graph with 33 autapses removed: 166,700 neurons, 6,242,085 edges, 89,859,938 synapses; w_syn 0.17875 mV exactly, external kick w_syn*f_poi = 44.6875 mV. The frozen male protocol uses 108 bilateral typed inputs and primary MN9 L10331; R16949 is secondary.

All rates are mean ± population SD in Hz, n=30. Male MN11D/MN11V/CEM statistics are computed over per-trial means across 3/2/6 cells, respectively. Latencies below are medians among positive trials; a group latency is its earliest member spike. The female reference uses unilateral Shiu sets on FlyWire v783, all connections, w_syn 0.275 mV; these are different experiments and are not paired trials.

Female values come from frozen [lookup_table_v1_2.json](../data/lookup_table_v1_2.json), `mn9_left_mean`/`mn9_left_std`, `mn9_right_mean`/`mn9_right_std`, `mn11d_mean`/`mn11d_sd`, and `mn11v_mean`/`mn11v_sd`, at identical Hz coordinates with bitter 0. Water 60 uses the `low` grid cell. Female CEM: not recorded in the female grid. The numerical tables below use the grid, not the earlier characterisation screen.

### Table 1: water alone

| water Hz | male L10331 | male R16949 | male MN11D | male MN11V | male CEM | male network median | female left MN9 | female right MN9 | female MN11D | female MN11V |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.0 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 |
| 60 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 1286.5 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 |
| 180 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 4475.0 | 22.300 ± 6.659 | 8.433 ± 4.681 | 6.183 ± 1.851 | 0.217 ± 0.495 |
| 240 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 6005.5 | 45.800 ± 5.338 | 20.400 ± 4.055 | 21.483 ± 3.736 | 1.800 ± 1.646 |

### Table 2: water × sugar

| sugar Hz | water Hz | male L10331 | female left MN9 | male MN11D | female MN11D |
| --- | --- | --- | --- | --- | --- |
| 0 | 0 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 |
| 0 | 60 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 |
| 0 | 180 | 0.000 ± 0.000 | 22.300 ± 6.659 | 0.000 ± 0.000 | 6.183 ± 1.851 |
| 0 | 240 | 0.000 ± 0.000 | 45.800 ± 5.338 | 0.000 ± 0.000 | 21.483 ± 3.736 |
| 60 | 0 | 16.233 ± 4.752 | 34.667 ± 6.052 | 0.000 ± 0.000 | 35.167 ± 14.244 |
| 60 | 60 | 11.867 ± 4.349 | 61.767 ± 5.005 | 0.000 ± 0.000 | 76.100 ± 9.103 |
| 60 | 180 | 5.767 ± 2.276 | 68.467 ± 6.185 | 0.000 ± 0.000 | 98.283 ± 9.093 |
| 60 | 240 | 5.200 ± 2.227 | 70.800 ± 5.406 | 0.856 ± 0.739 | 104.167 ± 9.596 |
| 80 | 0 | 40.867 ± 6.391 | 58.033 ± 5.376 | 0.000 ± 0.000 | 70.650 ± 8.020 |
| 80 | 60 | 34.800 ± 10.111 | 70.567 ± 5.207 | 0.022 ± 0.120 | 94.250 ± 8.097 |
| 80 | 180 | 16.300 ± 4.458 | 78.400 ± 5.187 | 0.356 ± 0.354 | 109.033 ± 7.580 |
| 80 | 240 | 16.867 ± 4.425 | 77.933 ± 5.785 | 3.144 ± 1.053 | 112.283 ± 7.880 |
| 120 | 0 | 81.267 ± 5.046 | 74.633 ± 4.476 | 17.233 ± 16.180 | 92.733 ± 8.514 |
| 120 | 60 | 77.167 ± 8.000 | 85.833 ± 4.748 | 24.356 ± 16.957 | 113.050 ± 9.657 |
| 120 | 180 | 62.167 ± 6.532 | 91.333 ± 4.134 | 24.100 ± 14.339 | 122.867 ± 6.810 |
| 120 | 240 | 61.333 ± 6.987 | 88.400 ± 5.607 | 28.256 ± 12.911 | 127.483 ± 8.765 |
| 200 | 0 | 101.967 ± 4.309 | 91.767 ± 5.018 | 39.078 ± 17.284 | 123.183 ± 7.996 |
| 200 | 60 | 96.433 ± 4.470 | 97.233 ± 5.578 | 60.178 ± 21.032 | 132.633 ± 6.282 |
| 200 | 180 | 92.133 ± 5.590 | 101.633 ± 3.911 | 59.767 ± 9.362 | 140.850 ± 7.075 |
| 200 | 240 | 94.133 ± 4.072 | 100.367 ± 5.388 | 61.189 ± 9.591 | 140.267 ± 8.085 |

### Table 3: ir94e alone

| ir94e Hz | male L10331 | male R16949 | male MN11D | male MN11V | male CEM | male network median | female left MN9 | female right MN9 | female MN11D | female MN11V |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.0 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 |
| 60 | 1.300 ± 1.295 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 298894.0 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 |
| 120 | 0.867 ± 0.884 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 301499.5 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.200 ± 0.748 | 0.083 ± 0.291 |
| 200 | 0.500 ± 0.619 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 303067.5 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.200 ± 0.542 | 0.083 ± 0.227 |

### Table 4: ir94e × sugar

| sugar Hz | ir94e Hz | male L10331 | female left MN9 | male MN11D | female MN11D |
| --- | --- | --- | --- | --- | --- |
| 0 | 0 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 |
| 0 | 60 | 1.300 ± 1.295 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.000 ± 0.000 |
| 0 | 120 | 0.867 ± 0.884 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.200 ± 0.748 |
| 0 | 200 | 0.500 ± 0.619 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.200 ± 0.542 |
| 60 | 0 | 16.233 ± 4.752 | 34.667 ± 6.052 | 0.000 ± 0.000 | 35.167 ± 14.244 |
| 60 | 60 | 5.567 ± 2.201 | 1.400 ± 1.977 | 0.000 ± 0.000 | 4.483 ± 6.016 |
| 60 | 120 | 4.733 ± 2.220 | 0.433 ± 0.667 | 0.000 ± 0.000 | 5.417 ± 4.708 |
| 60 | 200 | 3.267 ± 2.159 | 0.100 ± 0.300 | 0.000 ± 0.000 | 10.450 ± 8.621 |
| 80 | 0 | 40.867 ± 6.391 | 58.033 ± 5.376 | 0.000 ± 0.000 | 70.650 ± 8.020 |
| 80 | 60 | 4.233 ± 2.390 | 15.400 ± 5.320 | 0.000 ± 0.000 | 33.600 ± 10.842 |
| 80 | 120 | 4.467 ± 2.187 | 3.633 ± 2.041 | 0.000 ± 0.000 | 26.817 ± 14.248 |
| 80 | 200 | 3.767 ± 1.667 | 0.867 ± 0.806 | 0.000 ± 0.000 | 27.100 ± 13.103 |
| 120 | 0 | 81.267 ± 5.046 | 74.633 ± 4.476 | 17.233 ± 16.180 | 92.733 ± 8.514 |
| 120 | 60 | 1.600 ± 1.200 | 56.433 ± 5.976 | 0.000 ± 0.000 | 83.567 ± 7.463 |
| 120 | 120 | 1.033 ± 1.048 | 28.133 ± 7.338 | 0.000 ± 0.000 | 80.217 ± 10.363 |
| 120 | 200 | 1.300 ± 1.418 | 8.600 ± 4.302 | 0.000 ± 0.000 | 73.633 ± 10.182 |
| 200 | 0 | 101.967 ± 4.309 | 91.767 ± 5.018 | 39.078 ± 17.284 | 123.183 ± 7.996 |
| 200 | 60 | 6.833 ± 2.491 | 82.967 ± 5.351 | 0.000 ± 0.000 | 116.817 ± 6.837 |
| 200 | 120 | 2.233 ± 1.453 | 70.767 ± 5.110 | 0.000 ± 0.000 | 110.950 ± 9.116 |
| 200 | 200 | 1.267 ± 1.236 | 60.667 ± 8.957 | 0.000 ± 0.000 | 107.700 ± 11.021 |

## Descriptive verdicts

Water is not observed as an appetitive driver under this design.
Ir94e suppresses.

These are descriptive, pre-declared screen criteria, not gates. Water is called appetitive if water 240 alone gives L10331 >5 Hz or any tested water dose raises L10331 at sugar 60 by >5 Hz against sugar 60 alone. Ir94e suppression means non-increasing L10331 across ir94e 0/60/120/200 at sugar 200 with a net decrease and ir94e 200 alone <5 Hz; otherwise any ir94e-alone level >5 Hz gives “excites MN9”, otherwise no monotone suppression is observed.

The [female characterisation](phase1_characterization.md#channel-summary) reports water as excitatory alone and facilitating as a modifier of sugar. It reports Ir94e as having no effect alone and being suppressive as a modifier of sugar under that design. These historical female screen classifications use their original criteria, not the male descriptive criteria.

## Every condition and readout

### s0_b0_w0_i0

| readout (Body_ID where individual) | Hz | positive trials / 30 | latency median ms |
| --- | --- | --- | --- |
| L | 0.000 ± 0.000 | 0 | not observed |
| R | 0.000 ± 0.000 | 0 | not observed |
| mn11d_11269 | 0.000 ± 0.000 | 0 | not observed |
| mn11d_11393 | 0.000 ± 0.000 | 0 | not observed |
| mn11d_551398 | 0.000 ± 0.000 | 0 | not observed |
| mn11d | 0.000 ± 0.000 | 0 | not observed |
| mn11v_49829 | 0.000 ± 0.000 | 0 | not observed |
| mn11v_492462351 | 0.000 ± 0.000 | 0 | not observed |
| mn11v | 0.000 ± 0.000 | 0 | not observed |
| cem_19823 | 0.000 ± 0.000 | 0 | not observed |
| cem_20518 | 0.000 ± 0.000 | 0 | not observed |
| cem_23511 | 0.000 ± 0.000 | 0 | not observed |
| cem_32852 | 0.000 ± 0.000 | 0 | not observed |
| cem_34597 | 0.000 ± 0.000 | 0 | not observed |
| cem_482595 | 0.000 ± 0.000 | 0 | not observed |
| cem | 0.000 ± 0.000 | 0 | not observed |

Network spikes median [min–max]: 0.0 [0–0]; neurons fired median [min–max]: 0.0 [0–0].

### s60_b0_w0_i0

| readout (Body_ID where individual) | Hz | positive trials / 30 | latency median ms |
| --- | --- | --- | --- |
| L | 16.233 ± 4.752 | 30 | 94.80000000000001 |
| R | 0.000 ± 0.000 | 0 | not observed |
| mn11d_11269 | 0.000 ± 0.000 | 0 | not observed |
| mn11d_11393 | 0.000 ± 0.000 | 0 | not observed |
| mn11d_551398 | 0.000 ± 0.000 | 0 | not observed |
| mn11d | 0.000 ± 0.000 | 0 | not observed |
| mn11v_49829 | 0.000 ± 0.000 | 0 | not observed |
| mn11v_492462351 | 0.000 ± 0.000 | 0 | not observed |
| mn11v | 0.000 ± 0.000 | 0 | not observed |
| cem_19823 | 0.000 ± 0.000 | 0 | not observed |
| cem_20518 | 0.000 ± 0.000 | 0 | not observed |
| cem_23511 | 0.000 ± 0.000 | 0 | not observed |
| cem_32852 | 0.000 ± 0.000 | 0 | not observed |
| cem_34597 | 0.000 ± 0.000 | 0 | not observed |
| cem_482595 | 0.000 ± 0.000 | 0 | not observed |
| cem | 0.000 ± 0.000 | 0 | not observed |

Network spikes median [min–max]: 6995.5 [5538–8736]; neurons fired median [min–max]: 569.0 [358–732].

### s80_b0_w0_i0

| readout (Body_ID where individual) | Hz | positive trials / 30 | latency median ms |
| --- | --- | --- | --- |
| L | 40.867 ± 6.391 | 30 | 69.95 |
| R | 0.000 ± 0.000 | 0 | not observed |
| mn11d_11269 | 0.000 ± 0.000 | 0 | not observed |
| mn11d_11393 | 0.000 ± 0.000 | 0 | not observed |
| mn11d_551398 | 0.000 ± 0.000 | 0 | not observed |
| mn11d | 0.000 ± 0.000 | 0 | not observed |
| mn11v_49829 | 0.000 ± 0.000 | 0 | not observed |
| mn11v_492462351 | 0.000 ± 0.000 | 0 | not observed |
| mn11v | 0.000 ± 0.000 | 0 | not observed |
| cem_19823 | 0.000 ± 0.000 | 0 | not observed |
| cem_20518 | 0.000 ± 0.000 | 0 | not observed |
| cem_23511 | 0.000 ± 0.000 | 0 | not observed |
| cem_32852 | 0.000 ± 0.000 | 0 | not observed |
| cem_34597 | 0.000 ± 0.000 | 0 | not observed |
| cem_482595 | 0.000 ± 0.000 | 0 | not observed |
| cem | 0.000 ± 0.000 | 0 | not observed |

Network spikes median [min–max]: 11775.5 [9874–14019]; neurons fired median [min–max]: 772.5 [707–881].

### s120_b0_w0_i0

| readout (Body_ID where individual) | Hz | positive trials / 30 | latency median ms |
| --- | --- | --- | --- |
| L | 81.267 ± 5.046 | 30 | 47.300000000000004 |
| R | 0.000 ± 0.000 | 0 | not observed |
| mn11d_11269 | 23.767 ± 21.568 | 30 | 196.95000000000002 |
| mn11d_11393 | 25.200 ± 23.364 | 30 | 197.05 |
| mn11d_551398 | 2.733 ± 3.705 | 21 | 502.8 |
| mn11d | 17.233 ± 16.180 | 30 | 196.95000000000002 |
| mn11v_49829 | 8.567 ± 12.230 | 21 | 498.70000000000005 |
| mn11v_492462351 | 0.667 ± 1.300 | 10 | 429.65000000000003 |
| mn11v | 4.617 ± 6.730 | 21 | 498.70000000000005 |
| cem_19823 | 0.000 ± 0.000 | 0 | not observed |
| cem_20518 | 1.067 ± 1.031 | 19 | 496.8 |
| cem_23511 | 0.233 ± 0.423 | 7 | 575.0000000000001 |
| cem_32852 | 0.000 ± 0.000 | 0 | not observed |
| cem_34597 | 0.000 ± 0.000 | 0 | not observed |
| cem_482595 | 0.000 ± 0.000 | 0 | not observed |
| cem | 0.217 ± 0.211 | 19 | 496.8 |

Network spikes median [min–max]: 24533.0 [19483–250157]; neurons fired median [min–max]: 1292.5 [939–8236].

### s200_b0_w0_i0

| readout (Body_ID where individual) | Hz | positive trials / 30 | latency median ms |
| --- | --- | --- | --- |
| L | 101.967 ± 4.309 | 30 | 38.1 |
| R | 0.000 ± 0.000 | 0 | not observed |
| mn11d_11269 | 53.900 ± 22.947 | 30 | 81.55000000000001 |
| mn11d_11393 | 57.133 ± 24.802 | 30 | 81.30000000000001 |
| mn11d_551398 | 6.200 ± 4.269 | 27 | 218.60000000000002 |
| mn11d | 39.078 ± 17.284 | 30 | 81.30000000000001 |
| mn11v_49829 | 19.300 ± 12.432 | 27 | 210.4 |
| mn11v_492462351 | 1.600 ± 1.583 | 18 | 261.45000000000005 |
| mn11v | 10.450 ± 6.929 | 27 | 210.4 |
| cem_19823 | 0.000 ± 0.000 | 0 | not observed |
| cem_20518 | 1.533 ± 1.176 | 23 | 207.50000000000003 |
| cem_23511 | 0.467 ± 0.562 | 13 | 278.90000000000003 |
| cem_32852 | 0.000 ± 0.000 | 0 | not observed |
| cem_34597 | 0.000 ± 0.000 | 0 | not observed |
| cem_482595 | 0.000 ± 0.000 | 0 | not observed |
| cem | 0.333 ± 0.262 | 23 | 207.50000000000003 |

Network spikes median [min–max]: 327007.5 [291428–335669]; neurons fired median [min–max]: 8086.5 [7581–8256].

### s0_b0_w60_i0

| readout (Body_ID where individual) | Hz | positive trials / 30 | latency median ms |
| --- | --- | --- | --- |
| L | 0.000 ± 0.000 | 0 | not observed |
| R | 0.000 ± 0.000 | 0 | not observed |
| mn11d_11269 | 0.000 ± 0.000 | 0 | not observed |
| mn11d_11393 | 0.000 ± 0.000 | 0 | not observed |
| mn11d_551398 | 0.000 ± 0.000 | 0 | not observed |
| mn11d | 0.000 ± 0.000 | 0 | not observed |
| mn11v_49829 | 0.000 ± 0.000 | 0 | not observed |
| mn11v_492462351 | 0.000 ± 0.000 | 0 | not observed |
| mn11v | 0.000 ± 0.000 | 0 | not observed |
| cem_19823 | 0.000 ± 0.000 | 0 | not observed |
| cem_20518 | 0.000 ± 0.000 | 0 | not observed |
| cem_23511 | 0.000 ± 0.000 | 0 | not observed |
| cem_32852 | 0.000 ± 0.000 | 0 | not observed |
| cem_34597 | 0.000 ± 0.000 | 0 | not observed |
| cem_482595 | 0.000 ± 0.000 | 0 | not observed |
| cem | 0.000 ± 0.000 | 0 | not observed |

Network spikes median [min–max]: 1286.5 [1186–1430]; neurons fired median [min–max]: 33.0 [29–38].

### s0_b0_w180_i0

| readout (Body_ID where individual) | Hz | positive trials / 30 | latency median ms |
| --- | --- | --- | --- |
| L | 0.000 ± 0.000 | 0 | not observed |
| R | 0.000 ± 0.000 | 0 | not observed |
| mn11d_11269 | 0.000 ± 0.000 | 0 | not observed |
| mn11d_11393 | 0.000 ± 0.000 | 0 | not observed |
| mn11d_551398 | 0.000 ± 0.000 | 0 | not observed |
| mn11d | 0.000 ± 0.000 | 0 | not observed |
| mn11v_49829 | 0.000 ± 0.000 | 0 | not observed |
| mn11v_492462351 | 0.000 ± 0.000 | 0 | not observed |
| mn11v | 0.000 ± 0.000 | 0 | not observed |
| cem_19823 | 0.000 ± 0.000 | 0 | not observed |
| cem_20518 | 0.000 ± 0.000 | 0 | not observed |
| cem_23511 | 0.000 ± 0.000 | 0 | not observed |
| cem_32852 | 0.000 ± 0.000 | 0 | not observed |
| cem_34597 | 0.000 ± 0.000 | 0 | not observed |
| cem_482595 | 0.000 ± 0.000 | 0 | not observed |
| cem | 0.000 ± 0.000 | 0 | not observed |

Network spikes median [min–max]: 4475.0 [4270–4615]; neurons fired median [min–max]: 68.0 [67–72].

### s0_b0_w240_i0

| readout (Body_ID where individual) | Hz | positive trials / 30 | latency median ms |
| --- | --- | --- | --- |
| L | 0.000 ± 0.000 | 0 | not observed |
| R | 0.000 ± 0.000 | 0 | not observed |
| mn11d_11269 | 0.000 ± 0.000 | 0 | not observed |
| mn11d_11393 | 0.000 ± 0.000 | 0 | not observed |
| mn11d_551398 | 0.000 ± 0.000 | 0 | not observed |
| mn11d | 0.000 ± 0.000 | 0 | not observed |
| mn11v_49829 | 0.000 ± 0.000 | 0 | not observed |
| mn11v_492462351 | 0.000 ± 0.000 | 0 | not observed |
| mn11v | 0.000 ± 0.000 | 0 | not observed |
| cem_19823 | 0.000 ± 0.000 | 0 | not observed |
| cem_20518 | 0.000 ± 0.000 | 0 | not observed |
| cem_23511 | 0.000 ± 0.000 | 0 | not observed |
| cem_32852 | 0.000 ± 0.000 | 0 | not observed |
| cem_34597 | 0.000 ± 0.000 | 0 | not observed |
| cem_482595 | 0.000 ± 0.000 | 0 | not observed |
| cem | 0.000 ± 0.000 | 0 | not observed |

Network spikes median [min–max]: 6005.5 [5784–6132]; neurons fired median [min–max]: 83.0 [75–120].

### s60_b0_w60_i0

| readout (Body_ID where individual) | Hz | positive trials / 30 | latency median ms |
| --- | --- | --- | --- |
| L | 11.867 ± 4.349 | 30 | 94.4 |
| R | 0.000 ± 0.000 | 0 | not observed |
| mn11d_11269 | 0.000 ± 0.000 | 0 | not observed |
| mn11d_11393 | 0.000 ± 0.000 | 0 | not observed |
| mn11d_551398 | 0.000 ± 0.000 | 0 | not observed |
| mn11d | 0.000 ± 0.000 | 0 | not observed |
| mn11v_49829 | 0.000 ± 0.000 | 0 | not observed |
| mn11v_492462351 | 0.000 ± 0.000 | 0 | not observed |
| mn11v | 0.000 ± 0.000 | 0 | not observed |
| cem_19823 | 0.000 ± 0.000 | 0 | not observed |
| cem_20518 | 0.000 ± 0.000 | 0 | not observed |
| cem_23511 | 0.000 ± 0.000 | 0 | not observed |
| cem_32852 | 0.000 ± 0.000 | 0 | not observed |
| cem_34597 | 0.000 ± 0.000 | 0 | not observed |
| cem_482595 | 0.000 ± 0.000 | 0 | not observed |
| cem | 0.000 ± 0.000 | 0 | not observed |

Network spikes median [min–max]: 7268.0 [6519–8597]; neurons fired median [min–max]: 499.0 [307–684].

### s60_b0_w180_i0

| readout (Body_ID where individual) | Hz | positive trials / 30 | latency median ms |
| --- | --- | --- | --- |
| L | 5.767 ± 2.276 | 30 | 136.65 |
| R | 0.000 ± 0.000 | 0 | not observed |
| mn11d_11269 | 0.000 ± 0.000 | 0 | not observed |
| mn11d_11393 | 0.000 ± 0.000 | 0 | not observed |
| mn11d_551398 | 0.000 ± 0.000 | 0 | not observed |
| mn11d | 0.000 ± 0.000 | 0 | not observed |
| mn11v_49829 | 0.000 ± 0.000 | 0 | not observed |
| mn11v_492462351 | 0.000 ± 0.000 | 0 | not observed |
| mn11v | 0.000 ± 0.000 | 0 | not observed |
| cem_19823 | 0.000 ± 0.000 | 0 | not observed |
| cem_20518 | 0.000 ± 0.000 | 0 | not observed |
| cem_23511 | 0.000 ± 0.000 | 0 | not observed |
| cem_32852 | 0.000 ± 0.000 | 0 | not observed |
| cem_34597 | 0.000 ± 0.000 | 0 | not observed |
| cem_482595 | 0.000 ± 0.000 | 0 | not observed |
| cem | 0.000 ± 0.000 | 0 | not observed |

Network spikes median [min–max]: 9775.5 [9094–10781]; neurons fired median [min–max]: 310.0 [262–584].

### s60_b0_w240_i0

| readout (Body_ID where individual) | Hz | positive trials / 30 | latency median ms |
| --- | --- | --- | --- |
| L | 5.200 ± 2.227 | 30 | 157.40000000000003 |
| R | 0.000 ± 0.000 | 0 | not observed |
| mn11d_11269 | 1.267 ± 1.093 | 21 | 361.3 |
| mn11d_11393 | 1.300 ± 1.130 | 21 | 358.50000000000006 |
| mn11d_551398 | 0.000 ± 0.000 | 0 | not observed |
| mn11d | 0.856 ± 0.739 | 21 | 358.50000000000006 |
| mn11v_49829 | 0.000 ± 0.000 | 0 | not observed |
| mn11v_492462351 | 0.000 ± 0.000 | 0 | not observed |
| mn11v | 0.000 ± 0.000 | 0 | not observed |
| cem_19823 | 0.000 ± 0.000 | 0 | not observed |
| cem_20518 | 0.000 ± 0.000 | 0 | not observed |
| cem_23511 | 0.000 ± 0.000 | 0 | not observed |
| cem_32852 | 0.000 ± 0.000 | 0 | not observed |
| cem_34597 | 0.000 ± 0.000 | 0 | not observed |
| cem_482595 | 0.000 ± 0.000 | 0 | not observed |
| cem | 0.000 ± 0.000 | 0 | not observed |

Network spikes median [min–max]: 11119.5 [10334–11955]; neurons fired median [min–max]: 323.0 [269–647].

### s80_b0_w60_i0

| readout (Body_ID where individual) | Hz | positive trials / 30 | latency median ms |
| --- | --- | --- | --- |
| L | 34.800 ± 10.111 | 30 | 64.80000000000001 |
| R | 0.000 ± 0.000 | 0 | not observed |
| mn11d_11269 | 0.033 ± 0.180 | 1 | 945.7 |
| mn11d_11393 | 0.033 ± 0.180 | 1 | 946.8000000000001 |
| mn11d_551398 | 0.000 ± 0.000 | 0 | not observed |
| mn11d | 0.022 ± 0.120 | 1 | 945.7 |
| mn11v_49829 | 0.000 ± 0.000 | 0 | not observed |
| mn11v_492462351 | 0.000 ± 0.000 | 0 | not observed |
| mn11v | 0.000 ± 0.000 | 0 | not observed |
| cem_19823 | 0.000 ± 0.000 | 0 | not observed |
| cem_20518 | 0.000 ± 0.000 | 0 | not observed |
| cem_23511 | 0.000 ± 0.000 | 0 | not observed |
| cem_32852 | 0.000 ± 0.000 | 0 | not observed |
| cem_34597 | 0.000 ± 0.000 | 0 | not observed |
| cem_482595 | 0.000 ± 0.000 | 0 | not observed |
| cem | 0.000 ± 0.000 | 0 | not observed |

Network spikes median [min–max]: 11756.0 [8971–14237]; neurons fired median [min–max]: 772.5 [678–927].

### s80_b0_w180_i0

| readout (Body_ID where individual) | Hz | positive trials / 30 | latency median ms |
| --- | --- | --- | --- |
| L | 16.300 ± 4.458 | 30 | 79.10000000000001 |
| R | 0.000 ± 0.000 | 0 | not observed |
| mn11d_11269 | 0.400 ± 0.490 | 12 | 475.00000000000006 |
| mn11d_11393 | 0.667 ± 0.650 | 17 | 486.50000000000006 |
| mn11d_551398 | 0.000 ± 0.000 | 0 | not observed |
| mn11d | 0.356 ± 0.354 | 17 | 486.50000000000006 |
| mn11v_49829 | 0.000 ± 0.000 | 0 | not observed |
| mn11v_492462351 | 0.000 ± 0.000 | 0 | not observed |
| mn11v | 0.000 ± 0.000 | 0 | not observed |
| cem_19823 | 0.000 ± 0.000 | 0 | not observed |
| cem_20518 | 0.000 ± 0.000 | 0 | not observed |
| cem_23511 | 0.000 ± 0.000 | 0 | not observed |
| cem_32852 | 0.000 ± 0.000 | 0 | not observed |
| cem_34597 | 0.000 ± 0.000 | 0 | not observed |
| cem_482595 | 0.000 ± 0.000 | 0 | not observed |
| cem | 0.000 ± 0.000 | 0 | not observed |

Network spikes median [min–max]: 12209.0 [11098–14087]; neurons fired median [min–max]: 655.5 [413–758].

### s80_b0_w240_i0

| readout (Body_ID where individual) | Hz | positive trials / 30 | latency median ms |
| --- | --- | --- | --- |
| L | 16.867 ± 4.425 | 30 | 90.05000000000001 |
| R | 0.000 ± 0.000 | 0 | not observed |
| mn11d_11269 | 4.567 ± 1.627 | 30 | 178.15000000000003 |
| mn11d_11393 | 4.867 ± 1.565 | 30 | 172.3 |
| mn11d_551398 | 0.000 ± 0.000 | 0 | not observed |
| mn11d | 3.144 ± 1.053 | 30 | 172.3 |
| mn11v_49829 | 0.000 ± 0.000 | 0 | not observed |
| mn11v_492462351 | 0.000 ± 0.000 | 0 | not observed |
| mn11v | 0.000 ± 0.000 | 0 | not observed |
| cem_19823 | 0.000 ± 0.000 | 0 | not observed |
| cem_20518 | 0.000 ± 0.000 | 0 | not observed |
| cem_23511 | 0.000 ± 0.000 | 0 | not observed |
| cem_32852 | 0.000 ± 0.000 | 0 | not observed |
| cem_34597 | 0.000 ± 0.000 | 0 | not observed |
| cem_482595 | 0.000 ± 0.000 | 0 | not observed |
| cem | 0.000 ± 0.000 | 0 | not observed |

Network spikes median [min–max]: 13483.0 [12629–15178]; neurons fired median [min–max]: 652.5 [401–883].

### s120_b0_w60_i0

| readout (Body_ID where individual) | Hz | positive trials / 30 | latency median ms |
| --- | --- | --- | --- |
| L | 77.167 ± 8.000 | 30 | 50.75 |
| R | 0.000 ± 0.000 | 0 | not observed |
| mn11d_11269 | 34.067 ± 23.439 | 30 | 197.0 |
| mn11d_11393 | 35.267 ± 24.376 | 30 | 197.65 |
| mn11d_551398 | 3.733 ± 3.162 | 21 | 409.40000000000003 |
| mn11d | 24.356 ± 16.957 | 30 | 196.85000000000002 |
| mn11v_49829 | 11.400 ± 10.105 | 22 | 435.05 |
| mn11v_492462351 | 1.000 ± 0.966 | 19 | 535.4 |
| mn11v | 6.200 ± 5.448 | 22 | 435.05 |
| cem_19823 | 0.000 ± 0.000 | 0 | not observed |
| cem_20518 | 1.767 ± 1.476 | 22 | 353.7 |
| cem_23511 | 0.533 ± 0.618 | 14 | 447.20000000000005 |
| cem_32852 | 0.000 ± 0.000 | 0 | not observed |
| cem_34597 | 0.000 ± 0.000 | 0 | not observed |
| cem_482595 | 0.000 ± 0.000 | 0 | not observed |
| cem | 0.383 ± 0.331 | 22 | 353.7 |

Network spikes median [min–max]: 62512.5 [20473–249691]; neurons fired median [min–max]: 7140.5 [956–8236].

### s120_b0_w180_i0

| readout (Body_ID where individual) | Hz | positive trials / 30 | latency median ms |
| --- | --- | --- | --- |
| L | 62.167 ± 6.532 | 30 | 50.05 |
| R | 0.000 ± 0.000 | 0 | not observed |
| mn11d_11269 | 33.467 ± 19.879 | 30 | 127.4 |
| mn11d_11393 | 36.367 ± 20.763 | 30 | 116.25 |
| mn11d_551398 | 2.467 ± 2.604 | 18 | 486.00000000000006 |
| mn11d | 24.100 ± 14.339 | 30 | 116.25 |
| mn11v_49829 | 7.433 ± 7.902 | 18 | 481.29999999999995 |
| mn11v_492462351 | 0.333 ± 0.596 | 8 | 557.2 |
| mn11v | 3.883 ± 4.189 | 18 | 481.29999999999995 |
| cem_19823 | 0.000 ± 0.000 | 0 | not observed |
| cem_20518 | 1.300 ± 1.269 | 20 | 337.90000000000003 |
| cem_23511 | 0.467 ± 0.618 | 12 | 407.15 |
| cem_32852 | 0.000 ± 0.000 | 0 | not observed |
| cem_34597 | 0.000 ± 0.000 | 0 | not observed |
| cem_482595 | 0.000 ± 0.000 | 0 | not observed |
| cem | 0.294 ± 0.300 | 20 | 337.90000000000003 |

Network spikes median [min–max]: 159992.0 [19953–271622]; neurons fired median [min–max]: 7936.5 [876–8243].

### s120_b0_w240_i0

| readout (Body_ID where individual) | Hz | positive trials / 30 | latency median ms |
| --- | --- | --- | --- |
| L | 61.333 ± 6.987 | 30 | 51.45 |
| R | 0.000 ± 0.000 | 0 | not observed |
| mn11d_11269 | 39.933 ± 17.694 | 30 | 83.85000000000001 |
| mn11d_11393 | 42.100 ± 18.580 | 30 | 75.15 |
| mn11d_551398 | 2.733 ± 2.620 | 18 | 259.25 |
| mn11d | 28.256 ± 12.911 | 30 | 75.15 |
| mn11v_49829 | 7.733 ± 7.598 | 18 | 255.60000000000002 |
| mn11v_492462351 | 0.467 ± 0.670 | 12 | 306.35 |
| mn11v | 4.100 ± 4.069 | 18 | 255.60000000000002 |
| cem_19823 | 0.000 ± 0.000 | 0 | not observed |
| cem_20518 | 1.567 ± 1.687 | 20 | 227.7 |
| cem_23511 | 0.600 ± 0.841 | 14 | 245.35000000000002 |
| cem_32852 | 0.000 ± 0.000 | 0 | not observed |
| cem_34597 | 0.000 ± 0.000 | 0 | not observed |
| cem_482595 | 0.000 ± 0.000 | 0 | not observed |
| cem | 0.361 ± 0.406 | 20 | 227.7 |

Network spikes median [min–max]: 176603.5 [22153–319752]; neurons fired median [min–max]: 7832.5 [1004–8230].

### s200_b0_w60_i0

| readout (Body_ID where individual) | Hz | positive trials / 30 | latency median ms |
| --- | --- | --- | --- |
| L | 96.433 ± 4.470 | 30 | 37.5 |
| R | 0.000 ± 0.000 | 0 | not observed |
| mn11d_11269 | 83.100 ± 27.724 | 30 | 75.45 |
| mn11d_11393 | 88.033 ± 29.325 | 30 | 73.7 |
| mn11d_551398 | 9.400 ± 6.317 | 28 | 181.9 |
| mn11d | 60.178 ± 21.032 | 30 | 73.7 |
| mn11v_49829 | 28.467 ± 18.507 | 28 | 176.10000000000002 |
| mn11v_492462351 | 2.167 ± 2.051 | 21 | 261.2 |
| mn11v | 15.317 ± 10.187 | 28 | 176.10000000000002 |
| cem_19823 | 0.000 ± 0.000 | 0 | not observed |
| cem_20518 | 2.467 ± 1.431 | 28 | 199.8 |
| cem_23511 | 0.800 ± 0.792 | 17 | 191.10000000000002 |
| cem_32852 | 0.000 ± 0.000 | 0 | not observed |
| cem_34597 | 0.000 ± 0.000 | 0 | not observed |
| cem_482595 | 0.000 ± 0.000 | 0 | not observed |
| cem | 0.544 ± 0.341 | 28 | 199.8 |

Network spikes median [min–max]: 330861.0 [293424–337752]; neurons fired median [min–max]: 8124.5 [7683–8291].

### s200_b0_w180_i0

| readout (Body_ID where individual) | Hz | positive trials / 30 | latency median ms |
| --- | --- | --- | --- |
| L | 92.133 ± 5.590 | 30 | 36.25 |
| R | 0.000 ± 0.000 | 0 | not observed |
| mn11d_11269 | 83.433 ± 11.904 | 30 | 59.35000000000001 |
| mn11d_11393 | 89.167 ± 12.809 | 30 | 57.400000000000006 |
| mn11d_551398 | 6.700 ± 3.680 | 30 | 239.95 |
| mn11d | 59.767 ± 9.362 | 30 | 57.400000000000006 |
| mn11v_49829 | 18.667 ± 10.306 | 30 | 235.3 |
| mn11v_492462351 | 1.300 ± 1.038 | 23 | 410.50000000000006 |
| mn11v | 9.983 ± 5.585 | 30 | 235.3 |
| cem_19823 | 0.000 ± 0.000 | 0 | not observed |
| cem_20518 | 4.600 ± 1.645 | 30 | 146.75000000000003 |
| cem_23511 | 1.467 ± 1.024 | 25 | 223.3 |
| cem_32852 | 0.000 ± 0.000 | 0 | not observed |
| cem_34597 | 0.000 ± 0.000 | 0 | not observed |
| cem_482595 | 0.000 ± 0.000 | 0 | not observed |
| cem | 1.011 ± 0.368 | 30 | 146.75000000000003 |

Network spikes median [min–max]: 330341.5 [281597–341096]; neurons fired median [min–max]: 8119.5 [7900–8233].

### s200_b0_w240_i0

| readout (Body_ID where individual) | Hz | positive trials / 30 | latency median ms |
| --- | --- | --- | --- |
| L | 94.133 ± 4.072 | 30 | 36.25000000000001 |
| R | 0.000 ± 0.000 | 0 | not observed |
| mn11d_11269 | 86.400 ± 12.093 | 30 | 54.300000000000004 |
| mn11d_11393 | 91.533 ± 12.994 | 30 | 52.35000000000001 |
| mn11d_551398 | 5.633 ± 3.996 | 27 | 220.0 |
| mn11d | 61.189 ± 9.591 | 30 | 52.35000000000001 |
| mn11v_49829 | 15.800 ± 11.190 | 27 | 212.9 |
| mn11v_492462351 | 0.733 ± 0.814 | 16 | 344.6 |
| mn11v | 8.267 ± 5.853 | 27 | 212.9 |
| cem_19823 | 0.000 ± 0.000 | 0 | not observed |
| cem_20518 | 5.800 ± 1.740 | 30 | 143.35 |
| cem_23511 | 2.000 ± 1.125 | 28 | 213.75 |
| cem_32852 | 0.000 ± 0.000 | 0 | not observed |
| cem_34597 | 0.000 ± 0.000 | 0 | not observed |
| cem_482595 | 0.000 ± 0.000 | 0 | not observed |
| cem | 1.300 ± 0.423 | 30 | 143.35 |

Network spikes median [min–max]: 330847.0 [297132–342792]; neurons fired median [min–max]: 8091.0 [7354–8260].

### s0_b0_w0_i60

| readout (Body_ID where individual) | Hz | positive trials / 30 | latency median ms |
| --- | --- | --- | --- |
| L | 1.300 ± 1.295 | 18 | 588.15 |
| R | 0.000 ± 0.000 | 0 | not observed |
| mn11d_11269 | 0.000 ± 0.000 | 0 | not observed |
| mn11d_11393 | 0.000 ± 0.000 | 0 | not observed |
| mn11d_551398 | 0.000 ± 0.000 | 0 | not observed |
| mn11d | 0.000 ± 0.000 | 0 | not observed |
| mn11v_49829 | 0.000 ± 0.000 | 0 | not observed |
| mn11v_492462351 | 0.000 ± 0.000 | 0 | not observed |
| mn11v | 0.000 ± 0.000 | 0 | not observed |
| cem_19823 | 0.000 ± 0.000 | 0 | not observed |
| cem_20518 | 0.000 ± 0.000 | 0 | not observed |
| cem_23511 | 0.000 ± 0.000 | 0 | not observed |
| cem_32852 | 0.000 ± 0.000 | 0 | not observed |
| cem_34597 | 0.000 ± 0.000 | 0 | not observed |
| cem_482595 | 0.000 ± 0.000 | 0 | not observed |
| cem | 0.000 ± 0.000 | 0 | not observed |

Network spikes median [min–max]: 298894.0 [278322–305240]; neurons fired median [min–max]: 7832.0 [7701–8068].

### s0_b0_w0_i120

| readout (Body_ID where individual) | Hz | positive trials / 30 | latency median ms |
| --- | --- | --- | --- |
| L | 0.867 ± 0.884 | 19 | 566.4 |
| R | 0.000 ± 0.000 | 0 | not observed |
| mn11d_11269 | 0.000 ± 0.000 | 0 | not observed |
| mn11d_11393 | 0.000 ± 0.000 | 0 | not observed |
| mn11d_551398 | 0.000 ± 0.000 | 0 | not observed |
| mn11d | 0.000 ± 0.000 | 0 | not observed |
| mn11v_49829 | 0.000 ± 0.000 | 0 | not observed |
| mn11v_492462351 | 0.000 ± 0.000 | 0 | not observed |
| mn11v | 0.000 ± 0.000 | 0 | not observed |
| cem_19823 | 0.000 ± 0.000 | 0 | not observed |
| cem_20518 | 0.000 ± 0.000 | 0 | not observed |
| cem_23511 | 0.000 ± 0.000 | 0 | not observed |
| cem_32852 | 0.000 ± 0.000 | 0 | not observed |
| cem_34597 | 0.000 ± 0.000 | 0 | not observed |
| cem_482595 | 0.000 ± 0.000 | 0 | not observed |
| cem | 0.000 ± 0.000 | 0 | not observed |

Network spikes median [min–max]: 301499.5 [276205–310045]; neurons fired median [min–max]: 7810.5 [7662–8054].

### s0_b0_w0_i200

| readout (Body_ID where individual) | Hz | positive trials / 30 | latency median ms |
| --- | --- | --- | --- |
| L | 0.500 ± 0.619 | 13 | 559.9000000000001 |
| R | 0.000 ± 0.000 | 0 | not observed |
| mn11d_11269 | 0.000 ± 0.000 | 0 | not observed |
| mn11d_11393 | 0.000 ± 0.000 | 0 | not observed |
| mn11d_551398 | 0.000 ± 0.000 | 0 | not observed |
| mn11d | 0.000 ± 0.000 | 0 | not observed |
| mn11v_49829 | 0.000 ± 0.000 | 0 | not observed |
| mn11v_492462351 | 0.000 ± 0.000 | 0 | not observed |
| mn11v | 0.000 ± 0.000 | 0 | not observed |
| cem_19823 | 0.000 ± 0.000 | 0 | not observed |
| cem_20518 | 0.000 ± 0.000 | 0 | not observed |
| cem_23511 | 0.000 ± 0.000 | 0 | not observed |
| cem_32852 | 0.000 ± 0.000 | 0 | not observed |
| cem_34597 | 0.000 ± 0.000 | 0 | not observed |
| cem_482595 | 0.000 ± 0.000 | 0 | not observed |
| cem | 0.000 ± 0.000 | 0 | not observed |

Network spikes median [min–max]: 303067.5 [291512–315406]; neurons fired median [min–max]: 7837.5 [7566–7992].

### s60_b0_w0_i60

| readout (Body_ID where individual) | Hz | positive trials / 30 | latency median ms |
| --- | --- | --- | --- |
| L | 5.567 ± 2.201 | 30 | 314.45000000000005 |
| R | 0.000 ± 0.000 | 0 | not observed |
| mn11d_11269 | 0.000 ± 0.000 | 0 | not observed |
| mn11d_11393 | 0.000 ± 0.000 | 0 | not observed |
| mn11d_551398 | 0.000 ± 0.000 | 0 | not observed |
| mn11d | 0.000 ± 0.000 | 0 | not observed |
| mn11v_49829 | 0.000 ± 0.000 | 0 | not observed |
| mn11v_492462351 | 0.000 ± 0.000 | 0 | not observed |
| mn11v | 0.000 ± 0.000 | 0 | not observed |
| cem_19823 | 0.000 ± 0.000 | 0 | not observed |
| cem_20518 | 0.000 ± 0.000 | 0 | not observed |
| cem_23511 | 0.000 ± 0.000 | 0 | not observed |
| cem_32852 | 0.000 ± 0.000 | 0 | not observed |
| cem_34597 | 0.000 ± 0.000 | 0 | not observed |
| cem_482595 | 0.000 ± 0.000 | 0 | not observed |
| cem | 0.000 ± 0.000 | 0 | not observed |

Network spikes median [min–max]: 297399.0 [269762–305185]; neurons fired median [min–max]: 7866.5 [7140–8135].

### s60_b0_w0_i120

| readout (Body_ID where individual) | Hz | positive trials / 30 | latency median ms |
| --- | --- | --- | --- |
| L | 4.733 ± 2.220 | 30 | 335.3 |
| R | 0.000 ± 0.000 | 0 | not observed |
| mn11d_11269 | 0.000 ± 0.000 | 0 | not observed |
| mn11d_11393 | 0.000 ± 0.000 | 0 | not observed |
| mn11d_551398 | 0.000 ± 0.000 | 0 | not observed |
| mn11d | 0.000 ± 0.000 | 0 | not observed |
| mn11v_49829 | 0.000 ± 0.000 | 0 | not observed |
| mn11v_492462351 | 0.000 ± 0.000 | 0 | not observed |
| mn11v | 0.000 ± 0.000 | 0 | not observed |
| cem_19823 | 0.000 ± 0.000 | 0 | not observed |
| cem_20518 | 0.000 ± 0.000 | 0 | not observed |
| cem_23511 | 0.000 ± 0.000 | 0 | not observed |
| cem_32852 | 0.000 ± 0.000 | 0 | not observed |
| cem_34597 | 0.000 ± 0.000 | 0 | not observed |
| cem_482595 | 0.000 ± 0.000 | 0 | not observed |
| cem | 0.000 ± 0.000 | 0 | not observed |

Network spikes median [min–max]: 302668.0 [278046–312893]; neurons fired median [min–max]: 7912.5 [7710–8162].

### s60_b0_w0_i200

| readout (Body_ID where individual) | Hz | positive trials / 30 | latency median ms |
| --- | --- | --- | --- |
| L | 3.267 ± 2.159 | 28 | 435.20000000000005 |
| R | 0.000 ± 0.000 | 0 | not observed |
| mn11d_11269 | 0.000 ± 0.000 | 0 | not observed |
| mn11d_11393 | 0.000 ± 0.000 | 0 | not observed |
| mn11d_551398 | 0.000 ± 0.000 | 0 | not observed |
| mn11d | 0.000 ± 0.000 | 0 | not observed |
| mn11v_49829 | 0.000 ± 0.000 | 0 | not observed |
| mn11v_492462351 | 0.000 ± 0.000 | 0 | not observed |
| mn11v | 0.000 ± 0.000 | 0 | not observed |
| cem_19823 | 0.000 ± 0.000 | 0 | not observed |
| cem_20518 | 0.000 ± 0.000 | 0 | not observed |
| cem_23511 | 0.000 ± 0.000 | 0 | not observed |
| cem_32852 | 0.000 ± 0.000 | 0 | not observed |
| cem_34597 | 0.000 ± 0.000 | 0 | not observed |
| cem_482595 | 0.000 ± 0.000 | 0 | not observed |
| cem | 0.000 ± 0.000 | 0 | not observed |

Network spikes median [min–max]: 307943.5 [284008–313862]; neurons fired median [min–max]: 7924.5 [7803–8175].

### s80_b0_w0_i60

| readout (Body_ID where individual) | Hz | positive trials / 30 | latency median ms |
| --- | --- | --- | --- |
| L | 4.233 ± 2.390 | 29 | 351.00000000000006 |
| R | 0.000 ± 0.000 | 0 | not observed |
| mn11d_11269 | 0.000 ± 0.000 | 0 | not observed |
| mn11d_11393 | 0.000 ± 0.000 | 0 | not observed |
| mn11d_551398 | 0.000 ± 0.000 | 0 | not observed |
| mn11d | 0.000 ± 0.000 | 0 | not observed |
| mn11v_49829 | 0.000 ± 0.000 | 0 | not observed |
| mn11v_492462351 | 0.000 ± 0.000 | 0 | not observed |
| mn11v | 0.000 ± 0.000 | 0 | not observed |
| cem_19823 | 0.000 ± 0.000 | 0 | not observed |
| cem_20518 | 0.000 ± 0.000 | 0 | not observed |
| cem_23511 | 0.000 ± 0.000 | 0 | not observed |
| cem_32852 | 0.000 ± 0.000 | 0 | not observed |
| cem_34597 | 0.000 ± 0.000 | 0 | not observed |
| cem_482595 | 0.000 ± 0.000 | 0 | not observed |
| cem | 0.000 ± 0.000 | 0 | not observed |

Network spikes median [min–max]: 299918.5 [263036–312739]; neurons fired median [min–max]: 7869.5 [7197–8106].

### s80_b0_w0_i120

| readout (Body_ID where individual) | Hz | positive trials / 30 | latency median ms |
| --- | --- | --- | --- |
| L | 4.467 ± 2.187 | 29 | 315.5 |
| R | 0.000 ± 0.000 | 0 | not observed |
| mn11d_11269 | 0.000 ± 0.000 | 0 | not observed |
| mn11d_11393 | 0.000 ± 0.000 | 0 | not observed |
| mn11d_551398 | 0.000 ± 0.000 | 0 | not observed |
| mn11d | 0.000 ± 0.000 | 0 | not observed |
| mn11v_49829 | 0.000 ± 0.000 | 0 | not observed |
| mn11v_492462351 | 0.000 ± 0.000 | 0 | not observed |
| mn11v | 0.000 ± 0.000 | 0 | not observed |
| cem_19823 | 0.000 ± 0.000 | 0 | not observed |
| cem_20518 | 0.000 ± 0.000 | 0 | not observed |
| cem_23511 | 0.000 ± 0.000 | 0 | not observed |
| cem_32852 | 0.000 ± 0.000 | 0 | not observed |
| cem_34597 | 0.000 ± 0.000 | 0 | not observed |
| cem_482595 | 0.000 ± 0.000 | 0 | not observed |
| cem | 0.000 ± 0.000 | 0 | not observed |

Network spikes median [min–max]: 305591.5 [284626–313387]; neurons fired median [min–max]: 7887.0 [7775–8118].

### s80_b0_w0_i200

| readout (Body_ID where individual) | Hz | positive trials / 30 | latency median ms |
| --- | --- | --- | --- |
| L | 3.767 ± 1.667 | 30 | 370.1 |
| R | 0.000 ± 0.000 | 0 | not observed |
| mn11d_11269 | 0.000 ± 0.000 | 0 | not observed |
| mn11d_11393 | 0.000 ± 0.000 | 0 | not observed |
| mn11d_551398 | 0.000 ± 0.000 | 0 | not observed |
| mn11d | 0.000 ± 0.000 | 0 | not observed |
| mn11v_49829 | 0.000 ± 0.000 | 0 | not observed |
| mn11v_492462351 | 0.000 ± 0.000 | 0 | not observed |
| mn11v | 0.000 ± 0.000 | 0 | not observed |
| cem_19823 | 0.000 ± 0.000 | 0 | not observed |
| cem_20518 | 0.000 ± 0.000 | 0 | not observed |
| cem_23511 | 0.000 ± 0.000 | 0 | not observed |
| cem_32852 | 0.000 ± 0.000 | 0 | not observed |
| cem_34597 | 0.000 ± 0.000 | 0 | not observed |
| cem_482595 | 0.000 ± 0.000 | 0 | not observed |
| cem | 0.000 ± 0.000 | 0 | not observed |

Network spikes median [min–max]: 307361.0 [286419–315897]; neurons fired median [min–max]: 7919.5 [7749–8139].

### s120_b0_w0_i60

| readout (Body_ID where individual) | Hz | positive trials / 30 | latency median ms |
| --- | --- | --- | --- |
| L | 1.600 ± 1.200 | 26 | 111.5 |
| R | 0.000 ± 0.000 | 0 | not observed |
| mn11d_11269 | 0.000 ± 0.000 | 0 | not observed |
| mn11d_11393 | 0.000 ± 0.000 | 0 | not observed |
| mn11d_551398 | 0.000 ± 0.000 | 0 | not observed |
| mn11d | 0.000 ± 0.000 | 0 | not observed |
| mn11v_49829 | 0.000 ± 0.000 | 0 | not observed |
| mn11v_492462351 | 0.000 ± 0.000 | 0 | not observed |
| mn11v | 0.000 ± 0.000 | 0 | not observed |
| cem_19823 | 0.000 ± 0.000 | 0 | not observed |
| cem_20518 | 0.000 ± 0.000 | 0 | not observed |
| cem_23511 | 0.000 ± 0.000 | 0 | not observed |
| cem_32852 | 0.000 ± 0.000 | 0 | not observed |
| cem_34597 | 0.000 ± 0.000 | 0 | not observed |
| cem_482595 | 0.000 ± 0.000 | 0 | not observed |
| cem | 0.000 ± 0.000 | 0 | not observed |

Network spikes median [min–max]: 301068.5 [261602–309454]; neurons fired median [min–max]: 7956.0 [7130–8142].

### s120_b0_w0_i120

| readout (Body_ID where individual) | Hz | positive trials / 30 | latency median ms |
| --- | --- | --- | --- |
| L | 1.033 ± 1.048 | 19 | 448.3 |
| R | 0.000 ± 0.000 | 0 | not observed |
| mn11d_11269 | 0.000 ± 0.000 | 0 | not observed |
| mn11d_11393 | 0.000 ± 0.000 | 0 | not observed |
| mn11d_551398 | 0.000 ± 0.000 | 0 | not observed |
| mn11d | 0.000 ± 0.000 | 0 | not observed |
| mn11v_49829 | 0.000 ± 0.000 | 0 | not observed |
| mn11v_492462351 | 0.000 ± 0.000 | 0 | not observed |
| mn11v | 0.000 ± 0.000 | 0 | not observed |
| cem_19823 | 0.000 ± 0.000 | 0 | not observed |
| cem_20518 | 0.000 ± 0.000 | 0 | not observed |
| cem_23511 | 0.000 ± 0.000 | 0 | not observed |
| cem_32852 | 0.000 ± 0.000 | 0 | not observed |
| cem_34597 | 0.000 ± 0.000 | 0 | not observed |
| cem_482595 | 0.000 ± 0.000 | 0 | not observed |
| cem | 0.000 ± 0.000 | 0 | not observed |

Network spikes median [min–max]: 302836.0 [276868–323174]; neurons fired median [min–max]: 7908.0 [7696–8161].

### s120_b0_w0_i200

| readout (Body_ID where individual) | Hz | positive trials / 30 | latency median ms |
| --- | --- | --- | --- |
| L | 1.300 ± 1.418 | 20 | 557.8500000000001 |
| R | 0.000 ± 0.000 | 0 | not observed |
| mn11d_11269 | 0.000 ± 0.000 | 0 | not observed |
| mn11d_11393 | 0.000 ± 0.000 | 0 | not observed |
| mn11d_551398 | 0.000 ± 0.000 | 0 | not observed |
| mn11d | 0.000 ± 0.000 | 0 | not observed |
| mn11v_49829 | 0.000 ± 0.000 | 0 | not observed |
| mn11v_492462351 | 0.000 ± 0.000 | 0 | not observed |
| mn11v | 0.000 ± 0.000 | 0 | not observed |
| cem_19823 | 0.000 ± 0.000 | 0 | not observed |
| cem_20518 | 0.000 ± 0.000 | 0 | not observed |
| cem_23511 | 0.000 ± 0.000 | 0 | not observed |
| cem_32852 | 0.000 ± 0.000 | 0 | not observed |
| cem_34597 | 0.000 ± 0.000 | 0 | not observed |
| cem_482595 | 0.000 ± 0.000 | 0 | not observed |
| cem | 0.000 ± 0.000 | 0 | not observed |

Network spikes median [min–max]: 306912.5 [270806–317309]; neurons fired median [min–max]: 7974.5 [7729–8156].

### s200_b0_w0_i60

| readout (Body_ID where individual) | Hz | positive trials / 30 | latency median ms |
| --- | --- | --- | --- |
| L | 6.833 ± 2.491 | 30 | 40.050000000000004 |
| R | 0.000 ± 0.000 | 0 | not observed |
| mn11d_11269 | 0.000 ± 0.000 | 0 | not observed |
| mn11d_11393 | 0.000 ± 0.000 | 0 | not observed |
| mn11d_551398 | 0.000 ± 0.000 | 0 | not observed |
| mn11d | 0.000 ± 0.000 | 0 | not observed |
| mn11v_49829 | 0.000 ± 0.000 | 0 | not observed |
| mn11v_492462351 | 0.000 ± 0.000 | 0 | not observed |
| mn11v | 0.000 ± 0.000 | 0 | not observed |
| cem_19823 | 0.000 ± 0.000 | 0 | not observed |
| cem_20518 | 0.000 ± 0.000 | 0 | not observed |
| cem_23511 | 0.000 ± 0.000 | 0 | not observed |
| cem_32852 | 0.000 ± 0.000 | 0 | not observed |
| cem_34597 | 0.000 ± 0.000 | 0 | not observed |
| cem_482595 | 0.000 ± 0.000 | 0 | not observed |
| cem | 0.000 ± 0.000 | 0 | not observed |

Network spikes median [min–max]: 328363.0 [284846–338060]; neurons fired median [min–max]: 7995.0 [7758–8277].

### s200_b0_w0_i120

| readout (Body_ID where individual) | Hz | positive trials / 30 | latency median ms |
| --- | --- | --- | --- |
| L | 2.233 ± 1.453 | 27 | 193.3 |
| R | 0.000 ± 0.000 | 0 | not observed |
| mn11d_11269 | 0.000 ± 0.000 | 0 | not observed |
| mn11d_11393 | 0.000 ± 0.000 | 0 | not observed |
| mn11d_551398 | 0.000 ± 0.000 | 0 | not observed |
| mn11d | 0.000 ± 0.000 | 0 | not observed |
| mn11v_49829 | 0.000 ± 0.000 | 0 | not observed |
| mn11v_492462351 | 0.000 ± 0.000 | 0 | not observed |
| mn11v | 0.000 ± 0.000 | 0 | not observed |
| cem_19823 | 0.000 ± 0.000 | 0 | not observed |
| cem_20518 | 0.000 ± 0.000 | 0 | not observed |
| cem_23511 | 0.000 ± 0.000 | 0 | not observed |
| cem_32852 | 0.000 ± 0.000 | 0 | not observed |
| cem_34597 | 0.000 ± 0.000 | 0 | not observed |
| cem_482595 | 0.000 ± 0.000 | 0 | not observed |
| cem | 0.000 ± 0.000 | 0 | not observed |

Network spikes median [min–max]: 315737.5 [269260–340310]; neurons fired median [min–max]: 7960.0 [7274–8145].

### s200_b0_w0_i200

| readout (Body_ID where individual) | Hz | positive trials / 30 | latency median ms |
| --- | --- | --- | --- |
| L | 1.267 ± 1.236 | 20 | 457.75 |
| R | 0.000 ± 0.000 | 0 | not observed |
| mn11d_11269 | 0.000 ± 0.000 | 0 | not observed |
| mn11d_11393 | 0.000 ± 0.000 | 0 | not observed |
| mn11d_551398 | 0.000 ± 0.000 | 0 | not observed |
| mn11d | 0.000 ± 0.000 | 0 | not observed |
| mn11v_49829 | 0.000 ± 0.000 | 0 | not observed |
| mn11v_492462351 | 0.000 ± 0.000 | 0 | not observed |
| mn11v | 0.000 ± 0.000 | 0 | not observed |
| cem_19823 | 0.000 ± 0.000 | 0 | not observed |
| cem_20518 | 0.000 ± 0.000 | 0 | not observed |
| cem_23511 | 0.000 ± 0.000 | 0 | not observed |
| cem_32852 | 0.000 ± 0.000 | 0 | not observed |
| cem_34597 | 0.000 ± 0.000 | 0 | not observed |
| cem_482595 | 0.000 ± 0.000 | 0 | not observed |
| cem | 0.000 ± 0.000 | 0 | not observed |

Network spikes median [min–max]: 319484.5 [284855–341515]; neurons fired median [min–max]: 7972.0 [7369–8162].

## Execution and verification

The [runner](../sim/malecns/male_v1_phase1.py) uses a spawn pool, one build per worker, restore before every trial, 1,000 ms duration and 0.1 ms dt; driven inputs have zero refractory and inactive inputs retain 2.2 ms. Existing outputs are refused, with no retry/resume. Sources and the compile-only plan are hashed in the [results](../data/malecns/male_v1_phase1_results.json). The independent [audit](../data/malecns/male_v1_phase1_audit.json) recomputes 1,050 raw trials, all 13 individual readouts, group means, latencies, network/source counts, every Poisson train from its seed/rates/layout, and every summary and derived-table field. [Tests](../sim/malecns/test_male_v1_phase1.py) cover configuration tampering, synthetic corruption, verdict logic and exact report regeneration. Run the report generator with `--check` to verify this entire generated block and the program Phase 1 section; later report sections are preserved.

<!-- male-v1-phase1:end -->
