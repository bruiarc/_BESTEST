# Case 600 VDI No-IW Implementation Notes

## Topology

The diagnostic route uses `RClib.vdi6007.no_iw.PreparedVDI6007NoIWModel`.
It keeps the AW branch active and omits the IW branch completely.

## Modelica/IBPSA Evidence

IBPSA `RC.OneElement` is the structural reference: it has exterior-wall
storage, window heat transfer, room-air convection, ventilation ports, and
solar/internal gain paths, but no `AInt`, `RInt`, `CInt`, or `InteriorWall`
component. IBPSA `RC.TwoElements` makes `intWallRC`, IW convection, and IW
radiative links conditional on `AInt > 0`.

## Why 96 m2 IW Is Not Used

The previous `A_IW = 2 * floor_area = 96 m2` is an RClib adapter fallback when
no interior surfaces are present. Case 600 evidence reviewed so far does not
identify a physical partition/internal-mass component corresponding to that
area.

## RClib Reduction

The no-IW route is a parallel wrapper, not a mutation of the existing positive
IW implementation. It reuses AW component reduction, AW aggregation, equivalent
AW boundary temperature, window handling, ventilation, and thermostat logic.
It removes IW component reduction, IW aggregation, IW coefficients, IW state
updates, and AW/IW radiative resistance. Radiant internal gains and radiant
HVAC fractions are allocated to AW because the eligible room-surface area is
AW only.

No epsilon IW area/resistance/capacitance is used.

## Remaining Uncertainty

The Case 600 floor is still represented as an AW/boundary construction in this
diagnostic. Whether it should use a more specific VDI boundary treatment remains
UNRESOLVED.
