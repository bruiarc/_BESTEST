# BESTEST LBNL All-Cases Reference

## Purpose

This file is a compact reference for Codex and Jupyter notebook development under:

`_development/2__validation/_BESTEST/`

It records the LBNL Modelica ISO 13790 BESTEST reporting format, all 20 conditioned cases, the 6 associated free-floating cases used in the LBNL presentation, and the published reference data visible in the bundled UsersGuide material.

This file is intentionally not limited to Case 600.

---

# 1. Scope

## 1.1 Conditioned cases

The 20 conditioned BESTEST cases are:

`600, 610, 620, 630, 640, 650, 660, 670, 680, 685, 695, 900, 910, 920, 930, 940, 950, 980, 985, 995`

## 1.2 Free-floating cases

The free-floating cases used in the LBNL presentation are:

`600FF, 650FF, 680FF, 900FF, 950FF, 980FF`

---

# 2. LBNL reporting structure

## 2.1 Conditioned cases

The LBNL Modelica ISO 13790 BESTEST UsersGuide reports:

1. Annual heating energy
2. Annual cooling energy
3. Peak heating load
4. Peak cooling load
5. Peak occurrence time
6. Case 600 one-day load profile
7. Case 900 one-day load profile

The bundled LBNL generator uses **1 February** for the Case 600 and Case 900 daily profiles.

### Figure categories

1. `annual_heating`
2. `annual_cooling`
3. `peak_heating`
4. `peak_cooling`
5. `hourly_load_600_Feb1`
6. `hourly_load_900_Feb1`

## 2.2 Free-floating cases

The UsersGuide reports:

7. Annual maximum zone-air temperature
8. Annual minimum zone-air temperature
9. Case 600FF daily temperature profile on 1 February
10. Case 900FF daily temperature profile on 1 February
11. Case 650FF daily temperature profile on 14 July
12. Case 950FF daily temperature profile on 14 July
13. Annual average zone-air temperature
14. Case 900FF annual temperature-bin/distribution plot

### Figure categories

7. `max_temperature`
8. `min_temperature`
9. `FF_temperature_600FF_Feb1`
10. `FF_temperature_900FF_Feb1`
11. `FF_temperature_650FF_Jul14`
12. `FF_temperature_950FF_Jul14`
13. `ave_temperature`
14. `bin_temperature_900FF`

---

# 3. Annual heating energy reference data

Units: **MWh**

| Case | Lower | Upper | BSIMAC | CSE | DeST | EnergyPlus | ESP-r | TRNSYS | Modelica ISO13790 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 600 | 3.75 | 4.98 | 4.050 | 3.993 | 4.047 | 4.324 | 4.362 | 4.504 | 4.658 |
| 610 | 3.61 | 5.27 | 4.163 | 4.066 | 4.144 | 4.375 | 4.527 | 4.592 | 4.784 |
| 620 | 3.67 | 5.38 | 4.370 | 4.094 | 4.297 | 4.485 | 4.514 | 4.719 | 4.824 |
| 630 | 3.69 | 6.12 | 4.923 | 4.356 | 4.677 | 4.784 | 5.051 | 5.139 | 5.097 |
| 640 | 1.58 | 3.76 | 2.682 | 2.403 | 2.619 | 2.662 | 2.654 | 2.653 | 2.898 |
| 650 | 0.00 | 0.00 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 660 | 2.68 | 4.82 | 3.574 | 3.602 | 3.821 | 3.707 | 3.787 | 3.790 | 3.898 |
| 670 | 4.00 | 7.96 | 5.484 | 5.300 | 5.573 | 5.616 | 5.975 | 6.140 | 7.381 |
| 680 | 1.21 | 3.08 | 2.219 | 1.786 | 1.732 | 2.180 | 2.132 | 2.286 | 2.646 |
| 685 | 4.08 | 5.75 | 4.532 | 4.574 | 4.646 | 4.877 | 4.904 | 5.042 | 5.063 |
| 695 | 1.70 | 3.81 | 2.709 | 2.415 | 2.385 | 2.802 | 2.732 | 2.892 | 3.147 |
| 900 | 1.04 | 2.28 | 1.726 | 1.379 | 1.591 | 1.664 | 1.585 | 1.814 | 1.833 |
| 910 | 1.56 | 2.30 | 2.163 | 1.648 | 1.860 | 1.956 | 2.067 | 2.132 | 2.284 |
| 920 | 2.55 | 4.20 | 3.500 | 2.956 | 3.259 | 3.337 | 3.300 | 3.607 | 3.650 |
| 930 | 2.75 | 5.35 | 4.270 | 3.524 | 3.933 | 3.994 | 4.278 | 4.384 | 4.183 |
| 940 | 0.22 | 1.91 | 1.389 | 0.863 | 1.149 | 1.067 | 1.015 | 1.169 | 1.242 |
| 950 | 0.00 | 0.00 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 980 | -0.61 | 1.28 | 0.720 | 0.246 | 0.266 | 0.411 | 0.351 | 0.450 | 0.494 |
| 985 | 1.68 | 3.09 | 2.801 | 2.120 | 2.279 | 2.369 | 2.283 | 2.536 | 2.333 |
| 995 | -0.15 | 2.02 | 1.330 | 0.755 | 0.770 | 1.006 | 0.905 | 1.077 | 0.927 |

