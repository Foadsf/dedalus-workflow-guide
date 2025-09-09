import h5py
import numpy as np
import pathlib
from pyevtk.hl import gridToVTK


def find_coordinate_datasets(h5_file):
    """Find the coordinate datasets by their NAME attribute."""
    x_key = None
    z_key = None

    for key in h5_file["scales"].keys():
        dataset = h5_file["scales"][key]
        if hasattr(dataset, "attrs") and "NAME" in dataset.attrs:
            name = dataset.attrs["NAME"]
            if isinstance(name, bytes):
                name = name.decode("utf-8")
            if name == "x":
                x_key = key
            elif name == "z":
                z_key = key

    return x_key, z_key


def convert_hdf5_to_vtk():
    """Convert Dedalus HDF5 files to VTK format."""

    snapshots_dir = pathlib.Path("snapshots")
    vtk_dir = pathlib.Path("vtk_output")
    vtk_dir.mkdir(exist_ok=True)

    for file_path in sorted(snapshots_dir.glob("snapshots_s*.h5")):
        print(f"Processing {file_path.name}")

        with h5py.File(file_path, "r") as h5_file:
            # Get time data
            sim_time = h5_file["scales/sim_time"][:]

            # Find coordinate datasets
            x_key, z_key = find_coordinate_datasets(h5_file)
            if not x_key or not z_key:
                raise ValueError("Could not find x and z coordinate datasets")

            x = h5_file[f"scales/{x_key}"][:]
            z = h5_file[f"scales/{z_key}"][:]

            # Get tasks
            tasks = list(h5_file["tasks"].keys())

            # Process each timestep
            for i, t in enumerate(sim_time):
                # Prepare data dictionary
                cellData = {}
                for task in tasks:
                    # Data is stored as (time, x, z), we need (x, z) for this timestep
                    data = h5_file[f"tasks/{task}"][i, :, :]
                    # VTK expects flattened data in a specific order
                    cellData[task] = data.flatten(order="F")  # Fortran order for VTK

                # Create output filename
                output_name = vtk_dir / f"{file_path.stem}_t_{i:06d}"

                # Write VTK file
                # Note: VTK expects 3D coordinates, so we add a dummy Y coordinate
                y = np.array([0.0])  # Single Y coordinate for 2D data

                # Create coordinate meshes
                X, Y, Z = np.meshgrid(x, y, z, indexing="ij")

                gridToVTK(str(output_name), X, Y, Z, cellData=cellData)

        print(f"Converted {file_path.name} to VTK format")


if __name__ == "__main__":
    try:
        convert_hdf5_to_vtk()
        print("VTK conversion complete.")
    except Exception as e:
        print(f"Error during conversion: {e}")
