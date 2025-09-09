# Example 01: 2D Kelvin-Helmholtz Instability

This example simulates the development of the Kelvin-Helmholtz instability in a 2D shear flow.

### The Physics

The Kelvin-Helmholtz instability is a fundamental fluid dynamic process that occurs when there is a velocity difference across an interface between two fluids or in a single fluid with a shear layer. This shear creates vortices that roll up and evolve into the characteristic "billow" or "wave" pattern.

In this simulation:
- We model an incompressible fluid.
- The initial condition is a smooth horizontal shear flow: the fluid moves to the right (`+x`) in the top half of the domain and to the left (`-x`) in the bottom half.
- A passive scalar field `s` is initialized to match the velocity profile, acting as a dye to visualize the mixing of the two layers.
- Small random perturbations are added to the vertical velocity field to provide a seed for the instability to grow.

### Running the Simulation

1.  **Activate Conda Environment**: Make sure your `dedalus3` environment is active.
    ```bash
    conda activate dedalus3
    ```

2.  **Run in Parallel**: Execute the script using `mpiexec`. Using 4 cores is a good starting point.
    ```bash
    mpiexec -n 4 python3 kelvin_helmholtz.py
    ```

3.  **Output**: The simulation will create a `snapshots` directory and save `.h5` data files containing the scalar field, velocity field, and vorticity at regular time intervals.

### Visualizing the Results

The simulation output is in HDF5 format. To view it in ParaView or VisIt, you must first generate XDMF metadata files.

1.  **Generate XDMF files**: Use the helper script from the parent directory.
    ```bash
    python3 ../../helpers/make_xdmf_manual.py
    ```
    This will create `.xmf` files for each `.h5` snapshot.

2.  **Open in ParaView/VisIt**:
    -   Launch your visualization software.
    -   Open the `.xmf` file group from the `snapshots` directory.
    -   Create a **Pseudocolor** plot of the `scalar` or `vorticity` field.
    -   Use the time controls to play the animation and watch the instability develop.

You should see the initial flat layers evolve into the beautiful, swirling vortices characteristic of the Kelvin-Helmholtz instability.