---

# 4. Annual cooling energy reference data

Units: **MWh**

| Case | Lower | Upper | BSIMAC | CSE | DeST | EnergyPlus | ESP-r | TRNSYS | Modelica ISO13790 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 600 | 5.00 | 6.83 | 5.822 | 5.913 | 5.432 | 6.027 | 6.162 | 5.780 | 5.803 |
| 610 | 2.74 | 6.03 | 4.299 | 4.382 | 4.173 | 4.333 | 4.233 | 4.117 | 4.602 |
| 620 | 2.76 | 5.19 | 4.404 | 4.079 | 3.909 | 4.060 | 4.246 | 3.841 | 4.009 |
| 630 | 1.08 | 4.42 | 3.074 | 3.020 | 2.787 | 2.836 | 2.595 | 2.573 | 2.954 |
| 640 | 4.44 | 6.86 | 5.804 | 5.644 | 5.237 | 5.763 | 5.893 | 5.477 | 5.617 |
| 650 | 3.46 | 5.88 | 4.629 | 4.654 | 4.186 | 4.817 | 4.945 | 4.632 | 4.821 |
| 660 | 1.91 | 4.33 | 3.014 | 3.340 | 3.260 | 3.232 | 3.219 | 2.966 | 3.185 |
| 670 | 5.05 | 7.67 | 6.539 | 6.578 | 5.954 | 6.623 | 6.520 | 6.198 | 4.975 |
| 680 | 5.13 | 7.70 | 5.938 | 6.430 | 5.932 | 6.444 | 6.529 | 6.310 | 6.764 |
| 685 | 7.70 | 10.14 | 9.130 | 8.859 | 8.238 | 9.119 | 9.121 | 8.851 | 8.651 |
| 695 | 7.49 | 10.58 | 8.755 | 8.974 | 8.386 | 9.172 | 9.149 | 9.039 | 9.323 |
| 900 | 2.35 | 2.60 | 2.714 | 2.464 | 2.383 | 2.489 | 2.488 | 2.267 | 2.284 |
| 910 | 2.00 | 0.86 | 1.484 | 1.415 | 1.490 | 1.383 | 1.283 | 1.191 | 1.674 |
| 920 | 2.43 | 3.08 | 3.128 | 2.789 | 2.706 | 2.731 | 2.814 | 2.549 | 2.684 |
| 930 | 1.24 | 2.64 | 2.161 | 2.075 | 1.908 | 1.919 | 1.654 | 1.672 | 1.920 |
| 940 | 2.24 | 3.14 | 2.613 | 2.397 | 2.343 | 2.424 | 2.428 | 2.203 | 2.251 |
| 950 | 0.43 | 1.52 | 0.586 | 0.598 | 0.618 | 0.707 | 0.656 | 0.642 | 0.638 |
| 980 | 3.52 | 4.49 | 3.501 | 3.995 | 3.758 | 3.712 | 3.775 | 3.519 | 3.658 |
| 985 | 5.95 | 7.26 | 7.273 | 6.234 | 5.880 | 6.359 | 6.249 | 6.113 | 5.905 |
| 995 | 6.58 | 8.41 | 7.482 | 7.202 | 6.771 | 7.203 | 7.149 | 7.064 | 7.077 |

