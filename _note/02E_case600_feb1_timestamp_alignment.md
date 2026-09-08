# Case 600 — 1 February timestamp alignment

Both tracks are reported on the same completed-hour grid, without a shift.

* Modelica raw `PHea.y` and `PCoo.y` are `MovingAverage(delta=3600)` outputs.
  At time `t`, their definitions are the mean over `[t-3600, t]`; hence the
  value at 2,682,000 s is the completed interval 1 February 00:00–01:00.
  Before the first hour the block uses its documented shorter start-up window;
  this does not affect the 1 February slice.
* ISO loop index 0 reads EPW row 0 (`1-Jan`, hour 1), solves the first
  00:00–01:00 interval, and writes 3,600 s. It is therefore a completed-hour,
  not an instantaneous 00:00 value. No `.shift(1)` is used in the ISO runner,
  Modelica extractor, or profile slicer.
* `daily_slice` assigns an endpoint such as 2 February 00:00 to 1 February
  completed hour 24 for calendar labelling only. It does not move a value.

`results/case600/case600_feb1_timestamp_alignment_modelica_solar.csv` records
all 24 intervals for the controlled-forcing ISO track; the corresponding
`..._native.csv` records the native ISO track. Each has identical Modelica and
ISO raw timestamps and completed hours 1–24. The notebook displays hours
6–12 and 17–22 before plotting the aligned profile.
