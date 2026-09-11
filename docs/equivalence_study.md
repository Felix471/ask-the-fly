# Store/restore versus legacy PoissonInput equivalence study

## Existing-run facts

| trial | reusable sugar-only | legacy sugar-only | full sugar+bitter |
|---|---|---|---|
| 0 | 71.0 | 74.0 | 67.0 |
| 1 | 68.0 | 60.0 | 70.0 |
| 2 | 69.0 | 63.0 | 68.0 |
| 3 | 72.0 | 62.0 | 63.0 |
| 4 | 76.0 | 62.0 | 68.0 |
| 5 |  |  | 77.0 |
| 6 |  |  | 68.0 |
| 7 |  |  | 70.0 |
| 8 |  |  | 72.0 |
| 9 |  |  | 69.0 |
| 10 |  |  | 66.0 |
| 11 |  |  | 62.0 |
| 12 |  |  | 67.0 |
| 13 |  |  | 59.0 |
| 14 |  |  | 75.0 |
| 15 |  |  | 62.0 |
| 16 |  |  | 65.0 |
| 17 |  |  | 65.0 |
| 18 |  |  | 72.0 |
| 19 |  |  | 66.0 |
| 20 |  |  | 64.0 |
| 21 |  |  | 68.0 |
| 22 |  |  | 58.0 |
| 23 |  |  | 71.0 |
| 24 |  |  | 72.0 |
| 25 |  |  | 77.0 |
| 26 |  |  | 62.0 |
| 27 |  |  | 68.0 |
| 28 |  |  | 64.0 |
| 29 |  |  | 62.0 |

- **reusable:** n=5; seeds 20260910..20260914; channels=sugar only; mean=71.200, std(ddof=0)=2.786, std(ddof=1)=3.114, SE=1.393 Hz.
- **legacy:** n=5; seeds 20260910..20260914; channels=sugar only; mean=64.200, std(ddof=0)=4.996, std(ddof=1)=5.586, SE=2.498 Hz.
- **full:** n=30; seeds 20262910..20262939; channels=sugar + bitter; mean=67.233, std(ddof=0)=4.724, std(ddof=1)=4.804, SE=0.877 Hz.

The full run's condition index is 2 in `expand_conditions` ordering, hence its +2000 seed offset. Its zero-rate bitter GRNs nevertheless have `rfc=0`; the sugar-only legacy run does not alter them.

## Restore determinism

A == A2: **True**; A == A3: **True**. Totals: {'A': 9794, 'B': 9633, 'A2': 9794, 'A3': 9794}; MN9-left: {'A': 71, 'B': 68, 'A2': 71, 'A3': 71}. Post-restore state all at rest: **True**; values: `{'v_all_at_rest': True, 'g_all_at_rest': True, 'not_refractory_all_true': True, 'lastspike_all_at_rest': True, 'lastspike_initial_s': -10000.0, 'stimulus_rates_all_at_rest': True, 'max_abs_g_mV': 0.0, 'max_abs_v_minus_v0_mV': 0.0, 'not_refractory_false': 0, 'poisson_rates_sum_hz': 0.0}`.

## Matched PoissonGroup trials

| seed | reusable MN9-L | fresh PG MN9-L | paired diff (Hz) | all neurons exact |
|---|---|---|---|---|
| 20260910 | 71.0 | 71.0 | 0.0 | True |
| 20260911 | 68.0 | 68.0 | 0.0 | True |
| 20260912 | 69.0 | 69.0 | 0.0 | True |
| 20260913 | 72.0 | 72.0 | 0.0 | True |
| 20260914 | 76.0 | 76.0 | 0.0 | True |
| 20260915 | 70.0 | 70.0 | 0.0 | True |
| 20260916 | 71.0 | 71.0 | 0.0 | True |
| 20260917 | 69.0 | 69.0 | 0.0 | True |
| 20260918 | 65.0 | 65.0 | 0.0 | True |
| 20260919 | 63.0 | 63.0 | 0.0 | True |

Mean paired MN9-left difference (reusable - fresh): **0.000 Hz**. Exact spike-train equality: **10/10 seeds**.