> Note: Case 910 is reproduced exactly as visible in the source table, where the cooling "lower" and "upper" entries appear as `2.00` and `0.86`. This looks internally inconsistent. Do not silently correct it in executable validation logic; verify against the authoritative supplemental workbook before using it for pass/fail.

---

# 5. Peak heating reference data

Units: **kW**

| Case | BSIMAC | BSIMAC hour | CSE | CSE hour | DeST | DeST hour | EnergyPlus | EnergyPlus hour | ESP-r | ESP-r hour | TRNSYS | TRNSYS hour | Modelica ISO13790 | Modelica hour |
|---|---:|---|---:|---|---:|---|---:|---|---:|---|---:|---|---:|---|
| 600 | 3.255 | 26-Nov:8 | 3.020 | 01-Jan:1 | 3.035 | 01-Jan:0 | 3.204 | 31-Dec:24 | 3.228 | 01-Jan:1 | 3.359 | 01-Jan:1 | 3.232 | 31-Dec:24 |
| 610 | 3.166 | 26-Nov:8 | 3.021 | 01-Jan:1 | 3.039 | 01-Jan:0 | 3.192 | 31-Dec:24 | 3.233 | 01-Jan:1 | 3.360 | 01-Jan:1 | 3.236 | 31-Dec:24 |
| 620 | 3.145 | 31-Dec:24 | 3.038 | 01-Jan:1 | 3.068 | 01-Jan:0 | 3.229 | 31-Dec:24 | 3.253 | 01-Jan:1 | 3.385 | 01-Jan:1 | 3.249 | 31-Dec:24 |
| 630 | 3.252 | 31-Dec:24 | 3.039 | 01-Jan:1 | 3.072 | 01-Jan:0 | 3.207 | 31-Dec:24 | 3.259 | 01-Jan:1 | 3.388 | 01-Jan:1 | 3.251 | 31-Dec:24 |
| 640 | 4.633 | 08-Feb:9 | 4.222 | 26-Nov:8 | 4.658 | 26-Nov:7 | 4.559 | 26-Nov:8 | 4.101 | 26-Nov:8 | 4.039 | 26-Nov:8 | 3.880 | 26-Nov:8 |
| 650 | 0.000 | N/A | 0.000 | 01-Jan:1 | 0.000 | N/A | 0.000 | 01-Jan:1 | 0.000 | 01-Jan:1 | 0.000 | 31-Dec:0 | 0.000 | 31-Dec:24 |
| 660 | 2.620 | 26-Nov:8 | 2.758 | 01-Jan:1 | 2.798 | 01-Jan:0 | 2.831 | 31-Dec:24 | 2.846 | 01-Jan:1 | 2.955 | 01-Jan:1 | 2.717 | 31-Dec:24 |
| 670 | 4.122 | 26-Nov:8 | 3.655 | 01-Jan:1 | 3.812 | 01-Jan:0 | 3.854 | 26-Nov:7 | 3.992 | 26-Nov:7 | 4.221 | 26-Nov:8 | 4.516 | 31-Dec:24 |
| 680 | 2.126 | 26-Nov:8 | 1.778 | 09-Feb:6 | 1.811 | 01-Jan:1 | 2.052 | 26-Nov:7 | 2.022 | 09-Feb:7 | 2.115 | 26-Nov:8 | 2.241 | 31-Dec:24 |
| 685 | 3.169 | 26-Nov:8 | 3.032 | 01-Jan:1 | 3.054 | 01-Jan:0 | 3.223 | 31-Dec:24 | 3.247 | 01-Jan:1 | 3.374 | 01-Jan:1 | 3.233 | 31-Dec:24 |
| 695 | 2.138 | 26-Nov:8 | 1.795 | 01-Jan:1 | 1.855 | 01-Jan:1 | 2.072 | 31-Dec:24 | 2.025 | 26-Nov:7 | 2.118 | 26-Nov:8 | 2.271 | 31-Dec:24 |
| 900 | 2.551 | 08-Feb:24 | 2.443 | 09-Feb:6 | 2.453 | 09-Feb:5 | 2.687 | 09-Feb:6 | 2.633 | 09-Feb:7 | 2.778 | 09-Feb:7 | 2.640 | 9-Feb:6 |
| 910 | 2.761 | 08-Feb:24 | 2.469 | 09-Feb:6 | 2.474 | 09-Feb:5 | 2.699 | 09-Feb:6 | 2.684 | 09-Feb:7 | 2.799 | 09-Feb:6 | 2.679 | 9-Feb:6 |
| 920 | 2.895 | 26-Nov:8 | 2.512 | 09-Feb:6 | 2.513 | 09-Feb:5 | 2.770 | 09-Feb:6 | 2.706 | 09-Feb:7 | 2.864 | 09-Feb:6 | 2.728 | 9-Feb:6 |
| 930 | 2.968 | 31-Dec:24 | 2.537 | 09-Feb:6 | 2.549 | 09-Feb:5 | 2.785 | 09-Feb:6 | 2.765 | 09-Feb:6 | 2.900 | 09-Feb:6 | 2.760 | 9-Feb:6 |
| 940 | 3.882 | 08-Feb:9 | 3.052 | 01-Jan:9 | 3.659 | 09-Feb:7 | 3.143 | 31-Dec:9 | 3.122 | 09-Feb:9 | 3.405 | 01-Jan:9 | 3.111 | 9-Feb:9 |
| 950 | 0.000 | N/A | 0.000 | 01-Jan:1 | 0.000 | N/A | 0.000 | 01-Jan:1 | 0.000 | 01-Jan:1 | 0.000 | 31-Dec:0 | 0.000 | 31-Dec:24 |
| 980 | 1.693 | 08-Feb:24 | 1.254 | 09-Feb:6 | 1.382 | 09-Feb:5 | 1.538 | 09-Feb:6 | 1.473 | 09-Feb:7 | 1.592 | 09-Feb:7 | 1.706 | 9-Feb:6 |
| 985 | 2.754 | 08-Feb:24 | 2.452 | 09-Feb:6 | 2.458 | 09-Feb:5 | 2.695 | 09-Feb:6 | 2.642 | 09-Feb:7 | 2.785 | 09-Feb:6 | 2.636 | 9-Feb:6 |
| 995 | 1.711 | 26-Nov:8 | 1.370 | 09-Feb:6 | 1.462 | 09-Feb:5 | 1.622 | 09-Feb:6 | 1.560 | 09-Feb:7 | 1.662 | 09-Feb:6 | 1.740 | 9-Feb:6 |

