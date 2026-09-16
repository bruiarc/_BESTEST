# VDI 6007 mass-area and surface-coupling fidelity audit

## Scope and verdict

This is a source-level Task 2 audit of the implemented VDI 6007 equations and
the Case 600/900 BESTEST adapters. It does not use annual-load agreement as a
fidelity criterion, does not change the verified Case 900 materials, and does
not run the wider 6XX/9XX sequence.

| Question | Verdict |
|---|---|
| Does ISO 13790 effective mass area (`facMas`, `A_m`, or `A_m/A_t`) enter the VDI calculation? | **No.** The shared effective-area field is input metadata only. The shared aggregate heat capacity is used only in an adapter reconciliation diagnostic. |
| Are the ordinary two-group VDI AW/IW area and coupling equations implemented consistently with the documented VDI equations? | **Yes.** Physical component areas drive reduction, aggregation, source allocation, convection, radiation, and boundary coupling. |
| Is the Case 600 F36/F52 no-IW route demonstrated to be native/normative VDI 6007? | **No.** It is a documented, internally coherent one-group extension, not the standard AW/IW delta/star topology and not an epsilon-IW limit. |
| Is there a confirmed algebra or area-semantics bug in that no-IW route? | **No.** The qualification is applicability/model topology, not a demonstrated coding error. |
| Does Case 900 require an ISO-style effective mass area? | **No.** Its verified material layers and physical component areas supply the dynamic inputs directly. |

Accordingly, there is no reason to import ISO effective-mass-area semantics or
restore the unsupported 96 m2 IW fallback. The broader paired sequence has a
**conditional go-ahead as a study of the declared VDI-derived no-IW BESTEST
model**. It does not yet have an unconditional go-ahead if the intended claim
is strict, normative VDI 6007 compliance: that claim requires authoritative
evidence that the one-group AW-only degeneration is within the guideline's
scope, or a benchmark-supported physical IW construction.

## 1. VDI area semantics

The implementation uses actual room-side component area, not an ISO effective
mass area:

1. Each material layer is reduced from its areal resistance `s/lambda` and
   areal capacity `rho*c*s`; component area enters the component reduction.
   See `RC_br/RClib/vdi6007/components.py`, Eqs. (1)-(17).
2. Reduced AW and IW components are aggregated separately as parallel dynamic
   impedances at the VDI room aggregation period. Massless windows alter the
   associated opaque AW first resistance while retaining that opaque
   component's reduced capacitance. See
   `RC_br/RClib/vdi6007/aggregation.py`, Eqs. (19)-(27).
3. Internal radiant sources use
   `f_IW = A_IW/A_room` and `f_AW = A_AW/A_room`. Transmitted sources use the
   VDI orientation exclusion area in the denominator. See
   `RC_br/RClib/vdi6007/sources.py`, Eqs. (43)-(46).
4. Surface convection uses `R_alpha = 1/(alpha*A)`. AW/IW long-wave exchange
   uses the limiting physical AW or IW area. See
   `RC_br/RClib/vdi6007/components.py` and
   `RC_br/RClib/vdi6007/aggregation.py`, Eqs. (29)-(31).

`effective_mass_area_per_floor_area` is accepted by the shared-case input
schema but has no consumer in VDI component reduction, aggregation, source
allocation, or solution. Likewise,
`thermal_capacitance_per_floor_area * floor_area` is calculated only as an
adapter diagnostic and compared with reduced `C1_AW + C1_IW`; it does not set
either VDI capacitance. See `RC_br/RClib/vdi6007/_BR_.py` and
`RC_br/RClib/vdi6007/case_adapter.py`.

Thus ISO quantities such as `facMas`, `A_m`, and `A_m/A_t` are not being
silently imported into the VDI physics. A difference between the VDI reduced
capacity and an ISO aggregate capacity is a cross-model diagnostic, not an
input override.

## 2. VDI surface-coupling equations

### Standard AW/IW route

The ordinary two-group path constructs three room-side links:

- AW-to-air convection from the parallel component resistances
  `1/[(alpha_total - 5) A_AW]`;
- IW-to-air convection from the corresponding IW resistances;
- AW-to-IW long-wave exchange
  `1/[5 min(A_AW,A_IW)]`, implemented component-wise and combined in
  parallel.

The fixed 5 W/(m2 K) radiative coefficient is removed from the supplied total
inside coefficient to obtain convection (VDI Eq. 30). These three delta links
are converted to the central-star branches with Eqs. (55)-(57) in
`RC_br/RClib/vdi6007/network.py`. Dynamic mass-to-surface coupling enters
through the reduced component `R1` and `C1` and their AW/IW aggregate response
coefficients. Exterior coupling enters through whole-component U-value
conductances, equivalent exterior temperatures, the residual AW resistance,
and the exterior surface resistance. The hourly air and surface balances are
then evaluated by `RC_br/RClib/vdi6007/solver.py`, Eqs. (75) and (96)-(107).

No comparator-specific coefficient or ISO node topology was found in this
standard coupling path.

### BESTEST no-IW route

F36/F52 use `RC_br/RClib/vdi6007/no_iw.py`. That module explicitly removes
IW reduction, IW capacitance/state, IW surface coupling, and the AW/IW
radiative link. It sets `A_room = A_AW`, allocates all eligible non-air radiant
heat to AW, and retains the AW-to-air convective link

`R_conv,AW = 1 / [(alpha_total - 5) A_AW]`.

The missing 5 W/(m2 K) term is not an omitted AW-to-air convective term: it is
the coefficient reserved for surface-to-surface long-wave exchange. With only
one collapsed surface-temperature group, there is no distinct receiving
surface node on which to place that exchange. This makes the route internally
consistent as a one-group reduction, but it is structurally different from
the standard VDI AW/IW delta/star network.