## Stimulus semantics (30 seeds)

PoissonInput and PoissonGroup consume the RNG differently, so PoissonInput comparisons are distributional despite equal seed labels.

### MN9-left rate (Hz)

| trial | seed | reusable | PoissonInput | fresh PoissonGroup |
|---|---|---|---|---|
| 0 | 20260910 | 71.0 | 74.0 | 71.0 |
| 1 | 20260911 | 68.0 | 60.0 | 68.0 |
| 2 | 20260912 | 69.0 | 63.0 | 69.0 |
| 3 | 20260913 | 72.0 | 62.0 | 72.0 |
| 4 | 20260914 | 76.0 | 62.0 | 76.0 |
| 5 | 20260915 | 70.0 | 61.0 | 70.0 |
| 6 | 20260916 | 71.0 | 64.0 | 71.0 |
| 7 | 20260917 | 69.0 | 68.0 | 69.0 |
| 8 | 20260918 | 65.0 | 62.0 | 65.0 |
| 9 | 20260919 | 63.0 | 69.0 | 63.0 |
| 10 | 20260920 | 68.0 | 61.0 | 68.0 |
| 11 | 20260921 | 59.0 | 69.0 | 59.0 |
| 12 | 20260922 | 60.0 | 62.0 | 60.0 |
| 13 | 20260923 | 65.0 | 72.0 | 65.0 |
| 14 | 20260924 | 65.0 | 67.0 | 65.0 |
| 15 | 20260925 | 72.0 | 71.0 | 72.0 |
| 16 | 20260926 | 70.0 | 71.0 | 70.0 |
| 17 | 20260927 | 68.0 | 59.0 | 68.0 |
| 18 | 20260928 | 73.0 | 59.0 | 73.0 |
| 19 | 20260929 | 71.0 | 67.0 | 71.0 |
| 20 | 20260930 | 69.0 | 61.0 | 69.0 |
| 21 | 20260931 | 73.0 | 64.0 | 73.0 |
| 22 | 20260932 | 64.0 | 63.0 | 64.0 |
| 23 | 20260933 | 72.0 | 70.0 | 72.0 |
| 24 | 20260934 | 72.0 | 68.0 | 72.0 |
| 25 | 20260935 | 65.0 | 65.0 | 65.0 |
| 26 | 20260936 | 61.0 | 69.0 | 61.0 |
| 27 | 20260937 | 63.0 | 67.0 | 63.0 |
| 28 | 20260938 | 68.0 | 72.0 | 68.0 |
| 29 | 20260939 | 67.0 | 69.0 | 67.0 |
| 30 | 20260940 | 65.0 | 65.0 | 65.0 |
| 31 | 20260941 | 66.0 | 65.0 | 66.0 |
| 32 | 20260942 | 57.0 | 64.0 | 57.0 |
| 33 | 20260943 | 65.0 | 63.0 | 65.0 |
| 34 | 20260944 | 64.0 | 70.0 | 64.0 |
| 35 | 20260945 | 67.0 | 75.0 | 67.0 |
| 36 | 20260946 | 59.0 | 63.0 | 59.0 |
| 37 | 20260947 | 70.0 | 66.0 | 70.0 |
| 38 | 20260948 | 57.0 | 61.0 | 57.0 |
| 39 | 20260949 | 66.0 | 62.0 | 66.0 |
| 40 | 20260950 | 64.0 | 73.0 | 64.0 |
| 41 | 20260951 | 62.0 | 74.0 | 62.0 |
| 42 | 20260952 | 62.0 | 64.0 | 62.0 |
| 43 | 20260953 | 63.0 | 71.0 | 63.0 |
| 44 | 20260954 | 77.0 | 71.0 | 77.0 |
| 45 | 20260955 | 71.0 | 60.0 | 71.0 |
| 46 | 20260956 | 69.0 | 62.0 | 69.0 |
| 47 | 20260957 | 62.0 | 71.0 | 62.0 |
| 48 | 20260958 | 66.0 | 68.0 | 66.0 |
| 49 | 20260959 | 62.0 | 66.0 | 62.0 |
| 50 | 20260960 | 69.0 | 70.0 | 69.0 |
| 51 | 20260961 | 70.0 | 70.0 | 70.0 |
| 52 | 20260962 | 69.0 | 76.0 | 69.0 |
| 53 | 20260963 | 65.0 | 68.0 | 65.0 |
| 54 | 20260964 | 65.0 | 72.0 | 65.0 |
| 55 | 20260965 | 70.0 | 67.0 | 70.0 |
| 56 | 20260966 | 63.0 | 67.0 | 63.0 |
| 57 | 20260967 | 60.0 | 65.0 | 60.0 |
| 58 | 20260968 | 79.0 | 76.0 | 79.0 |
| 59 | 20260969 | 67.0 | 73.0 | 67.0 |
| 60 | 20260970 | 69.0 | 69.0 | 69.0 |
| 61 | 20260971 | 62.0 | 60.0 | 62.0 |
| 62 | 20260972 | 62.0 | 69.0 | 62.0 |
| 63 | 20260973 | 57.0 | 70.0 | 57.0 |
| 64 | 20260974 | 72.0 | 62.0 | 72.0 |
| 65 | 20260975 | 70.0 | 68.0 | 70.0 |
| 66 | 20260976 | 77.0 | 67.0 | 77.0 |
| 67 | 20260977 | 63.0 | 64.0 | 63.0 |
| 68 | 20260978 | 71.0 | 59.0 | 71.0 |
| 69 | 20260979 | 63.0 | 61.0 | 63.0 |
| 70 | 20260980 | 60.0 | 79.0 | 60.0 |
| 71 | 20260981 | 73.0 | 74.0 | 73.0 |
| 72 | 20260982 | 63.0 | 65.0 | 63.0 |
| 73 | 20260983 | 63.0 | 65.0 | 63.0 |
| 74 | 20260984 | 59.0 | 59.0 | 59.0 |
| 75 | 20260985 | 60.0 | 68.0 | 60.0 |
| 76 | 20260986 | 67.0 | 67.0 | 67.0 |
| 77 | 20260987 | 75.0 | 64.0 | 75.0 |
| 78 | 20260988 | 63.0 | 67.0 | 63.0 |
| 79 | 20260989 | 69.0 | 79.0 | 69.0 |
| 80 | 20260990 | 61.0 | 66.0 | 61.0 |
| 81 | 20260991 | 62.0 | 63.0 | 62.0 |
| 82 | 20260992 | 66.0 | 63.0 | 66.0 |
| 83 | 20260993 | 72.0 | 66.0 | 72.0 |
| 84 | 20260994 | 58.0 | 77.0 | 58.0 |
| 85 | 20260995 | 70.0 | 62.0 | 70.0 |
| 86 | 20260996 | 54.0 | 72.0 | 54.0 |
| 87 | 20260997 | 64.0 | 67.0 | 64.0 |
| 88 | 20260998 | 67.0 | 66.0 | 67.0 |
| 89 | 20260999 | 62.0 | 67.0 | 62.0 |