---

# 6. Peak cooling reference data

Units: **kW**

| Case | BSIMAC | BSIMAC hour | CSE | CSE hour | DeST | DeST hour | EnergyPlus | EnergyPlus hour | ESP-r | ESP-r hour | TRNSYS | TRNSYS hour | Modelica ISO13790 | Modelica hour |
|---|---:|---|---:|---|---:|---|---:|---|---:|---|---:|---|---:|---|
| 600 | 5.650 | 22-Jan:15 | 6.481 | 22-Jan:14 | 5.422 | 22-Jan:14 | 6.352 | 22-Jan:14 | 6.193 | 22-Jan:14 | 6.046 | 22-Jan:14 | 5.570 | 22-Jan:14 |
| 610 | 5.466 | 22-Jan:15 | 6.432 | 01-Dec:14 | 5.331 | 22-Jan:14 | 6.135 | 01-Dec:14 | 5.934 | 22-Jan:14 | 5.868 | 01-Dec:14 | 4.611 | 18-Oct:14 |
| 620 | 4.704 | 26-Jun:18 | 4.493 | 26-Jun:17 | 3.955 | 26-Jun:17 | 4.797 | 26-Jun:17 | 4.622 | 26-Jun:17 | 4.588 | 26-Jun:17 | 4.384 | 26-Jun:18 |
| 630 | 4.121 | 26-Jun:18 | 3.998 | 26-Jun:18 | 3.526 | 26-Jun:17 | 4.212 | 26-Jun:17 | 3.971 | 26-Jun:17 | 3.949 | 26-Jun:17 | 3.734 | 26-Jun:18 |
| 640 | 5.650 | 22-Jan:15 | 6.429 | 22-Jan:14 | 5.365 | 22-Jan:14 | 6.297 | 22-Jan:14 | 6.127 | 22-Jan:14 | 5.967 | 22-Jan:14 | 5.516 | 22-Jan:14 |
| 650 | 5.648 | 22-Jan:15 | 6.290 | 01-Dec:14 | 5.045 | 18-Oct:14 | 6.138 | 18-Oct:14 | 5.961 | 18-Oct:14 | 5.797 | 18-Oct:14 | 5.382 | 18-Oct:14 |
| 660 | 3.343 | 18-Oct:15 | 3.933 | 01-Oct:13 | 3.355 | 11-Oct:14 | 3.770 | 18-Oct:14 | 3.530 | 01-Oct:14 | 3.457 | 18-Oct:14 | 3.344 | 18-Oct:14 |
| 670 | 6.217 | 18-Oct:14 | 6.925 | 01-Oct:13 | 5.839 | 10-Oct:13 | 6.806 | 22-Jan:14 | 6.482 | 18-Oct:14 | 6.401 | 18-Oct:14 | 5.187 | 18-Oct:14 |
| 680 | 5.761 | 22-Jan:15 | 7.051 | 22-Jan:14 | 5.861 | 22-Jan:14 | 6.770 | 22-Jan:14 | 6.676 | 22-Jan:14 | 6.557 | 22-Jan:14 | 6.281 | 22-Jan:14 |
| 685 | 6.318 | 22-Jan:15 | 7.159 | 22-Jan:14 | 6.071 | 22-Jan:14 | 7.107 | 22-Jan:14 | 6.934 | 22-Jan:14 | 6.867 | 22-Jan:14 | 6.265 | 22-Jan:14 |
| 695 | 6.232 | 22-Jan:15 | 7.541 | 22-Jan:14 | 6.355 | 22-Jan:14 | 7.334 | 22-Jan:14 | 7.239 | 22-Jan:14 | 7.175 | 22-Jan:14 | 6.829 | 22-Jan:14 |
| 900 | 3.039 | 01-Oct:15 | 3.376 | 01-Oct:14 | 2.556 | 11-Sep:14 | 3.040 | 01-Oct:14 | 2.896 | 12-Oct:15 | 2.940 | 01-Oct:14 | 2.365 | 1-Oct:15 |
| 910 | 2.493 | 18-Oct:14 | 2.722 | 02-Oct:15 | 2.103 | 12-Oct:14 | 2.222 | 18-Oct:15 | 2.212 | 02-Oct:15 | 2.081 | 12-Oct:15 | 2.012 | 11-Sep:15 |
| 920 | 3.481 | 26-Jun:18 | 3.057 | 26-Jun:18 | 2.710 | 26-Jun:17 | 3.260 | 26-Jun:18 | 3.099 | 26-Jun:18 | 3.154 | 26-Jun:18 | 2.798 | 26-Jun:18 |
| 930 | 3.052 | 26-Jun:18 | 2.662 | 26-Jun:18 | 2.335 | 26-Jun:17 | 2.782 | 26-Jun:18 | 2.494 | 26-Jun:18 | 2.613 | 26-Jun:18 | 2.365 | 26-Jun:18 |
| 940 | 3.158 | 01-Oct:15 | 3.376 | 01-Oct:14 | 2.556 | 11-Sep:14 | 3.040 | 01-Oct:14 | 2.891 | 12-Oct:15 | 2.938 | 01-Oct:14 | 2.365 | 1-Oct:15 |
| 950 | 2.366 | 10-Sep:15 | 2.364 | 04-Sep:15 | 2.054 | 11-Sep:14 | 2.388 | 11-Sep:15 | 2.202 | 10-Sep:15 | 2.236 | 11-Sep:15 | 1.940 | 11-Sep:16 |
| 980 | 3.384 | 18-Oct:14 | 3.668 | 02-Oct:14 | 2.930 | 18-Oct:14 | 3.450 | 18-Oct:15 | 3.341 | 12-Oct:15 | 3.313 | 12-Oct:14 | 2.658 | 18-Oct:15 |
| 985 | 3.977 | 18-Oct:14 | 4.225 | 01-Oct:14 | 3.208 | 11-Oct:14 | 3.915 | 18-Oct:15 | 3.736 | 12-Oct:15 | 3.885 | 01-Oct:14 | 3.053 | 1-Oct:15 |
| 995 | 4.129 | 22-Jan:14 | 4.224 | 22-Jan:15 | 3.315 | 22-Jan:14 | 4.177 | 22-Jan:15 | 3.954 | 22-Jan:15 | 4.115 | 22-Jan:15 | 3.113 | 18-Oct:15 |

