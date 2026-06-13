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