| path | mean | std0 | std1 | SE |
|---|---|---|---|---|
| a_reusable | 66.267 | 5.059 | 5.088 | 0.536 |
| b_poissoninput | 66.822 | 4.769 | 4.796 | 0.506 |
| c_fresh_poissongroup | 66.267 | 5.059 | 5.088 | 0.536 |

| comparison | mean diff | 95% CI | Welch t | Welch p | MWU U | MWU p |
|---|---|---|---|---|---|---|
| a_reusable_vs_b_poissoninput | -0.556 | [-2.010, 0.899] | -0.7538091612222019 | 0.451963 | 3871.500 | 0.609845 |
| c_fresh_poissongroup_vs_b_poissoninput | -0.556 | [-2.010, 0.899] | -0.7538091612222019 | 0.451963 | 3871.500 | 0.609845 |
| a_reusable_vs_c_fresh_poissongroup | 0.000 | [-1.497, 1.497] | 0.0 | 1 | 4050.000 | 1 |

### MN9-right rate (Hz)

| trial | seed | reusable | PoissonInput | fresh PoissonGroup |
|---|---|---|---|---|
| 0 | 20260910 | 54.0 | 62.0 | 54.0 |
| 1 | 20260911 | 50.0 | 49.0 | 50.0 |
| 2 | 20260912 | 51.0 | 43.0 | 51.0 |
| 3 | 20260913 | 51.0 | 53.0 | 51.0 |
| 4 | 20260914 | 56.0 | 49.0 | 56.0 |
| 5 | 20260915 | 53.0 | 47.0 | 53.0 |
| 6 | 20260916 | 58.0 | 40.0 | 58.0 |
| 7 | 20260917 | 45.0 | 51.0 | 45.0 |
| 8 | 20260918 | 48.0 | 45.0 | 48.0 |
| 9 | 20260919 | 46.0 | 47.0 | 46.0 |
| 10 | 20260920 | 54.0 | 46.0 | 54.0 |
| 11 | 20260921 | 48.0 | 53.0 | 48.0 |
| 12 | 20260922 | 44.0 | 46.0 | 44.0 |
| 13 | 20260923 | 51.0 | 56.0 | 51.0 |
| 14 | 20260924 | 44.0 | 47.0 | 44.0 |
| 15 | 20260925 | 45.0 | 56.0 | 45.0 |
| 16 | 20260926 | 53.0 | 57.0 | 53.0 |
| 17 | 20260927 | 54.0 | 48.0 | 54.0 |
| 18 | 20260928 | 50.0 | 45.0 | 50.0 |
| 19 | 20260929 | 52.0 | 47.0 | 52.0 |
| 20 | 20260930 | 47.0 | 45.0 | 47.0 |
| 21 | 20260931 | 54.0 | 44.0 | 54.0 |
| 22 | 20260932 | 48.0 | 43.0 | 48.0 |
| 23 | 20260933 | 53.0 | 50.0 | 53.0 |
| 24 | 20260934 | 53.0 | 48.0 | 53.0 |
| 25 | 20260935 | 53.0 | 46.0 | 53.0 |
| 26 | 20260936 | 46.0 | 45.0 | 46.0 |
| 27 | 20260937 | 47.0 | 52.0 | 47.0 |
| 28 | 20260938 | 45.0 | 55.0 | 45.0 |
| 29 | 20260939 | 50.0 | 52.0 | 50.0 |
| 30 | 20260940 | 47.0 | 50.0 | 47.0 |
| 31 | 20260941 | 49.0 | 48.0 | 49.0 |
| 32 | 20260942 | 43.0 | 45.0 | 43.0 |
| 33 | 20260943 | 51.0 | 48.0 | 51.0 |
| 34 | 20260944 | 48.0 | 46.0 | 48.0 |
| 35 | 20260945 | 48.0 | 56.0 | 48.0 |
| 36 | 20260946 | 46.0 | 53.0 | 46.0 |
| 37 | 20260947 | 51.0 | 45.0 | 51.0 |
| 38 | 20260948 | 48.0 | 44.0 | 48.0 |
| 39 | 20260949 | 45.0 | 46.0 | 45.0 |
| 40 | 20260950 | 47.0 | 48.0 | 47.0 |
| 41 | 20260951 | 44.0 | 58.0 | 44.0 |
| 42 | 20260952 | 49.0 | 48.0 | 49.0 |
| 43 | 20260953 | 51.0 | 49.0 | 51.0 |
| 44 | 20260954 | 54.0 | 42.0 | 54.0 |
| 45 | 20260955 | 57.0 | 53.0 | 57.0 |
| 46 | 20260956 | 56.0 | 56.0 | 56.0 |
| 47 | 20260957 | 42.0 | 51.0 | 42.0 |
| 48 | 20260958 | 43.0 | 44.0 | 43.0 |
| 49 | 20260959 | 52.0 | 45.0 | 52.0 |
| 50 | 20260960 | 49.0 | 51.0 | 49.0 |
| 51 | 20260961 | 47.0 | 50.0 | 47.0 |
| 52 | 20260962 | 44.0 | 50.0 | 44.0 |
| 53 | 20260963 | 46.0 | 48.0 | 46.0 |
| 54 | 20260964 | 47.0 | 54.0 | 47.0 |
| 55 | 20260965 | 56.0 | 45.0 | 56.0 |
| 56 | 20260966 | 47.0 | 45.0 | 47.0 |
| 57 | 20260967 | 47.0 | 45.0 | 47.0 |
| 58 | 20260968 | 60.0 | 48.0 | 60.0 |
| 59 | 20260969 | 50.0 | 52.0 | 50.0 |
| 60 | 20260970 | 41.0 | 46.0 | 41.0 |
| 61 | 20260971 | 42.0 | 46.0 | 42.0 |
| 62 | 20260972 | 40.0 | 56.0 | 40.0 |
| 63 | 20260973 | 43.0 | 53.0 | 43.0 |
| 64 | 20260974 | 52.0 | 45.0 | 52.0 |
| 65 | 20260975 | 49.0 | 47.0 | 49.0 |
| 66 | 20260976 | 55.0 | 47.0 | 55.0 |
| 67 | 20260977 | 51.0 | 46.0 | 51.0 |
| 68 | 20260978 | 53.0 | 49.0 | 53.0 |
| 69 | 20260979 | 46.0 | 44.0 | 46.0 |
| 70 | 20260980 | 50.0 | 56.0 | 50.0 |
| 71 | 20260981 | 50.0 | 52.0 | 50.0 |
| 72 | 20260982 | 48.0 | 55.0 | 48.0 |
| 73 | 20260983 | 49.0 | 47.0 | 49.0 |
| 74 | 20260984 | 43.0 | 44.0 | 43.0 |
| 75 | 20260985 | 45.0 | 49.0 | 45.0 |
| 76 | 20260986 | 44.0 | 48.0 | 44.0 |
| 77 | 20260987 | 55.0 | 49.0 | 55.0 |
| 78 | 20260988 | 48.0 | 54.0 | 48.0 |
| 79 | 20260989 | 48.0 | 48.0 | 48.0 |
| 80 | 20260990 | 46.0 | 43.0 | 46.0 |
| 81 | 20260991 | 47.0 | 47.0 | 47.0 |
| 82 | 20260992 | 52.0 | 50.0 | 52.0 |
| 83 | 20260993 | 56.0 | 46.0 | 56.0 |
| 84 | 20260994 | 45.0 | 56.0 | 45.0 |
| 85 | 20260995 | 52.0 | 49.0 | 52.0 |
| 86 | 20260996 | 43.0 | 57.0 | 43.0 |
| 87 | 20260997 | 46.0 | 46.0 | 46.0 |
| 88 | 20260998 | 48.0 | 56.0 | 48.0 |
| 89 | 20260999 | 45.0 | 47.0 | 45.0 |

