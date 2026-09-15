# Case 600 F36/F52: exact implementation and numerical features

## Conclusion

Yes—with one important qualification. F36 and F52 share five of the six
factorial settings, and the recorded factor that differs is source allocation.
However, calling F52 simply “Modelica-fraction allocation” can imply more than
the implementation actually does. Both cases use the **no-IW** solver, so
neither can send heat to an IW node. F52 reproduces the Modelica-derived air
fraction, then sends the entire non-air remainder to AW. It therefore matches
the Modelica fractions only as closely as the no-IW topology permits.

These are **the two factorial combinations satisfying both BESTEST annual-load
bounds**. Their shared settings are descriptive, not evidence that any one of
those settings caused the pass.

## Factor-by-factor comparison

| Feature | F36 | F52 | Relationship |
|---|---|---|---|
| IW topology | no-IW | no-IW | shared |
| Solar/source allocation | native VDI area allocation | Modelica-derived air fraction; non-air remainder to AW | different |
| Envelope convention | layer-controlled dynamics | layer-controlled dynamics | shared |
| Inside total coefficient | 8 W/(m²·K) | 8 W/(m²·K) | shared |
| Exterior long-wave | harmonised | harmonised | shared |
| Internal-gain allocation | 50% air, 50% AW | 50% air, 50% AW | shared |
| Solar pipeline | native VDI | native VDI | shared |
| Heating | 4.823417 MWh | 4.816070 MWh | both in range |
| Cooling | 5.678802 MWh | 5.748399 MWh | both in range |

The BESTEST intervals used here are

\[
3.75 \le Q_H \le 4.98\ \mathrm{MWh},\qquad
5.00 \le Q_C \le 6.83\ \mathrm{MWh}.
\]

Consequently, both cases have normalized distance to the accepted rectangle
of zero:

\[
D_{\mathrm{MWh,norm}}=
\sqrt{\left(\frac{d_H}{4.98-3.75}\right)^2+
      \left(\frac{d_C}{6.83-5.00}\right)^2}=0.
\]

## 1. No-IW topology

The ordinary adapter infers an unprescribed IW area of

\[
A_{IW}=2A_f=2(48)=96\ \mathrm{m^2}.
\]

F36 and F52 instead use the structural no-IW solver:

\[
A_{IW}=0,qquad A_{room}=A_{AW}.
\]

The exterior-facing room-side area is

\[
A_{AW}=159.6+12.0=171.6\ \mathrm{m^2},
\]

comprising 159.6 m² of opaque surfaces and 12 m² of south glazing. No IW
resistance, capacitance, temperature state, or radiant receiver exists. This
is a topology change, not an epsilon-IW approximation.

## 2. The allocation difference

### F36: native VDI area allocation

Native window-transmitted solar sources use the VDI exterior-source fractions

\[
f_{IW}=\frac{A_{IW}}{A_{room}-A_{nu}},\qquad
f_{AW}=\frac{A_{AW}-A_{nu}}{A_{room}-A_{nu}},
\]

where \(A_{nu}\) is the exterior area excluded for the source orientation.
For the no-IW geometry, \(A_{IW}=0\) and \(A_{room}=A_{AW}\), hence

\[
f_{IW}=0,\qquad f_{AW}=1.
\]

Thus F36 places 100% of the native interior solar source radiantly at AW:

\[
\Phi_{sol,air}=0,\qquad
\Phi_{sol,AW}=\Phi_{sol,native},\qquad
\Phi_{sol,IW}=0.
\]

### F52: Modelica-derived allocation constrained to no-IW

The nominal comparator fractions are derived from

\[
A_t=171.6\ \mathrm{m^2},\quad
A_m=141.6\ \mathrm{m^2},\quad
H_{tr,w}=37.2\ \mathrm{W/K},\quad
h_{sur}=9.1\ \mathrm{W/(m^2K)}.
\]

They are

\[
f_{air}=\frac{H_{tr,w}}{h_{sur}A_t}=0.0238223,
\]

\[
f_{IW}^{nom}=\frac{A_m}{A_t}=0.8251748,
\]

\[
f_{AW}^{nom}=1-f_{air}-f_{IW}^{nom}=0.1510028.
\]

Those three nominal fractions cannot be applied literally because F52 has no
IW node. The implemented no-IW projection preserves the air fraction and
maps the whole non-air remainder to AW:

\[
f_{air}^{F52}=0.0238223,
\quad f_{AW}^{F52}=1-f_{air}=0.9761777,
\quad f_{IW}^{F52}=0.
\]

For every native interior-solar hour,

\[
\Phi_{sol,air}=0.0238223\,\Phi_{sol,native},
\]

\[
\Phi_{sol,AW}=0.9761777\,\Phi_{sol,native}.
\]

Therefore the exact F36/F52 contrast is essentially **100% AW radiant solar**
versus **2.382% air plus 97.618% AW solar**, not a complete AW/IW Modelica
allocation comparison. The annual native interior-solar source recorded by
the experiment is 11.751956 MWh in both cases. Native opaque solar remains in
the VDI exterior-boundary calculation; it is not a second injected Modelica
source.

## 3. Layer-controlled envelope

`use_construction_properties=True` makes the dynamic VDI reductions use the
explicit material layers below. The prescribed component U-values are still
retained for whole-component boundary conductance. “Layer-controlled” here
therefore means **layer-controlled dynamic RC properties within the existing
mixed mapping**, not that all U-values are discarded and recalculated solely
from layers.

