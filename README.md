# Dedalus on Windows: A Complete Workflow Guide

This repository documents a complete, successful workflow for installing the Dedalus framework on a Windows machine, running a parallel simulation, and visualizing the results using standard scientific tools like ParaView and VisIt.

The primary method relies on the Windows Subsystem for Linux (WSL2) to provide a compatible environment for Dedalus and its complex dependencies.

## Table of Contents
- [Dedalus on Windows: A Complete Workflow Guide](#dedalus-on-windows-a-complete-workflow-guide)
  - [Table of Contents](#table-of-contents)
    - [1. Installation via WSL2 and Conda](#1-installation-via-wsl2-and-conda)
    - [2. Running a Parallel Simulation](#2-running-a-parallel-simulation)
    - [3. Visualization Workflow](#3-visualization-workflow)
      - [The Challenge with HDF5 Files](#the-challenge-with-hdf5-files)
      - [Solution 1: Manual XDMF Generation (Recommended)](#solution-1-manual-xdmf-generation-recommended)
      - [Solution 2: VTK Conversion](#solution-2-vtk-conversion)
    - [4. Project Structure](#4-project-structure)
    - [5. Helper Scripts](#5-helper-scripts)

---

### 1. Installation via WSL2 and Conda

Dedalus is not natively supported on Windows. The recommended installation path is through WSL2.

1.  **Install WSL2**: Open PowerShell as an administrator and run `wsl --install`. Follow the prompts to set up the default Ubuntu distribution.

2.  **Install Miniconda in WSL2**: Download and run the Miniconda installer *inside your Ubuntu terminal*.

3.  **Create Conda Environment**: Create a dedicated environment for Dedalus.
    ```bash
    # Create the environment
    conda create -n dedalus3

    # Activate it
    conda activate dedalus3
    ```

4.  **Configure for Performance**: Disable threading for optimal MPI performance.
    ```bash
    conda env config vars set OMP_NUM_THREADS=1
    conda env config vars set NUMEXPR_MAX_THREADS=1
    # Deactivate and reactivate for changes to take effect
    conda deactivate
    conda activate dedalus3
    ```

5.  **Install Dedalus**: Install Dedalus and all its dependencies from the `conda-forge` channel.
    ```bash
    conda install -c conda-forge dedalus
    ```

6.  **Verify Installation**: Run the built-in test suite.
    ```bash
    python3 -m dedalus test
    ```
    A successful run will end with a summary of passed, skipped, and xfailed tests.

---

### 2. Running a Parallel Simulation

The `examples/00_rayleigh_benard_2d` directory contains a script for simulating 2D Rayleigh-Bénard convection.

1.  Navigate to the example directory inside your WSL terminal.
2.  Run the simulation in parallel using `mpiexec`. The following command uses 2 processor cores:
    ```bash
    mpiexec -n 2 python3 rayleigh_benard.py
    ```
3.  The simulation will run and create a `snapshots` directory containing the HDF5 output files. The script automatically merges the per-process files (e.g., `_p0.h5`, `_p1.h5`) into unified snapshot files (e.g., `snapshots_s1.h5`).

---

### 3. Visualization Workflow

#### The Challenge with HDF5 Files
Standard visualization tools like ParaView and VisIt may fail to correctly read the raw `.h5` files from Dedalus 3. This is because the files lack the specific mesh and time-series metadata (in a format like XDMF) that these tools expect for automatic parsing.

#### Solution 1: Manual XDMF Generation (Recommended)
The best solution is to generate XDMF (`.xmf`) files. These are small XML-based metadata files that link to the data within the larger HDF5 files, telling the visualization software how to interpret it.

1.  **Run the helper script** `helpers/make_xdmf_manual.py` from within your WSL2 terminal. It will automatically find the snapshot files and generate corresponding `.xmf` files.
    ```bash
    # Navigate to the example directory
    cd examples/00_rayleigh_benard_2d/
    # Run the script
    python3 ../../helpers/make_xdmf_manual.py
    ```
2.  **Open in ParaView/VisIt**:
    -   Launch your visualization tool on Windows.
    -   Go to `File -> Open`.
    -   Navigate to the `snapshots` directory via the WSL path: `\\wsl$\Ubuntu\<path_to_project>\snapshots\`.
    -   Select the `.xmf` file group (e.g., `snapshots_s*.xmf database`).
    -   The data will load correctly as a time series, ready for plotting.

#### Solution 2: VTK Conversion
As an alternative, you can convert the HDF5 data into the VTK format (`.vtu` files). This creates self-contained files that are widely supported, but they will be much larger as they duplicate the data.

1.  **Install dependency**:
    ```bash
    pip install pyevtk
    ```
2.  **Run the conversion script**:
    ```bash
    # Navigate to the example directory
    cd examples/00_rayleigh_benard_2d/
    # Run the script
    python3 ../../helpers/convert_to_vtk.py
    ```
3.  This will create a `vtk_output` directory containing a `.vtu` file for each time step, which can be opened directly in ParaView or VisIt.

---

### 4. Project Structure
The final repository is organized as follows:
```
.
├── .gitignore
├── README.md
├── lessons_learned.md
├── examples/
│   └── 00_rayleigh_benard_2d/
│       ├── rayleigh_benard.py      # Main simulation script
│       └── plot_snapshots.py       # Script to generate PNG frames
└── helpers/
    ├── inspect_hdf5_structure.py # Utility to check HDF5 file contents
    ├── make_xdmf_manual.py       # (Recommended) Generates XDMF files for ParaView/VisIt
    └── convert_to_vtk.py         # (Alternative) Converts HDF5 to VTK format
```

---

### 5. Helper Scripts
- **`helpers/inspect_hdf5_structure.py`**: A crucial debugging tool to print the internal group/dataset structure of an HDF5 file. Essential for adapting scripts to new Dedalus versions.
- **`helpers/make_xdmf_manual.py`**: The primary tool for preparing data for visualization.
- **`helpers/convert_to_vtk.py`**: An alternative visualization prep tool.