| path | mean | std0 | std1 | SE |
|---|---|---|---|---|
| a_reusable | 48.878 | 4.219 | 4.242 | 0.447 |
| b_poissoninput | 48.978 | 4.346 | 4.370 | 0.461 |
| c_fresh_poissongroup | 48.878 | 4.219 | 4.242 | 0.447 |

| comparison | mean diff | 95% CI | Welch t | Welch p | MWU U | MWU p |
|---|---|---|---|---|---|---|
| a_reusable_vs_b_poissoninput | -0.100 | [-1.367, 1.167] | -0.15575905345762725 | 0.8764 | 4074.000 | 0.946239 |
| c_fresh_poissongroup_vs_b_poissoninput | -0.100 | [-1.367, 1.167] | -0.15575905345762725 | 0.8764 | 4074.000 | 0.946239 |
| a_reusable_vs_c_fresh_poissongroup | 0.000 | [-1.248, 1.248] | 0.0 | 1 | 4050.000 | 1 |

### network-wide spike count

| trial | seed | reusable | PoissonInput | fresh PoissonGroup |
|---|---|---|---|---|
| 0 | 20260910 | 9794 | 10660 | 9794 |
| 1 | 20260911 | 9633 | 9039 | 9633 |
| 2 | 20260912 | 10060 | 9348 | 10060 |
| 3 | 20260913 | 9993 | 9702 | 9993 |
| 4 | 20260914 | 9963 | 9584 | 9963 |
| 5 | 20260915 | 10308 | 9631 | 10308 |
| 6 | 20260916 | 10048 | 8966 | 10048 |
| 7 | 20260917 | 9465 | 9389 | 9465 |
| 8 | 20260918 | 9867 | 9721 | 9867 |
| 9 | 20260919 | 9487 | 9982 | 9487 |
| 10 | 20260920 | 10176 | 9901 | 10176 |
| 11 | 20260921 | 9286 | 9630 | 9286 |
| 12 | 20260922 | 9140 | 9570 | 9140 |
| 13 | 20260923 | 9452 | 10261 | 9452 |
| 14 | 20260924 | 9686 | 9983 | 9686 |
| 15 | 20260925 | 10026 | 10310 | 10026 |
| 16 | 20260926 | 9552 | 9911 | 9552 |
| 17 | 20260927 | 9841 | 9415 | 9841 |
| 18 | 20260928 | 9806 | 9290 | 9806 |
| 19 | 20260929 | 9612 | 9702 | 9612 |
| 20 | 20260930 | 9641 | 9347 | 9641 |
| 21 | 20260931 | 9963 | 9766 | 9963 |
| 22 | 20260932 | 9975 | 9266 | 9975 |
| 23 | 20260933 | 10331 | 9901 | 10331 |
| 24 | 20260934 | 9867 | 10088 | 9867 |
| 25 | 20260935 | 9465 | 9567 | 9465 |
| 26 | 20260936 | 9803 | 9614 | 9803 |
| 27 | 20260937 | 10089 | 9545 | 10089 |
| 28 | 20260938 | 9654 | 10114 | 9654 |
| 29 | 20260939 | 9374 | 9876 | 9374 |
| 30 | 20260940 | 9446 | 9416 | 9446 |
| 31 | 20260941 | 9655 | 9379 | 9655 |
| 32 | 20260942 | 8998 | 9229 | 8998 |
| 33 | 20260943 | 9685 | 9515 | 9685 |
| 34 | 20260944 | 10025 | 9946 | 10025 |
| 35 | 20260945 | 9737 | 9896 | 9737 |
| 36 | 20260946 | 9241 | 9442 | 9241 |
| 37 | 20260947 | 10218 | 9915 | 10218 |
| 38 | 20260948 | 9188 | 9793 | 9188 |
| 39 | 20260949 | 9743 | 9314 | 9743 |
| 40 | 20260950 | 9669 | 9861 | 9669 |
| 41 | 20260951 | 9045 | 10010 | 9045 |
| 42 | 20260952 | 9673 | 9839 | 9673 |
| 43 | 20260953 | 9647 | 9506 | 9647 |
| 44 | 20260954 | 9872 | 9776 | 9872 |
| 45 | 20260955 | 9682 | 9651 | 9682 |
| 46 | 20260956 | 10154 | 9733 | 10154 |
| 47 | 20260957 | 9537 | 9839 | 9537 |
| 48 | 20260958 | 9518 | 9298 | 9518 |
| 49 | 20260959 | 9198 | 9548 | 9198 |
| 50 | 20260960 | 9704 | 10039 | 9704 |
| 51 | 20260961 | 10000 | 9854 | 10000 |
| 52 | 20260962 | 10261 | 9838 | 10261 |
| 53 | 20260963 | 9649 | 9448 | 9649 |
| 54 | 20260964 | 9327 | 9660 | 9327 |
| 55 | 20260965 | 9409 | 9638 | 9409 |
| 56 | 20260966 | 9739 | 9609 | 9739 |
| 57 | 20260967 | 9348 | 9743 | 9348 |
| 58 | 20260968 | 10595 | 10159 | 10595 |
| 59 | 20260969 | 9753 | 9358 | 9753 |
| 60 | 20260970 | 10019 | 9036 | 10019 |
| 61 | 20260971 | 8791 | 9150 | 8791 |
| 62 | 20260972 | 9557 | 9958 | 9557 |
| 63 | 20260973 | 9566 | 9730 | 9566 |
| 64 | 20260974 | 10026 | 9164 | 10026 |
| 65 | 20260975 | 9716 | 9458 | 9716 |
| 66 | 20260976 | 9707 | 9511 | 9707 |
| 67 | 20260977 | 9880 | 9275 | 9880 |
| 68 | 20260978 | 10325 | 8668 | 10325 |
| 69 | 20260979 | 9169 | 9652 | 9169 |
| 70 | 20260980 | 9544 | 10477 | 9544 |
| 71 | 20260981 | 9808 | 9724 | 9808 |
| 72 | 20260982 | 9866 | 9701 | 9866 |
| 73 | 20260983 | 9779 | 9544 | 9779 |
| 74 | 20260984 | 9433 | 9654 | 9433 |
| 75 | 20260985 | 9287 | 9349 | 9287 |
| 76 | 20260986 | 9702 | 9762 | 9702 |
| 77 | 20260987 | 9796 | 9770 | 9796 |
| 78 | 20260988 | 9473 | 10487 | 9473 |
| 79 | 20260989 | 9200 | 9376 | 9200 |
| 80 | 20260990 | 9234 | 9591 | 9234 |
| 81 | 20260991 | 9501 | 9723 | 9501 |
| 82 | 20260992 | 9523 | 9421 | 9523 |
| 83 | 20260993 | 10224 | 9396 | 10224 |
| 84 | 20260994 | 9756 | 10555 | 9756 |
| 85 | 20260995 | 9571 | 8936 | 9571 |
| 86 | 20260996 | 9075 | 10410 | 9075 |
| 87 | 20260997 | 9587 | 9817 | 9587 |
| 88 | 20260998 | 9741 | 9804 | 9741 |
| 89 | 20260999 | 9768 | 9206 | 9768 |

