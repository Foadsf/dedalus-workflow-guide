# Dedalus 3 Visualization Guide: XDMF and VTK Export

## Overview

This guide documents the process of creating visualization files from Dedalus 3 simulation data for use in ParaView and other visualization tools. It covers the challenges encountered when migrating from Dedalus 2 to Dedalus 3 and provides working solutions.

## The Problem

The original `make_xdmf.py` script failed with:
```
ModuleNotFoundError: No module named 'dedalus.tools.xdmf'
```

**Root Cause**: The `dedalus.tools.xdmf` module that existed in Dedalus 2 has been removed or relocated in Dedalus 3.

## Key Lessons Learned

### 1. Dedalus 3 HDF5 File Structure Changes

Unlike earlier versions, Dedalus 3 stores coordinate information with hash-based names instead of predictable paths:

**Old expectation (Dedalus 2)**:
```
scales/x/1.0
scales/z/1.0
```

**Actual structure (Dedalus 3)**:
```
scales/x_hash_259ff677ed0cf648980d6e69fe3d2deb0dc82141
scales/z_hash_2b3e6c1ad6197e7bbb577c37c9be3babe1727daf
```

**Solution**: Use the `NAME` attribute to identify coordinate datasets:
```python
def find_coordinate_datasets(h5_file):
    """Find coordinate datasets by their NAME attribute."""
    x_key = None
    z_key = None

    for key in h5_file["scales"].keys():
        dataset = h5_file["scales"][key]
        if hasattr(dataset, 'attrs') and 'NAME' in dataset.attrs:
            name = dataset.attrs['NAME']
            if isinstance(name, bytes):
                name = name.decode('utf-8')
            if name == 'x':
                x_key = key
            elif name == 'z':
                z_key = key

    return x_key, z_key
```

### 2. File Structure Investigation is Critical

**Mistake**: Assuming the file structure without verification.

**Lesson**: Always inspect the actual HDF5 structure before writing conversion scripts:

```python
# Essential debugging script
with h5py.File(filepath, "r") as h5_file:
    print("Root level keys:", list(h5_file.keys()))
    h5_file.visititems(lambda name, obj: print(f"{name}: {obj}"))

    # Check attributes
    for key in h5_file["scales"].keys():
        dataset = h5_file["scales"][key]
        if dataset.attrs:
            print(f"{key} attributes:", dict(dataset.attrs))
```

### 3. XDMF Dimension Ordering

**Critical Detail**: XDMF expects dimensions in a specific order that may differ from how Dedalus stores data.

- Dedalus data shape: `(time, x, z)` → `(50, 256, 64)`
- XDMF topology expects: `(z_dims, x_dims)` → `"64 256"`

**Correct XDMF topology**:
```xml
<Topology TopologyType="2DRectMesh" Dimensions="64 256"/>
```

### 4. Data Array Indexing in XDMF

For time-dependent data, use proper HDF5 hyperslab notation:
```xml
<DataItem Format="HDF" Dimensions="64 256">
    filename.h5:/tasks/buoyancy[0,:,:]
</DataItem>
```

Where `[0,:,:]` selects the first time step and all spatial points.

## Working Solutions

### Solution 1: Manual XDMF Creation (Recommended)

**Advantages**:
- No data duplication (references original HDF5 files)
- Efficient for large datasets
- Native ParaView support
- Preserves time series information

**File**: `make_xdmf_manual.py`
```python
# Key components of the working solution:
# 1. Dynamic coordinate dataset discovery
# 2. Proper XML structure for XDMF 3.0
# 3. Correct dimension ordering
# 4. Time series support
```

### Solution 2: VTK Export

**Advantages**:
- Wide compatibility with visualization tools
- Self-contained files
- Good for smaller datasets

**Disadvantages**:
- Data duplication
- Larger file sizes
- Requires pyevtk dependency

**Installation**: `pip install pyevtk`

## Common Pitfalls and Solutions

### Pitfall 1: Hardcoded Dataset Paths
```python
# Wrong - will fail in Dedalus 3
x = h5_file["scales/x/1.0"][:]

# Correct - dynamic lookup
x_key, z_key = find_coordinate_datasets(h5_file)
x = h5_file[f"scales/{x_key}"][:]
```

### Pitfall 2: Incorrect XDMF Geometry Type
```xml
<!-- Wrong -->
<Geometry GeometryType="X_Y_Z">

<!-- Correct for 2D data -->
<Geometry GeometryType="VXVY">
```

### Pitfall 3: Missing Error Handling
```python
# Always include error handling
try:
    x_key, z_key = find_coordinate_datasets(h5_file)
    if not x_key or not z_key:
        raise ValueError("Could not find x and z coordinate datasets")
except Exception as e:
    print(f"Error processing {file_path.name}: {e}")
```

## Debugging Workflow

1. **Inspect file structure first**:
   ```bash
   python3 inspect_hdf5_structure.py
   ```

2. **Test with single file**:
   - Process one file at a time initially
   - Verify output in ParaView before batch processing

3. **Check XDMF file validity**:
   - XDMF files are XML - they should be readable as text
   - Verify paths reference existing datasets

4. **ParaView debugging**:
   - Check ParaView's Information panel for data ranges
   - Use "Find Data" to verify field values
   - Enable "Output Messages" for detailed error info

## File Organization

```
project/
├── snapshots/           # Dedalus HDF5 output
│   ├── snapshots_s1.h5
│   ├── snapshots_s1.xmf  # Generated XDMF files
│   └── ...
├── vtk_output/          # Generated VTK files
│   ├── snapshots_s1_t_000000.vtu
│   └── ...
├── make_xdmf_manual.py  # XDMF generation script
├── convert_to_vtk_fixed.py  # VTK conversion script
└── inspect_hdf5_structure.py  # Debugging utility
```

## ParaView Usage

### Opening XDMF Files:
1. File → Open → Select `.xmf` file
2. Reader: "Xdmf3ReaderT" (default)
3. Apply → Data should load with time series

### Time Animation:
- Use VCR controls at top
- Set frame rate in Animation View
- Export animation: File → Save Animation

## Performance Considerations

- **XDMF**: Best for large datasets, minimal overhead
- **VTK**: Better for small datasets, wider tool compatibility
- **Memory**: XDMF files reference data in-place, VTK files duplicate data

## Version Dependencies

- **Dedalus 3**: HDF5 structure with hashed coordinate names
- **ParaView**: Tested with 5.x series
- **Python libraries**: h5py, numpy, xml.etree.ElementTree (built-in)
- **Optional**: pyevtk for VTK export

## Conclusion

The transition from Dedalus 2 to Dedalus 3 requires adapting visualization workflows due to internal HDF5 structure changes. The key is understanding the actual file structure and adapting scripts accordingly, rather than assuming compatibility with older versions.

**Quick Start**: Use the `inspect_hdf5_structure.py` script first, then `make_xdmf_manual.py` for most visualization needs.

## Additional Resources

- [XDMF Format Documentation](https://www.xdmf.org/)
- [ParaView User Guide](https://docs.paraview.org/)
- [Dedalus Documentation](https://dedalus-project.readthedocs.io/)
- [HDF5 Python Documentation](https://docs.h5py.org/)