The module calls itself the structural equivalent of `IBPSA RC.OneElement`,
states that it is not an epsilon-IW limit, and the companion implementation
notes call it diagnostic. The package assumptions also warn that an AW-only
or IW-only capacity topology degenerates to one thermal storage node and may
fall outside guideline accuracy. Therefore the no-IW path cannot presently be
labelled proven normative VDI 6007 solely from repository evidence.

## 3. Case 600 audit

### Mass-area verdict: no implementation defect

Case 600's VDI dynamic behavior is derived from the physical AW layer chains
and their physical surface areas. ISO effective mass area is not used. The
generic adapter's fallback `A_IW = 2*A_floor = 96 m2` is explicitly marked a
provisional floor/ceiling proxy; it is not recovered from BESTEST evidence and
is not native VDI semantics. F36/F52 correctly avoid presenting that invented
area as benchmark provenance by routing through the no-IW model.

The resulting difference from an ISO 5R1C effective mass node is a legitimate
model-form difference, not evidence of a VDI area bug. Neither `A_m` nor the
96 m2 proxy should be inserted to force agreement.

### Surface-coupling verdict: no confirmed algebra defect; unresolved scope

The standard VDI two-group surface network is implemented faithfully to the
coded equations. Case 600 F36/F52, however, do not use that topology. Their
AW-only surface-to-air treatment is internally coherent and explicitly
documented, but repository evidence establishes it only as a diagnostic
extension. The lack of a separate IW surface also necessarily removes
AW-to-IW radiation and collapses operative surface temperature to the AW
surface temperature.

That is not a demonstrated coefficient, sign, or resistance-assembly bug. It
is an unresolved applicability question: whether a one-storage-group
degeneration is acceptable for the intended VDI 6007 claim. Treating the
difference from ISO as an error and adding ISO topology would be unjustified.

## 4. Case 900 audit

The verified heavyweight wall and raised-floor layers, plus the retained Case
600 roof layers, enter the same component transfer-matrix reduction using
their physical areas. Heavyweight capacity residing in AW is consistent with
those exterior/ground boundary constructions. It need not be moved to an
abstract ISO mass node, and the recorded Case 900 effective-mass-area factor
2.43 is neither needed nor used.

Case 900 inherits the same no-IW topology qualification as Case 600. Replacing
the former scaled-capacity proxy with verified layers fixed material
provenance; it did not prove that the AW-only extension is normative VDI 6007.
Conversely, the presence of heavyweight storage in AW is not itself a
structural defect. No Case 900 material change is recommended by this audit.

## 5. Actual implementation issues

No mass-area or surface-coupling algebra defect was established in the paths
audited.

One adapter issue remains if the generic positive-IW route is used for these
BESTEST cases: absent explicit interior surfaces, it fabricates
`A_IW = 2*A_floor`. The code correctly labels this provisional, but it must not
be reported as an ASHRAE 140 construction or native VDI-derived quantity.

The F36/F52 no-IW route has a claim/scope issue rather than a demonstrated
calculation bug: its one-group equations are a repository extension, while
the documented standard network expects positive AW and IW groups.

## 6. Legitimate model-form differences

- VDI derives dynamic resistance and capacity from material layers and actual
  component areas; ISO 13790 may use aggregate `C_m` and effective `A_m`.
- VDI allocates radiation using eligible receiving-surface areas and, for
  transparent sources, orientation exclusion. ISO comparator fractions need
  not match this allocation.
- VDI's normal surface network contains separate AW and IW surface groups,
  convection to room air, and inter-group radiation before delta/star
  conversion. This need not reproduce the ISO 5R1C topology.
- In the declared no-IW extension, all non-air radiant heat is projected onto
  AW and there is no separate inter-surface radiation branch. This is a
  consequence of the selected reduced topology, not proof that an ISO mass
  area should be introduced.

## 7. Recommended code changes, if any

No physics code or Case 900 material change is warranted from this audit.

Before claiming strict native/normative VDI 6007 compliance, obtain an
authoritative VDI source or independent validated implementation confirming
that the AW-only one-group degeneration is permitted. If it is permitted,
document that evidence beside `no_iw.py` and the BESTEST report. If it is not,
the remedy is to build a physically evidenced VDI AW/IW topology—not to use
ISO `A_m`, tune an IW area, or restore the unsupported 96 m2 fallback.

For the broader paired 6XX/9XX run, retain the current model unchanged and
label results as the declared **VDI-derived no-IW BESTEST application**. Hold
only the stronger claim of normative VDI 6007 compliance pending the evidence
above.

## Evidence paths reviewed

- `RC_br/RClib/vdi6007/components.py`
- `RC_br/RClib/vdi6007/aggregation.py`
- `RC_br/RClib/vdi6007/network.py`
- `RC_br/RClib/vdi6007/sources.py`
- `RC_br/RClib/vdi6007/orchestration.py`
- `RC_br/RClib/vdi6007/solver.py`
- `RC_br/RClib/vdi6007/no_iw.py`
- `RC_br/RClib/vdi6007/case_adapter.py`
- `RC_br/RClib/vdi6007/_BR_.py`
- `RC_br/RClib/vdi6007/z_ASSUMPTIONS_AND_UNKNOWNS.md`
- `2_validation/_BESTEST/2_vdi/doc/case600_no_iw_implementation_notes.md`
- `2_validation/_BESTEST/2_vdi/doc/case600_F36_F52_implementation.md`
- `2_validation/_BESTEST/2_vdi/doc/bestest_vdi_transfer_engine.py`
- `2_validation/_BESTEST/2_vdi/inputs/case900_defaults.json`