| path | mean | std0 | std1 | SE |
|---|---|---|---|---|
| a_reusable | 9685.522 | 334.702 | 336.577 | 35.478 |
| b_poissoninput | 9662.622 | 364.178 | 366.219 | 38.603 |
| c_fresh_poissongroup | 9685.522 | 334.702 | 336.577 | 35.478 |

| comparison | mean diff | 95% CI | Welch t | Welch p | MWU U | MWU p |
|---|---|---|---|---|---|---|
| a_reusable_vs_b_poissoninput | 22.900 | [-80.569, 126.369] | 0.43677391747473165 | 0.662808 | 4272.500 | 0.525341 |
| c_fresh_poissongroup_vs_b_poissoninput | 22.900 | [-80.569, 126.369] | 0.43677391747473165 | 0.662808 | 4272.500 | 0.525341 |
| a_reusable_vs_c_fresh_poissongroup | 0.000 | [-99.012, 99.012] | 0.0 | 1 | 4050.000 | 1 |

## Refractory quirk (10 matched seeds)

Three builds per seed, sugar 100 Hz: (a) sugar+bitter stimulus group with the old build-time `rfc=0` for both channels; (b) sugar-only stimulus group (bitter GRNs absent, rfc untouched); (c) the same sugar+bitter stimulus group as (a) with the per-channel rule (rfc=0 only for the driven channel). (a) and (c) consume an identical random stream, so (a)-(c) is the pure effect of the refractory rule; (a)-(b) also changes the stimulus group size and therefore the random draws.

