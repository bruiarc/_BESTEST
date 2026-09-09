# Case 600 VDI AW aggregation production-code retest

## Production functions tested

The tests call the original library functions directly: `dynamic_impedance`, `aggregate_dynamic_components_complex`, `aggregate_aw_components`, `aggregate_iw_components`, `aw_aggregate_inputs_with_massless_windows`, `transparent_component_r1`, `total_aw_resistance_details`, `residual_aw_resistance`, `combined_radiative_resistance`, `delta_to_star`, `reduce_component`, and the AW coefficient/history functions used by `prepare_aw_only_model`.

`ROOM_AGGREGATION_PERIOD_DAYS` is 5 days. Component reduction uses `reduce_component`, including 2/7-day selection and `corrected_capacity_asymmetric` for AW.

## Complex sign convention

`dynamic_impedance` implements `Z = R + 1/(j ω C)`, hence `Im(Z) < 0`. This corresponds to the conventional `exp(+jωt)` phasor sign. The code does not otherwise require an explicit time-domain phasor convention. Recovery uses `C = -1/(ω Im(Z))`, so construction and inversion are internally consistent. Single-branch round trips recover R and C to relative tolerance `1e-13`.

## Analytical regression tests

Production aggregation was compared with the permitted analytical oracle `1/sum(1/Z_i)` for two different branches, two identical branches, strongly unequal branches, three branches, and reversed ordering. Equivalent R, C, real/imaginary impedance, magnitude, and phase all agree within `1e-12` (phase absolute tolerance `1e-13` radians). Ordering is immaterial.

The regression file is `RC_br/tests/test_vdi_aw_aggregation_regression.py`. Together with the AW-only tests, 12 focused tests pass.

## Case 600 component inputs

| Component | Area m2 | Selected period d | R1 entering aggregation K/W | C entering aggregation J/K |
|---|---:|---:|---:|---:|
| north wall | 21.6 | 7 | 0.00118296919 | 210902.735 |
| east wall | 16.2 | 7 | 0.00157729225 | 158177.051 |
| south wall plus associated window R1 | 9.6 opaque | 7 | 0.00120104052 | 93734.549 |
| west wall | 16.2 | 7 | 0.00157729225 | 158177.051 |
| roof | 48.0 | 7 | 0.000550791436 | 381586.716 |
| floor | 48.0 | 7 | 0.00123677311 | 935138.309 |

The production `ReducedComponent.c1_effective_j_k` property selects `c1_corrected_j_k` for AW and ordinary `c1_j_k` for IW. Tests prove that AW aggregation receives corrected C1, not C2 or raw C1. Resistances are K/W and capacitances J/K after component area scaling. Doubling area halves R and doubles C; recombining equal material areas reproduces the single combined-area branch. No second area scaling was found.

## Window/AW ordering

The production sequence is:

1. `reduce_component` reduces opaque layers and applies asymmetric C correction.
2. `transparent_component_r1` removes inside/outside films from whole-window U and applies Eq. 25; window C remains zero.
3. `aw_aggregate_inputs_with_massless_windows` places window R1 in parallel with the matching opaque-plane R1 while retaining opaque corrected C1.
4. `aggregate_aw_components` performs the five-day room aggregation.
5. `total_aw_resistance_details` separately applies Eq. 27 once using whole-component `U*A`.

The regression verifies that window resistance is neither added twice nor assigned capacitance. Case 600 Eq. 27 conductance is 88.572 W/K, including 37.2 W/K from the south windows.

## Five-day amplitude/phase result

Case 600 production aggregate:

- R1 = 0.000347233580 K/W
- C1 = 1,937,626.647 J/K
- Z(5 d) = 0.000347233580 − 0.035484098817 j K/W
- magnitude = 0.035485797723 K/W
- phase = −89.43934370 degrees

At five days, the equivalent and unreduced parallel ensemble match exactly: magnitude ratio 1.0 and phase difference 0 degrees.

## Frequency-response diagnostic

The original component R1/C1 ensemble and the fixed five-day equivalent were evaluated analytically using the production `dynamic_impedance` values. Only the five-day row is an acceptance point.

| Period d | Equivalent/original magnitude | Phase difference degrees |
|---:|---:|---:|
| 1 | 0.998897706 | +0.00632082 |
| 2 | 0.999757307 | +0.00069454 |
| 5 | 1.000000000 | 0.00000000 |
| 7 | 1.000022687 | −0.00001854 |
| 14 | 1.000040416 | −0.00001651 |

At one day the magnitude differs by only −0.1102% and phase by +0.0063 degrees. For these Case 600 component inputs, room aggregation away from its fitting point is far too small to explain the approximately 1.261 MWh heating residual or its day/night distribution.

## Any implementation bug found

No aggregation bug was found. The negative-imaginary convention, inverse C recovery, complex parallel aggregation, corrected AW capacity, window order, and area scaling are consistent. Therefore no production aggregation function was modified.

The earlier AW-only diagnostic instrumentation and optional initial-state support remain separate from this retest; neither changes aggregation equations.

## Case 600 before/after result

Because no aggregation defect exists, Case 600 was not altered or rerun to manufacture an after result. Before and after are identical:

| Metric | Before | After |
|---|---:|---:|
| heating MWh | 5.919426 | 5.919426 |
| cooling MWh | 6.215837 | 6.215837 |
| heating EUI kWh/m2yr | 123.321 | 123.321 |
| cooling EUI kWh/m2yr | 129.497 | 129.497 |
| peak heating kW | 3.978921 | 3.978921 |
| peak cooling kW | 6.206469 | 6.206469 |
| evening/night VDI−Modelica heating MWh | 1.295426 | 1.295426 |
| daytime/morning VDI−Modelica heating MWh | −0.033997 | −0.033997 |
| heating ASHRAE status | FAIL, above upper bound | unchanged |
| cooling ASHRAE status | PASS | unchanged |

## Final conclusion

Production AW aggregation is verified at `T_RA=5 days`. Mathematically, a five-day equivalent can differ away from its fitting frequency, but the measured Case 600 one-day error is only 0.11% in magnitude and 0.0063 degrees in phase. Thus the observed evening/night residual cannot plausibly be attributed materially to Eqs. 19–24 aggregation. Investigation should remain focused on the broader AW-only room topology, its loss of the two-surface radiative/storage structure, and comparison with the detailed comparator dynamics—not on changing the verified aggregate to improve annual agreement.
