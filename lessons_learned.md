# Lessons Learned: Dedalus 3 Simulation and Visualization

## Overview

This document captures hard-learned lessons from setting up Dedalus 3 simulations and creating effective visualizations. These insights come from real troubleshooting experiences and should help avoid common pitfalls.

## Critical API Changes in Dedalus 3

### 1. Missing XDMF Module
**Problem**: Scripts using `from dedalus.tools.xdmf import XDMF` fail with `ModuleNotFoundError`.

**Root Cause**: The `dedalus.tools.xdmf` module was removed in Dedalus 3.

**Solution**: Create XDMF files manually using Python's built-in XML libraries.

### 2. Grid Shape Method Removed
**Problem**: `dist.local_grid_shape(scales=1)` throws `AttributeError`.

**Solution**: Use coordinate array shapes directly:
```python
# Wrong (Dedalus 2)
shape = dist.local_grid_shape(scales=1)

# Correct (Dedalus 3)
shape = z.shape  # or u['g'][1].shape
```

### 3. HDF5 Structure Changes
**Major Change**: Coordinate datasets now have hash-based names instead of predictable paths.

**Old structure**:
```
scales/x/1.0
scales/z/1.0
```

**New structure**:
```
scales/x_hash_259ff677ed0cf648980d6e69fe3d2deb0dc82141
scales/z_hash_dbaa493059a5260a1784ae85d009bb09723a1cd0
```

**Solution**: Use the `NAME` attribute to find coordinates dynamically:
```python
def find_coordinate_datasets(h5_file):
    x_key = z_key = None
    for key in h5_file["scales"].keys():
        dataset = h5_file["scales"][key]
        if hasattr(dataset, 'attrs') and 'NAME' in dataset.attrs:
            name = dataset.attrs['NAME']
            if isinstance(name, bytes):
                name = name.decode('utf-8')
            if name == 'x': x_key = key
            elif name == 'z': z_key = key
    return x_key, z_key
```

## Simulation Physics Lessons

### Kelvin-Helmholtz Instability Requirements
**Problem**: Initial simulation showed no instability development - velocity remained constant and no vortex formation occurred.

**Root Causes**:
1. **Insufficient perturbations**: Random noise of amplitude `1e-4` was too weak
2. **High viscosity**: `nu = 1e-4` suppressed instability growth
3. **Wrong perturbation type**: Random noise is less effective than structured perturbations

**Working Solution**:
```python
# Reduce viscosity to allow instability growth
nu = 1e-5
kappa = 1e-5

# Use structured sinusoidal perturbations
u["g"][1] += 0.1 * np.sin(2 * np.pi * x / Lx) * np.exp(-(z/0.2)**2)
```

**Key Indicators of Success**:
- W-component (vertical velocity) must be non-zero
- Scalar field range should expand beyond initial [-1,1] bounds
- Vorticity should show strong values (hundreds, not single digits)

## Visualization Challenges

### XDMF vs VTK Trade-offs
**XDMF Issues**:
- ParaView crashes frequently with custom XDMF files
- Dimension ordering is critical and error-prone
- Array size mismatches cause cryptic warnings in VisIt

**VTK Advantages**:
- More reliable loading in both ParaView and VisIt
- Self-contained files (no dependency on HDF5 structure)
- Better error messages when problems occur

**Recommendation**: Use VTK format for initial visualization, switch to XDMF only for very large datasets where file size matters.

### Vector Field Handling
**Problem**: Dedalus velocity fields have shape `(time, components, x, z)` but VTK expects separate scalar components.

**Solution**:
```python
if task == "velocity":
    u_component = data[0, :, :].flatten(order="F")
    w_component = data[1, :, :].flatten(order="F")
    v_component = np.zeros_like(u_component)  # Dummy for 3D VTK
    pointData["velocity"] = (u_component, v_component, w_component)
```

### Data Range Issues
**Common Problem**: Simulation data appears as uniform color in visualization tools.

**Debugging Steps**:
1. Check actual data ranges with inspection scripts
2. Manually set color scale ranges in ParaView/VisIt
3. Verify you're looking at evolved timesteps, not initial conditions
4. Check if field values are reasonable for the physics

## Development Workflow Lessons

### Always Inspect First
**Critical Habit**: Never assume HDF5 file structure. Always run inspection scripts before writing conversion code.

**Essential Debug Script**:
```python
# Check data ranges and evolution
with h5py.File(filepath, "r") as h5_file:
    for field in ['scalar', 'velocity', 'vorticity']:
        data = h5_file[f"tasks/{field}"][:]
        print(f"{field}: shape={data.shape}, range=[{data.min():.3f}, {data.max():.3f}]")
```

### Directory Organization Matters
**Problem**: Dedalus simulations create output relative to the current working directory, not the script location.

**Solution**: Always run simulations from their intended directory:
```bash
cd examples/01_kelvin_helmholtz_2d/
mpiexec -n 4 python3 kelvin_helmholtz.py
```

### Logging Verbosity
**Problem**: Default Dedalus logging is extremely verbose and unhelpful for monitoring progress.

**Solution**: Reduce logging levels and create custom progress indicators:
```python
logging.getLogger("subsystems").setLevel(logging.WARNING)
logging.getLogger("solvers").setLevel(logging.WARNING)
```

## Performance and Debugging

### Simulation Parameters
**Key Insight**: Physical instabilities require the right balance of:
- **Time scales**: Instability growth time vs. simulation time
- **Spatial resolution**: Adequate grid points to resolve developing structures
- **Dissipation**: Low enough viscosity/diffusivity for growth, high enough for stability
- **Perturbations**: Strong enough to overcome numerical diffusion

### When Simulations Fail Silently
**Warning Signs**:
- Max velocity stays constant throughout simulation
- Scalar field standard deviation only decreases (indicates pure diffusion)
- Vertical velocity component remains zero in shear flows

**Action**: Don't waste time on visualization - fix the physics first.

### File Format Strategy
1. **Start with VTK** for reliable visualization
2. **Use inspection scripts** to verify data before creating visualizations
3. **Test with small datasets** before running long simulations
4. **Only use XDMF** if file sizes become prohibitive

## Tools and Dependencies

### Essential Python Packages
- `h5py`: HDF5 file reading
- `pyevtk`: VTK file generation (`pip install pyevtk`)
- `xml.etree.ElementTree`: XDMF generation (built-in)

### Visualization Software
- **ParaView**: Better for publication-quality figures, more prone to crashes with custom formats
- **VisIt**: More robust with problematic files, better for exploratory analysis

## Common Error Patterns

### Data Shape Mismatches
**Symptom**: "Bad array shape" or "Array size mismatch" errors
**Cause**: Assuming Dedalus 2 array ordering in Dedalus 3
**Fix**: Always check actual array shapes before processing

### Silent Failures
**Symptom**: Code runs without errors but produces meaningless visualizations
**Cause**: Physics parameters prevent instability development
**Fix**: Verify simulation produces expected physical behavior before visualization

### Path Dependencies
**Symptom**: Files created in unexpected locations
**Cause**: Running scripts from wrong directory
**Fix**: Use absolute paths or ensure correct working directory

## Success Indicators

A working simulation should show:
- **Field evolution**: Significant changes in data ranges over time
- **Physical realism**: Velocity fields consistent with expected flow patterns
- **Instability growth**: Exponential or rapid growth phases followed by nonlinear development
- **Clean visualization**: Data loads without errors and shows expected structures

These lessons represent real debugging time that can be avoided by following these guidelines.