| seed | (a) old rule MN9-L | (b) sugar-only MN9-L | (a)-(b) | (a) vs (b) all-neuron exact | (c) per-channel rule MN9-L | (a)-(c) pure refractory | (a) vs (c) all-neuron exact |
|---|---|---|---|---|---|---|---|
| 20260910 | 73 | 71 | 2 | False | 73 | 0 | True |
| 20260911 | 68 | 68 | 0 | False | 68 | 0 | True |
| 20260912 | 72 | 69 | 3 | False | 72 | 0 | True |
| 20260913 | 74 | 72 | 2 | False | 74 | 0 | True |
| 20260914 | 56 | 76 | -20 | False | 56 | 0 | True |
| 20260915 | 69 | 70 | -1 | False | 69 | 0 | True |
| 20260916 | 51 | 71 | -20 | False | 51 | 0 | True |
| 20260917 | 64 | 69 | -5 | False | 64 | 0 | True |
| 20260918 | 62 | 65 | -3 | False | 62 | 0 | True |
| 20260919 | 64 | 63 | 1 | False | 64 | 0 | True |

Different-stream comparison (a)-(b): mean paired count difference **-4.100 spikes/trial**; exact all-neuron spike trains **0/10 seeds**.

Same-random-stream comparison (a)-(c): mean pure refractory difference **0.000 spikes/trial**; exact all-neuron spike trains **10/10 seeds**.