| Assembly | Layers, outside to room side | Layer R (m²K/W) | Areal C (J/m²K) | Prescribed U (W/m²K) |
|---|---|---:|---:|---:|
| Wall | 9 mm wood siding; 66 mm fiberglass; 12 mm plasterboard | 1.789286 | 14,534.28 | 0.53 |
| Roof | 19 mm roof deck; 111.8 mm fiberglass; 10 mm plasterboard | 2.993214 | 18,169.94 | 0.33 |
| Floor | 1.003 m massless insulation proxy; 25 mm timber | 25.253571 | 19,500.00 | 0.038 |
| Window | 12 m² south glazing, \(g=0.769\) | — | — | 3.10 |

For each layer,

\[
R_j=\frac{d_j}{\lambda_j},\qquad
C_j=d_j\rho_jc_{p,j}.
\]

The explicit opaque-layer capacity represented before VDI reduction is
approximately

\[
C_{layers}=63.6(14534.28)+48(18169.944)+48(19500)
=2.733\ \mathrm{MJ/K}.
\]

For context, the separate BESTEST lightweight aggregate input is

\[
C_m=42167(48)=2.024\ \mathrm{MJ/K}.
\]

The difference is one reason the layer mapping should not be interpreted as a
unique translation of the aggregate BESTEST mass input.

## 4. Inside heat-transfer coefficient

Both cases use the adapter's total inside coefficient

\[
h_i=8.0\ \mathrm{W/(m^2K)}.
\]

The VDI implementation subtracts its fixed radiative coefficient of
5 W/(m²K), leaving the convective component

\[
h_{i,conv}=8-5=3\ \mathrm{W/(m^2K)}.
\]

This differs from the 9.1 W/(m²K) comparator convention. It is a discrete
factor setting in this experiment, not a fitted value.

## 5. Harmonised exterior long-wave treatment

The ordinary VDI path reads EPW horizontal infrared radiation and calculates
an exterior equivalent-temperature correction. In the harmonised setting,
both atmospheric and ground long-wave irradiance are replaced with the
reference black-body value at outdoor dry-bulb temperature:

\[
E_{atm}=E_{gnd}=\varepsilon_{ref}\sigma(T_{out}+273.15)^4,
\]

with

\[
\varepsilon_{ref}=0.93,qquad
\sigma=5.670374419\times10^{-8}\ \mathrm{W/(m^2K^4)}.
\]

This makes the inferred long-wave radiative temperature equal to outdoor air
temperature and removes the explicit VDI long-wave equivalent-temperature
offset. It does not disable the native short-wave solar calculation.

## 6. Modelica-split internal gains under no-IW

The sensible internal gain is constant:

\[
\Phi_{int}=200\ \mathrm{W}.
\]

Both cases apply

\[
\Phi_{int,air}=0.5\Phi_{int}=100\ \mathrm{W}.
\]

Because the topology has no IW branch, the entire radiant half is mapped to
AW:

\[
\Phi_{int,AW}=100\ \mathrm{W},\qquad
\Phi_{int,IW}=0.
\]

As with solar, this is the feasible no-IW projection of the comparator split;
it is not a literal reproduction of a three-node air/AW/IW allocation.

Heating and cooling HVAC delivery remain 100% convective at the air node in
all factorial cases, matching the comparator's ideal air heat-flow connector.

## 7. Airflow, geometry, schedules, and controls

These non-factor quantities are identical in F36 and F52:

| Quantity | Value |
|---|---:|
| Floor area | 48.0 m² |
| Volume | 129.6 m³ |
| Infiltration | 0.414 h⁻¹ |
| Air density | 1.20 kg/m³ |
| Air specific heat | 1005 J/(kg·K) |
| Ventilation conductance | 17.974224 W/K |
| Heating setpoint | 20 °C |
| Cooling setpoint | 27 °C |
| Internal sensible gain | 200 W, constant |
| Simulation | 8,760 hourly steps |

The infiltration conductance is

\[
H_{ve}=\rho c_p\frac{nV}{3600}
=1.20(1005)\frac{0.414(129.6)}{3600}
=17.974224\ \mathrm{W/K}.
\]

## 8. Solar-pipeline effect for the same physical IDs

| ID | Modelica solar H | Modelica solar C | Native VDI H | Native VDI C | \(\Delta H\) native − Modelica | \(\Delta C\) native − Modelica |
|---|---:|---:|---:|---:|---:|---:|
| F36 | 5.061489 | 5.109224 | 4.823417 | 5.678802 | −0.238072 | +0.569578 |
| F52 | 5.054931 | 5.181582 | 4.816070 | 5.748399 | −0.238862 | +0.566818 |

Switching only the solar pipeline moves both configurations from heating just
above the upper BESTEST bound to inside both annual-load intervals. The nearly
identical shifts also show that the small F36/F52 allocation distinction has
only a modest annual effect here:

\[
Q_H^{F52}-Q_H^{F36}=-0.007347\ \mathrm{MWh},
\]

\[
Q_C^{F52}-Q_C^{F36}=+0.069597\ \mathrm{MWh}.
\]

This does not establish either allocation as physically preferable. It shows
only that, within the tested no-IW configuration, both allocation alternatives
land inside the annual BESTEST rectangle when used with native VDI solar.

## Implementation sources

- Factor construction and allocation projection: `doc/case600_crosswalk_engine.py`
- Envelope and geometry inputs: `inputs/case600_defaults.json` and
  `inputs/case600_geometry.json`
- Passing-case extract:
  `results/case600_vdi_crosswalk/factorial_passing_case_features.csv`
- Paired solar results:
  `results/case600_vdi_crosswalk/factorial_mwh_paired_solar_comparison.csv`