---

# 7. Free-floating maximum temperature reference data

Units: **°C**

| Case | BSIMAC | BSIMAC hour | CSE | CSE hour | DeST | DeST hour | EnergyPlus | EnergyPlus hour | ESP-r | ESP-r hour | TRNSYS | TRNSYS hour | Modelica ISO13790 | Modelica hour |
|---|---:|---|---:|---|---:|---|---:|---|---:|---|---:|---|---:|---|
| 600FF | 63.4 | 18-Oct:17 | 68.4 | 01-Oct:16 | 65.0 | 11-Oct:15 | 63.8 | 18-Oct:16 | 64.6 | 01-Oct:16 | 62.4 | 01-Oct:15 | 67.0 | 18-Oct:16 |
| 650FF | 62.1 | 18-Oct:17 | 66.8 | 01-Oct:16 | 62.6 | 11-Oct:15 | 62.5 | 18-Oct:16 | 63.3 | 01-Oct:16 | 61.1 | 01-Oct:15 | 66.2 | 18-Oct:16 |
| 680FF | 72.5 | 22-Jan:17 | 78.5 | 22-Jan:16 | 75.0 | 12-Oct:15 | 70.1 | 22-Jan:16 | 72.2 | 12-Oct:16 | 69.8 | 22-Jan:16 | 77.1 | 22-Jan:16 |
| 900FF | 46.0 | 01-Oct:17 | 45.1 | 04-Sep:15 | 44.5 | 11-Sep:15 | 44.3 | 12-Sep:15 | 44.3 | 12-Sep:16 | 43.3 | 12-Sep:15 | 43.4 | 11-Sep:16 |
| 950FF | 37.1 | 01-Oct:17 | 36.8 | 11-Sep:15 | 36.4 | 11-Sep:15 | 36.7 | 11-Sep:16 | 36.4 | 05-Aug:16 | 36.1 | 11-Sep:16 | 36.6 | 11-Sep:16 |
| 980FF | 49.7 | 01-Oct:17 | 52.2 | 12-Sep:15 | 52.8 | 21-Oct:14 | 49.6 | 12-Sep:16 | 50.2 | 12-Sep:15 | 48.5 | 12-Sep:15 | 49.9 | 12-Sep:16 |