The refractory rule has **zero measured effect**: with the random stream held fixed, the old build-time rule and the per-channel rule are spike-for-spike identical on every seed, so the undriven bitter GRNs never fired in this condition. The (a)-(b) difference is entirely the changed random stream (stimulus PoissonGroup of 65 versus 23 neurons), not the refractory rule. The per-channel rule is kept for fidelity to model.py; differences between pre-fix and fixed runs are sampling noise from different streams and must not be attributed to the rule.

## Semantic differences identified

- Reusable/fresh-PG use one `PoissonGroup` neuron per target plus one-to-one `Synapses(on_pre='v += w_stim')`; legacy uses one `PoissonInput(N=1)` per target.
- Before the fix, reusable construction set `rfc=0` for every neuron belonging to every built channel, even a channel run at 0 Hz. Legacy changes `rfc` only for channels passed into that fresh build; the study passes sugar only. The reusable path now applies rfc=0 per trial only to channels with a nonzero rate (measured effect: zero, see the refractory section).
- Reusable restores, sets rates, then calls `brian2.seed` immediately before running. Fresh paths construct and set rates first, then seed immediately before running.
- Reusable network membership includes the PoissonGroup and stimulus Synapses; legacy membership instead includes all PoissonInput objects. Fresh-PG matches reusable membership.
- Reusable retains one SpikeMonitor and relies on `restore('init')` to clear it; both legacy paths allocate a new monitor for every trial.
- Reusable restores neuron state, refractory bookkeeping, synaptic queues, monitor state, and network time; fresh paths obtain those states by construction.

