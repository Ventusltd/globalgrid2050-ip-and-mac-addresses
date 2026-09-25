# Cell-to-grid model links

Intended architecture, not an implemented load-flow solver in this repository.

The same permanent identities can join authorised inspection evidence with
electrical connectivity and versioned models:

cell position -> physical module -> string -> inverter -> transformer -> 400 kV bus.

Each link must state which real assets or defined positions it connects and when
that relationship was valid. An inspection is an observation, not a conductor or
a load-flow branch. A geometric layout is not proof of electrical connectivity.

Required model layers:

- Cell/module: suitable electrical parameters and measured I-V data, irradiance,
  temperature, bypass paths and validated interpretation of inspection findings.
- String/DC collection: actual series/parallel connections, conductor impedances,
  operating state and MPPT behaviour. Preserve mismatch effects where relevant.
- Inverter: conversion efficiency, operating limits and active/reactive control.
- AC collection/grid: cable/transformer parameters, taps, switch states, network
  topology, external-grid boundary conditions and applicable controls.

Couple the appropriate models at defined interfaces. Transfer P/Q injections and
operating constraints to network models, retaining the source IDs and model
versions behind aggregates. A cell need not be represented as a separate 400 kV
load-flow bus. Use finer detail where it changes the question's answer.

Every run should identify measured inputs, assumptions, missing values, units,
time alignment, model versions, convergence/residuals and independent comparison.
Unknown inputs remain unknown; large GPU case counts cannot validate absent
parameters. GPU batches can explore weather, deterioration, layout and control
scenarios after the physics and data contracts are checked.

The public identity index enables future joining; no cell-to-400-kV model is
claimed as complete by publishing IDs. Contributors retain control of private
measurements. Public registration never implies permission to publish evidence.

Relevant established network-solver interface:
https://pandapower.readthedocs.io/en/latest/powerflow/ac.html

Inspection and identity handoff: [KUIPER-INSPECTION-LINKS.md](KUIPER-INSPECTION-LINKS.md).
