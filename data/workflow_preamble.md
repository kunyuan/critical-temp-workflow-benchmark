# Workflow context (common to every task in this suite)

You are solving an instance of the **Monte Carlo finite-size scaling for
critical temperature** workflow. Problems of this class determine the critical
temperature (or critical coupling) of a classical spin model via Monte Carlo
simulation and finite-size scaling analysis. The workflow proceeds:

1. **Model and simulation setup** — define the spin model, lattice geometry,
   interaction parameters, and the Monte Carlo algorithm.
2. **Monte Carlo sampling** — generate equilibrium configurations and measure
   observables across a range of temperatures and system sizes L.
3. **Compute thermodynamic observables** — magnetization, susceptibility,
   specific heat, and the Binder cumulant U_L, used to locate the transition.
4. **Locate finite-size critical points** — extract a pseudo-critical
   temperature T_c(L) for each system size (e.g. susceptibility peak, Binder
   crossing).
5. **Finite-size extrapolation** — extrapolate T_c(L) to the thermodynamic
   limit (L→∞) to estimate the infinite-system critical temperature/coupling,
   and (where asked) the critical exponents from the scaling collapse.
6. **Report and interpret critical parameters** — summarize the critical
   temperature, exponents, transition order, and universality class.

Cross-check against known exact results where available (e.g. the 2D square-
lattice Ising model has T_c = 2/ln(1+√2) ≈ 2.269 J/k_B), and verify that
observables collapse onto universal scaling functions.

The task below is one concrete problem from this family. Apply the workflow;
the specific model, parameters, conventions, and requested outputs follow.

---