---

# 8. Free-floating minimum temperature reference data

Units: **°C**

| Case | BSIMAC | BSIMAC hour | CSE | CSE hour | DeST | DeST hour | EnergyPlus | EnergyPlus hour | ESP-r | ESP-r hour | TRNSYS | TRNSYS hour | Modelica ISO13790 | Modelica hour |
|---|---:|---|---:|---|---:|---|---:|---|---:|---|---:|---|---:|---|
| 600FF | -9.9 | 26-Nov:8 | -12.9 | 09-Feb:7 | -13.5 | 09-Feb:6 | -12.6 | 09-Feb:7 | -13.5 | 09-Feb:7 | -13.8 | 09-Feb:7 | -12.9 | 9-Feb:7 |
| 650FF | -16.7 | 31-Dec:24 | -17.8 | 01-Jan:1 | -17.4 | 30-Dec:23 | -17.1 | 31-Dec:24 | -17.5 | 01-Jan:1 | -17.5 | 31-Dec:24 | -17.5 | 31-Dec:24 |
| 680FF | -5.7 | 08-Feb:11 | -6.2 | 09-Feb:7 | -6.9 | 09-Feb:7 | -7.1 | 09-Feb:7 | -7.2 | 09-Feb:7 | -8.1 | 09-Feb:7 | -9.2 | 9-Feb:7 |
| 900FF | 0.6 | 08-Feb:11 | 2.2 | 09-Feb:7 | 1.3 | 09-Feb:7 | 1.2 | 09-Feb:7 | 1.6 | 09-Feb:7 | 0.6 | 09-Feb:7 | 0.3 | 9-Feb:7 |
| 950FF | -13.2 | 31-Dec:24 | -13.2 | 01-Jan:1 | -13.4 | 30-Dec:23 | -12.8 | 09-Feb:7 | -12.5 | 09-Feb:6 | -12.8 | 09-Feb:6 | -13.4 | 31-Dec:24 |
| 980FF | 7.3 | 08-Feb:11 | 12.5 | 04-Nov:7 | 12.4 | 05-Nov:6 | 9.9 | 04-Nov:7 | 10.5 | 04-Nov:8 | 9.5 | 04-Nov:7 | 8.6 | 4-Nov:7 |

---

# 9. Pilot-specific controlled-forcing convention

