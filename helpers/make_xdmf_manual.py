import h5py
import numpy as np
import pathlib
import xml.etree.ElementTree as ET


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


def create_xdmf_file(h5_filepath):
    """Create XDMF file for a given HDF5 snapshot file."""

    # Create XDMF filename
    xdmf_filepath = h5_filepath.with_suffix(".xmf")

    # Read HDF5 file structure
    with h5py.File(h5_filepath, "r") as h5_file:
        # Get metadata
        tasks = list(h5_file["tasks"].keys())
        sim_time = h5_file["scales/sim_time"][:]

        # Find coordinate datasets
        x_key, z_key = find_coordinate_datasets(h5_file)
        if not x_key or not z_key:
            raise ValueError("Could not find x and z coordinate datasets")

        x = h5_file[f"scales/{x_key}"][:]
        z = h5_file[f"scales/{z_key}"][:]

        # Create XML structure
        xdmf_root = ET.Element("Xdmf", Version="3.0")
        domain = ET.SubElement(xdmf_root, "Domain")

        # Create temporal grid collection
        temporal_grid = ET.SubElement(
            domain,
            "Grid",
            Name="Temporal_Grid",
            GridType="Collection",
            CollectionType="Temporal",
        )

        # Add each time step
        for i, t in enumerate(sim_time):
            # Create grid for this timestep
            grid = ET.SubElement(
                temporal_grid, "Grid", Name=f"Grid_t_{t:.6f}", GridType="Uniform"
            )

            # Add time information
            time_elem = ET.SubElement(grid, "Time", Value=str(t))

            # Add topology (2D rectangular mesh)
            # Note: Dedalus stores data as (x, z), but XDMF expects (z, x) order
            topology = ET.SubElement(
                grid,
                "Topology",
                TopologyType="2DRectMesh",
                Dimensions=f"{len(z)} {len(x)}",
            )

            # Add geometry
            geometry = ET.SubElement(grid, "Geometry", GeometryType="VXVY")

            # X coordinates (stored as VX in XDMF)
            x_item = ET.SubElement(
                geometry,
                "DataItem",
                Dimensions=str(len(x)),
                NumberType="Float",
                Precision="8",
                Format="HDF",
            )
            x_item.text = f"{h5_filepath.name}:/scales/{x_key}"

            # Z coordinates (stored as VY in XDMF)
            z_item = ET.SubElement(
                geometry,
                "DataItem",
                Dimensions=str(len(z)),
                NumberType="Float",
                Precision="8",
                Format="HDF",
            )
            z_item.text = f"{h5_filepath.name}:/scales/{z_key}"

            # Add data attributes
            for task in tasks:
                attribute = ET.SubElement(
                    grid, "Attribute", Name=task, AttributeType="Scalar", Center="Node"
                )

                # Note: Data dimensions need to be transposed for XDMF
                data_item = ET.SubElement(
                    attribute,
                    "DataItem",
                    Dimensions=f"{len(z)} {len(x)}",
                    NumberType="Float",
                    Precision="8",
                    Format="HDF",
                )
                data_item.text = f"{h5_filepath.name}:/tasks/{task}[{i},:,:]"

    # Write XDMF file
    tree = ET.ElementTree(xdmf_root)
    ET.indent(tree, space="  ", level=0)  # Pretty formatting
    tree.write(xdmf_filepath, xml_declaration=True, encoding="utf-8")

    return xdmf_filepath


# Main execution
if __name__ == "__main__":
    snapshots_dir = pathlib.Path("snapshots")

    for file_path in sorted(snapshots_dir.glob("snapshots_s*.h5")):
        print(f"Processing {file_path.name}")
        try:
            xdmf_file = create_xdmf_file(file_path)
            print(f"Created {xdmf_file.name}")
        except Exception as e:
            print(f"Error processing {file_path.name}: {e}")

    print("XDMF generation complete.")
