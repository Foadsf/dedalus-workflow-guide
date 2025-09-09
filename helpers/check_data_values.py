import h5py
import numpy as np
import pathlib


def check_data_values():
    """Check the actual data values to see if the instability developed."""

    file_path = pathlib.Path("snapshots/snapshots_s1.h5")

    with h5py.File(file_path, "r") as h5_file:
        # Get time data
        sim_time = h5_file["scales/sim_time"][:]
        print(f"Time range: {sim_time[0]:.3f} to {sim_time[-1]:.3f}")
        print(f"Number of time steps: {len(sim_time)}")

        # Check scalar field evolution
        scalar_data = h5_file["tasks/scalar"][:]
        print(f"\nScalar field shape: {scalar_data.shape}")

        # Check values at different times
        times_to_check = [0, len(sim_time) // 4, len(sim_time) // 2, -1]

        for i in times_to_check:
            data_slice = scalar_data[i, :, :]
            print(f"\nTime step {i} (t={sim_time[i]:.3f}):")
            print(f"  Min: {data_slice.min():.6f}")
            print(f"  Max: {data_slice.max():.6f}")
            print(f"  Mean: {data_slice.mean():.6f}")
            print(f"  Std: {data_slice.std():.6f}")

        # Check velocity field
        velocity_data = h5_file["tasks/velocity"][:]
        print(f"\nVelocity field shape: {velocity_data.shape}")

        # Check velocity components at final time
        final_vel = velocity_data[-1, :, :, :]
        print(f"\nFinal velocity field:")
        print(
            f"  U-component (x): min={final_vel[0].min():.6f}, max={final_vel[0].max():.6f}"
        )
        print(
            f"  W-component (z): min={final_vel[1].min():.6f}, max={final_vel[1].max():.6f}"
        )

        # Check vorticity
        vorticity_data = h5_file["tasks/vorticity"][:]
        final_vort = vorticity_data[-1, :, :]
        print(f"\nFinal vorticity:")
        print(f"  Min: {final_vort.min():.6f}")
        print(f"  Max: {final_vort.max():.6f}")
        print(f"  Std: {final_vort.std():.6f}")


if __name__ == "__main__":
    check_data_values()
