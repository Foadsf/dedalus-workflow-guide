import h5py
import pathlib


def inspect_hdf5_structure(filepath):
    """Inspect the structure of a Dedalus HDF5 file."""
    print(f"Inspecting structure of: {filepath}")
    print("=" * 50)

    with h5py.File(filepath, "r") as h5_file:
        print("Root level keys:")
        for key in h5_file.keys():
            print(f"  {key}")

        print("\n" + "-" * 30)

        # Recursively print structure
        def print_structure(name, obj):
            if isinstance(obj, h5py.Dataset):
                print(f"Dataset: {name} - Shape: {obj.shape}, Dtype: {obj.dtype}")
            elif isinstance(obj, h5py.Group):
                print(f"Group: {name}")

        print("Full structure:")
        h5_file.visititems(print_structure)

        print("\n" + "-" * 30)

        # Check specific common paths
        common_paths = ["scales", "scales/sim_time", "scales/x", "scales/z", "tasks"]

        print("Checking common paths:")
        for path in common_paths:
            try:
                item = h5_file[path]
                if isinstance(item, h5py.Dataset):
                    print(f"  {path}: Dataset - Shape: {item.shape}")
                elif isinstance(item, h5py.Group):
                    print(f"  {path}: Group - Keys: {list(item.keys())}")
                else:
                    print(f"  {path}: {type(item)}")
            except KeyError:
                print(f"  {path}: NOT FOUND")

        # If scales group exists, explore it further
        if "scales" in h5_file:
            print("\nScales group detailed structure:")
            scales_group = h5_file["scales"]

            def print_scales_structure(name, obj):
                full_path = f"scales/{name}" if name else "scales"
                if isinstance(obj, h5py.Dataset):
                    print(
                        f"  Dataset: {full_path} - Shape: {obj.shape}, Dtype: {obj.dtype}"
                    )
                    # Print attributes if any
                    if obj.attrs:
                        for attr_name, attr_val in obj.attrs.items():
                            print(f"    Attr: {attr_name} = {attr_val}")
                elif isinstance(obj, h5py.Group):
                    print(f"  Group: {full_path} - Keys: {list(obj.keys())}")

            print_scales_structure("", scales_group)
            scales_group.visititems(print_scales_structure)


if __name__ == "__main__":
    snapshots_dir = pathlib.Path("snapshots")

    # Find first HDF5 file to inspect
    h5_files = list(snapshots_dir.glob("snapshots_s*.h5"))

    if h5_files:
        inspect_hdf5_structure(h5_files[0])
    else:
        print("No snapshot files found in snapshots/ directory")
        print("Looking for any .h5 files...")
        h5_files = list(pathlib.Path(".").glob("*.h5"))
        if h5_files:
            inspect_hdf5_structure(h5_files[0])
        else:
            print("No .h5 files found in current directory")