For current report-oriented notebooks, the controlled-forcing ISO result may be the default displayed ISO series while native ISO remains available through a switch.

Recommended configuration:

```python
ISO_MODE = "modelica_solar"
# accepted:
# "modelica_solar"
# "native"
```

Recommended labels:

- `Modelica native`
- `ISO 13790 + Modelica-resolved solar`
- `ISO 13790 native solar`

This display convention does not change the formal validation logic.

Formal native BESTEST result:
`BESTEST prescribed inputs -> native implementation preprocessing -> native thermal/control model -> outputs`

Controlled-forcing diagnostic result:
`Modelica-resolved solar forcing -> Python ISO 13790 thermal/control model -> outputs`

The controlled-forcing route must not be used silently as the formal ASHRAE pass/fail result.

---

# 10. Case 600 pilot result currently available

| Run | Heating | Cooling |
|---|---:|---:|
| Native ISO | 5.502373 MWh | 1.413772 MWh |
| ISO + Modelica solar | 4.582236 MWh | 5.727737 MWh |
| Modelica native | 4.657997 MWh | 5.802666 MWh |

Solar substitution changes ISO heating by **−16.72%** and cooling by **+305.14%**.

Remaining differences between controlled-forcing ISO and Modelica are:

- heating: **−1.63%**
- cooling: **−1.29%**

Native annual zone solar:
**4.270 MWh**

Modelica-resolved annual zone solar forcing:
**12.112 MWh**

Case600FF matched-forcing air-temperature MAE:
**0.298895 °C**

The native solar-preprocessing discrepancy remains a future-work thread.

---

# 11. Notebook development rules

For each case or case group:

1. Use the canonical BESTEST case definition as the physical source.
2. Map prescribed inputs explicitly to each implementation.
3. Keep native and diagnostic forcing routes separate.
4. Use a common 8760-hour completed-hour output convention where applicable.
5. Report the LBNL/BESTEST quantities corresponding to the case.
6. Keep units explicit.
7. Keep heating/cooling sign conventions explicit.
8. Preserve occurrence times for peak metrics.
9. Do not infer missing ASHRAE acceptance bounds from reference-program spread.
10. Do not use cross-implementation agreement as a substitute for formal native ASHRAE validation.
11. If a source value looks inconsistent, preserve it in this reference and flag it for verification rather than silently correcting it.
12. Use authoritative source files programmatically for executable validation logic wherever possible.

---

# 12. Suggested standardized output schemas

## Hourly conditioned output

```text
timestamp
case
implementation
run_mode
formal_ashrae_result
zone_temperature_C
heating_load_W
cooling_load_W
solar_gain_W
```

## Annual conditioned summary

```text
case
implementation
run_mode
formal_ashrae_result
annual_heating_MWh
annual_cooling_MWh
peak_heating_kW
peak_heating_time
peak_cooling_kW
peak_cooling_time
ashrae_heating_lower_MWh
ashrae_heating_upper_MWh
ashrae_cooling_lower_MWh
ashrae_cooling_upper_MWh
heating_within_range
cooling_within_range
```

## Free-floating summary

```text
case
implementation
run_mode
formal_ashrae_result
annual_min_temperature_C
annual_min_temperature_time
annual_max_temperature_C
annual_max_temperature_time
annual_mean_temperature_C
```

---

# 13. Source note

The bundled LBNL Modelica ISO13790 BESTEST UsersGuide states that the validation data come from `RESULTS5-2A.xlsx` in the ASHRAE Standard 140-2020 supplemental files.

The current local source includes published tables and figure structure, but the external supplemental workbook should still be obtained and parsed before formal pass/fail is assigned to metrics for which bundled numeric acceptance bounds are not available.

---

# 14. Artifact-retention contract

Avoid creating repeated large artifacts that duplicate an authoritative file
without adding information. Modelica execution artifacts are centrally retained
under:

`_development/2__validation/_modelica/results/`

For example, `modelica_case600_raw.csv` duplicates the centralized source CSV
`_modelica/results/Case600/Case600_res.csv`; it should not be generated as a
second report artifact. Diagnostic code must read the centralized Modelica CSV
directly when raw variables are required.

Keep only derived, standardized, or report-specific outputs in `_BESTEST`,
where they add traceable value: common-schema hourly results, calculated
metrics, required profile slices, reference joins, and LBNL-report figures.
