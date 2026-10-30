# ASHRAE 140 envelope constructions used for VDI validation
The experiment shows that proxy representations of fabric layers can materially distort the benchmark assessment. 

Given the uncertainty associated with such proxies, the ASHRAE 140 constructions are therefore referenced directly, using Table 7-2 (p. 40) for Case 600 and Table 7-27 for Case 900.

To avoid uncertainty introduced by proxy fabric definitions, the VDI validation uses the ASHRAE 140 constructions directly.

#### Case 600 — lightweight construction (ASHRAE 140 Table 7-2)

| Assembly | Layer order | Layer | Thickness (m) | Conductivity, k (W/m·K) | Density (kg/m³) | Specific heat, cp (J/kg·K) |
|---|---:|---|---:|---:|---:|---:|
| Wall | 1, inside | Plasterboard | 0.0120 | 0.160 | 950 | 840 |
| Wall | 2 | Fiberglass quilt | 0.0660 | 0.040 | 12 | 840 |
| Wall | 3, outside | Wood siding | 0.0090 | 0.140 | 530 | 900 |
| Roof | 1, inside | Plasterboard | 0.0100 | 0.160 | 950 | 840 |
| Roof | 2 | Fiberglass quilt | 0.1118 | 0.040 | 12 | 840 |
| Roof | 3, outside | Roof deck | 0.0190 | 0.140 | 530 | 900 |
| Floor | 1, inside | Timber flooring | 0.0250 | 0.140 | 650 | 1200 |
| Floor | 2, outside | Underfloor insulation — minimum permitted capacity | 1.0030 | 0.040 | minimum permitted | minimum permitted |

Notes:

- ASHRAE Table 7-2 presents the constructions inside-to-outside.
- The current VDI input may store the arrays outside-to-inside, but the reducer should receive them in room-side-to-outside order.
- For the underfloor insulation, ASHRAE requires the minimum density and specific heat permitted by the simulation program, not values below zero.
- Where the VDI material class requires strictly positive values, very small positive numerical surrogates may be used to represent the required negligible thermal capacity.


#### Case 900 — heavyweight construction (ASHRAE 140 Table 7-27)

| Assembly | Layer order | Layer | Thickness (m) | Conductivity, k (W/m·K) | Density (kg/m³) | Specific heat, cp (J/kg·K) |
|---|---:|---|---:|---:|---:|---:|
| Wall | 1, inside | Concrete block | 0.1000 | 0.510 | 1400 | 1000 |
| Wall | 2 | Foam insulation | 0.0615 | 0.040 | 10 | 1400 |
| Wall | 3, outside | Wood siding | 0.0090 | 0.140 | 530 | 900 |
| Roof | 1, inside | Plasterboard | 0.0100 | 0.160 | 950 | 840 |
| Roof | 2 | Fiberglass quilt | 0.1118 | 0.040 | 12 | 840 |
| Roof | 3, outside | Roof deck | 0.0190 | 0.140 | 530 | 900 |
| Floor | 1, inside | Concrete slab | 0.0800 | 1.130 | 1400 | 1000 |
| Floor | 2, outside | Underfloor insulation — minimum permitted capacity | 1.0070 | 0.040 | minimum permitted | minimum permitted |

Notes:

- Case 900 replaces the lightweight Case 600 wall and floor with heavyweight constructions.
- The roof construction remains the same as Case 600.
- The underfloor insulation again follows the benchmark minimum-capacity treatment.
- These physical layer chains should be used for the VDI dynamic reduction rather than scaling Case 600 material heat capacities to match an aggregate thermal-mass target.