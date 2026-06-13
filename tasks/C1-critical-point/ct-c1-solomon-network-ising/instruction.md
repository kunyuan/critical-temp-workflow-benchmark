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

# Environment & answer protocol (common to every task in this suite)

## Compute environment
- Local: Python 3 with numpy and scipy, for prototyping and light Monte Carlo.
- **Cloud HPC (a cloud HPC platform sandbox)**: for the heavy Monte Carlo and
  finite-size-scaling this workflow needs at research scale (large lattices,
  long thermalization, many disorder realizations for spin glasses, 3D/4D
  systems), submit work to a a cloud HPC platform sandbox via the `a cloud HPC platform` CLI:
  ```bash
  <cloud-HPC CLI command>
  <cloud-HPC CLI command>
                                             #   or <machine-sku> / <machine-sku> for GPU MC)
  <cloud-HPC CLI command>
  <cloud-HPC CLI command>
  <cloud-HPC CLI command>
  ```
  Discipline: reuse running sandboxes; SAVE results (files read) BEFORE
  `kill` — sandbox data is lost permanently after kill; kill promptly when
  finished. Scale your lattices, statistics, and disorder averaging to the
  precision the task asks for — do not let local-compute limits cap your
  finite-size extrapolation.

### Performance: use a fast language and parallelize (Monte Carlo is heavy)
- The default sandbox is small (**1 core, 2 GB**). For real MC+FSS, provision
  a multi-core sandbox: `<cloud-HPC CLI command>` lists SKUs (`<machine-sku>` 2-core is
  free; up to `<machine-sku>` / `<machine-sku>`). Create a larger template once,
  e.g. `a cloud HPC platform sdbx template create --name <machine-sku> --image <default-image> --cpu 16
  --memory 32Gi`, then `<cloud-HPC CLI command>`.
- **Do not run production Monte Carlo in pure Python — it is ~100× too slow**
  and will not reach the needed statistics. Implement the MC kernel in a
  COMPILED language (gcc / g++ / gfortran are preinstalled; numba, Julia, Rust
  are NOT). Vectorized-numpy checkerboard updates are the minimum acceptable
  fallback for small 2D models.
- **Parallelize**: use OpenMP threads in the C/C++/Fortran kernel, and/or run
  independent temperature points, system sizes L, and disorder realizations
  concurrently across the sandbox cores (`nproc`). Spin-glass / large-3D/4D
  tasks are infeasible without this.
- **Run long simulations asynchronously**: `<cloud-HPC CLI command>`
  returns a pid immediately; poll for completion and then `files read` the
  output. A single blocking `exec` that runs for minutes will time out / stall
  — never wait synchronously on a long run.

## Answer protocol
- Write your final answer to `pred.json` in the task directory — a single JSON
  object whose keys are exactly the quantity ids the task requests (no extra
  keys). Numeric values as JSON numbers; categorical answers exactly as the
  task's allowed-label set specifies.
- Report critical temperatures/couplings in the units the task states (e.g.
  T_c in J/k_B). Give ≥4 significant digits for numeric answers unless told
  otherwise.
- Equilibration, system sizes, and finite-size extrapolation are your
  responsibility: use the thermodynamic-limit extrapolation (L→∞), not a
  single finite L.
- **Derivation log (required)**: alongside `pred.json`, write `derivation.md`
  organized by the workflow steps (model setup → sampling → observables →
  finite-size critical points → extrapolation → report): the method, where it
  ran (local vs which sandbox), system sizes and statistics, the
  crossing/peak analysis, the extrapolation, and convergence checks. Not
  scored against the gold, but collected.

---

Consider the equilibrium ferromagnetic Ising model on a Solomon network. The network is constructed from two one-dimensional rings each of length L (total N=2L sites). Each spin S_i = +/-1. Spin i in chain 1 interacts with its two nearest neighbors i+/-1 in chain 1 AND with spins P(i)-1 and P(i)+1 in chain 2, where P is a completely random permutation of site indices (quenched disorder); each spin thus has exactly 4 nearest neighbors. The Hamiltonian is H = -J sum_{<ij>} S_i S_j with J=1, k_B=1. Spin flips follow heat-bath dynamics with flip probability P_i = 1/(1+exp(-2E_i/T)) where E_i = -J S_i sum_j S_j. Using Monte Carlo simulation with finite-size scaling (FSS) on systems from N=30,000 to 100,000 sites, with the Binder cumulant U_4 = 1 - <m^4>/(3<m^2>^2) to locate the critical point, determine the critical temperature T_c of the second-order ferromagnetic phase transition. Output a JSON object {"kBTc_over_J": <value>}.
