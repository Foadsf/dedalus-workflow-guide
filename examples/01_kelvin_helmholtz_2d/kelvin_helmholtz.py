"""
Dedalus script simulating 2D shear flow leading to the Kelvin-Helmholtz instability.

This script demonstrates solving an incompressible hydrodynamics problem. It can
be run serially or in parallel, and uses the built-in analysis framework to save
data snapshots to HDF5 files.

The problem is non-dimensionalized. The initial flow is in the x-direction,
with a shear layer in the z-direction centered at z=0. A small amount of noise
is added to the vertical velocity to trigger the instability.

To run, merge, and plot using 4 processes, for instance:
    $ mpiexec -n 4 python3 kelvin_helmholtz.py
    $ python3 ../../helpers/make_xdmf_manual.py
"""

import numpy as np
import dedalus.public as d3
import logging

logger = logging.getLogger(__name__)

# Parameters - Make more unstable
Lx, Lz = 4.0, 1.0
Nx, Nz = 256, 64
dealias = 3 / 2
stop_sim_time = 10.0  # Reduced time
timestepper = d3.RK222
max_timestep = 0.01  # Smaller timestep for stability
dtype = np.float64


# Bases
coords = d3.CartesianCoordinates("x", "z")
dist = d3.Distributor(coords, dtype=dtype)
xbasis = d3.RealFourier(coords["x"], size=Nx, bounds=(0, Lx), dealias=dealias)
zbasis = d3.ChebyshevT(coords["z"], size=Nz, bounds=(-Lz / 2, Lz / 2), dealias=dealias)

# Fields for a passive scalar `s` to visualize the flow
s = dist.Field(name="s", bases=(xbasis, zbasis))
p = dist.Field(name="p", bases=(xbasis, zbasis))
u = dist.VectorField(coords, name="u", bases=(xbasis, zbasis))
tau_p = dist.Field(name="tau_p")
tau_s1 = dist.Field(name="tau_s1", bases=xbasis)
tau_s2 = dist.Field(name="tau_s2", bases=xbasis)
tau_u1 = dist.VectorField(coords, name="tau_u1", bases=xbasis)
tau_u2 = dist.VectorField(coords, name="tau_u2", bases=xbasis)

# Substitutions - Reduced viscosity/diffusivity for stronger instability
nu = 1e-5  # Reduced from 1e-4
kappa = 1e-5  # Reduced from 1e-4

x, z = dist.local_grids(xbasis, zbasis)
ex, ez = coords.unit_vector_fields(dist)
lift_basis = zbasis.derivative_basis(1)
lift = lambda A: d3.Lift(A, lift_basis, -1)
grad_u = d3.grad(u) + ez * lift(tau_u1)
grad_s = d3.grad(s) + ez * lift(tau_s1)

# Problem
problem = d3.IVP([p, s, u, tau_p, tau_s1, tau_s2, tau_u1, tau_u2], namespace=locals())
problem.add_equation("trace(grad_u) + tau_p = 0")  # Incompressibility
problem.add_equation(
    "dt(s) - kappa*div(grad_s) + lift(tau_s2) = - u@grad(s)"
)  # Advection-diffusion of scalar
problem.add_equation(
    "dt(u) - nu*div(grad_u) + grad(p) + lift(tau_u2) = - u@grad(u)"
)  # Momentum equation
problem.add_equation("s(z=-Lz/2) = -1")  # Boundary condition for scalar
problem.add_equation("u(z=-Lz/2) = -0.5*ex")  # Boundary condition for velocity
problem.add_equation("s(z=Lz/2) = 1")  # Boundary condition for scalar
problem.add_equation("u(z=Lz/2) = 0.5*ex")  # Boundary condition for velocity
problem.add_equation("integ(p) = 0")  # Pressure gauge

# Solver
solver = problem.build_solver(timestepper)
solver.stop_sim_time = stop_sim_time

# Initial conditions - Much stronger perturbations
# Shear layer
u["g"][0] = 0.5 * np.tanh(z / 0.05)
# Passive scalar mimics the shear layer
s["g"] = np.tanh(z / 0.05)

# Add much stronger sinusoidal perturbations to trigger instability
u["g"][1] += 0.1 * np.sin(2 * np.pi * x / Lx) * np.exp(-((z / 0.2) ** 2))

# Analysis
import pathlib

script_dir = pathlib.Path(__file__).parent
snapshots = solver.evaluator.add_file_handler(
    script_dir / "snapshots", sim_dt=0.1, max_writes=150
)
snapshots.add_task(s, name="scalar")
snapshots.add_task(u, name="velocity")
snapshots.add_task(d3.div(d3.skew(u)), name="vorticity")

# CFL
CFL = d3.CFL(
    solver,
    initial_dt=max_timestep,
    cadence=10,
    safety=0.3,
    threshold=0.1,
    max_change=1.5,
    min_change=0.5,
    max_dt=max_timestep,
)
CFL.add_velocity(u)

# Flow properties
flow = d3.GlobalFlowProperty(solver, cadence=10)
flow.add_property(np.sqrt(u @ u), name="speed")

# Main loop
try:
    logger.info("Starting main loop")
    while solver.proceed:
        timestep = CFL.compute_timestep()
        solver.step(timestep)
        if (solver.iteration - 1) % 10 == 0:
            max_speed = flow.max("speed")
            logger.info(
                f"Iteration={solver.iteration}, Time={solver.sim_time:.2e}, dt={timestep:.2e}, max(speed)={max_speed:.2f}"
            )
except:
    logger.error("Exception raised, triggering end of main loop.")
    raise
finally:
    solver.log_stats()