## Conclusion

Relative to legacy PoissonInput, the reusable path is **inconclusive: difference -0.556 Hz (95% CI [-2.010, 0.899]) includes zero**. The reusable-vs-full-run gap (71.2 vs 67.2 Hz) uses both different seed sets and different channel sets (sugar-only versus sugar+bitter). The earlier ±1 standard-deviation overlap criterion was not an adequate test of bias.

## Acceptance criteria

| # | criterion | measured | threshold | PASS/FAIL |
|---|---|---|---|---|
| 1 | restore-determinism | same-seed exact=True; all restored state at rest=True | exact spike trains and v, g, refractory state, stimulus rates at rest | PASS |
| 2 | paired reusable vs fresh PoissonGroup | mean paired MN9-L difference=0.000 Hz; exact=10/10 | mean paired difference within ±2 Hz | PASS |
| 3 | stimulus semantics vs legacy PoissonInput | MN9-L CI=[-2.010, 0.899] Hz, p=0.451963; total CI=[-80.569, 126.369] spikes/trial ([-0.834%, 1.308%] of legacy mean), p=0.662808 | MN9-L 95% CI within ±3 Hz and including 0; total CI covers 0 (no p-value rule) | PASS |
| 4 | refractory quirk experiment | n=10; mean paired MN9-L count difference=-4.100 (different stream); exact=0/10; same-stream pure refractory difference=0.000, exact=10/10 | 10 matched seeds reported (diagnostic; no numerical equivalence bound) | PASS |

**Recommendation:** Use the reusable path as the single downstream path. Criterion 4: the same-random-stream variant shows the refractory rule has zero measured effect; the per-channel rule (rfc=0 only for driven channels, as in model.py) is kept for fidelity, not because it changes results. Phase 0 condition A was re-run on the fixed path; its delta at 100 Hz (+0.1 Hz) is random-stream sampling noise, so Phase 1 was not re-run.
