1. **IW topology**

   * [ ] Is an internal-wall branch included or excluded?
   * [ ] If excluded, how are its thermal storage and radiant-receiving functions redistributed?

2. **Solar/source allocation**

   * [ ] How is transmitted solar divided between air and thermal surfaces/nodes?
   * [ ] Is this allocation native to the VDI formulation, inherited from the comparator, or adapted because some nodes are absent?

3. **Envelope convention**

   * [ ] Which envelope information controls steady-state transmission and which controls dynamic thermal response?
   * [ ] Are prescribed \(U\)-values and material-layer properties being combined consistently?

4. **Inside heat-transfer treatment**

   * [ ] What inside heat-transfer coefficient/convention is assumed, and where does that assumption originate?
   * [ ] How is the total coefficient divided into convective and radiative components?

   Here you can subsequently record the current implementation, e.g. **total coefficient = 8**, as an assumed/default VDI-side setting rather than embedding it in the methodological question.

5. **Exterior long-wave treatment**

   * [ ] Is exterior long-wave radiation treated natively or harmonised with the comparator boundary condition?
   * [ ] If harmonised, exactly which physical contribution is suppressed or replaced?

6. **Internal-gain allocation**

   * [ ] How are sensible internal gains divided between air and thermal surfaces/mass?
   * [ ] Is the split prescribed by the benchmark, taken from the comparator formulation, or introduced as a modelling assumption?

   This is where a current **50/50** split can be recorded. Again, the checklist should ask *what the split is and why*, rather than assume that 50/50 is universally correct.

7. **Airflow / infiltration**    
   * [ ] What airflow or infiltration convention is used, and what is its original source (whether it has been converted as per the altitude)?
   * [ ] Is the value a direct benchmark input, a conversion from another airflow quantity, or a modelling assumption?

8. **Geometry, schedules and controls**

   * [ ] Which geometry, operating schedules, setpoints and HVAC-control assumptions are of fidelity to what has been proposed (e.g., list HVAC schedules that are finally used, as some case may be tricky where default minimal value of mechanical ventilation may be triggered whereas we have our own stipulation or interpretation regarding how one building is actually operated)?
  
   * [ ] 2 times of ['FLOOR_AREA'] is a default setting as fallback values, and I would like to know if it is used (which is dangerous as such value should be easily obtained but we use juvenile fallback)
