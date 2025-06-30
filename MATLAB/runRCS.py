#!/usr/bin/env python3
import os
import subprocess
import numpy as np
import matplotlib.pyplot as plt
import struct

# Base and data folders
BASE_DIR = os.getcwd()
MESH_FOLDER = os.path.join(BASE_DIR, 'DataFiles', 'Unv')   # contains .unv and .obj meshes
OBS_FOLDER  = os.path.join(BASE_DIR, 'DataFiles', 'Obs')   # output .obs files
EXE_FOLDER  = os.path.join(BASE_DIR, 'Executables')        # .exe files for RaytrAMP

# Ensure the observer output folder exists
os.makedirs(OBS_FOLDER, exist_ok=True)


def list_mesh_files():
    """List all .unv and .obj files available for selection."""
    files = sorted([f for f in os.listdir(MESH_FOLDER)
                    if f.lower().endswith(('.unv', '.obj'))])
    if not files:
        print(f"No mesh files (.unv/.obj) found in: {MESH_FOLDER}")
        exit(1)

    print("Available mesh files:")
    for i, fn in enumerate(files):
        print(f"  [{i}] {fn}")
    return files


def get_user_inputs():
    """Prompt user to select mesh and enter observation parameters."""
    files = list_mesh_files()
    idx = int(input("Select mesh file by index: "))
    mesh_file = files[idx]

    obs_count = int(input("Number of observation points [360]: ") or 360)
    az_start  = float(input("Azimuth start (deg) [0]: ") or 0)
    az_end    = float(input("Azimuth end   (deg) [360]: ") or 360)
    el_start  = float(input("Elevation start (deg) [0]: ") or 0)
    el_end    = float(input("Elevation end   (deg) [0]: ") or 0)
    radius    = float(input("Observer radius (m) [10]: ") or 10)

    px = float(input("Polarization X [0]: ") or 0)
    py = float(input("Polarization Y [0]: ") or 0)
    pz = float(input("Polarization Z [1]: ") or 1)

    freq = float(input("Frequency (Hz) [3e9]: ") or 3e9)
    rpl  = int(input("Rays per wavelength [2]: ") or 2)

    return mesh_file, obs_count, (az_start, az_end), (el_start, el_end), radius, (px, py, pz), freq, rpl


def make_rba(mesh_path, rba_path):
    """Run MakeRBA.exe to convert a mesh into .rba format."""
    exe = os.path.join(EXE_FOLDER, 'MakeRBA.exe')
    subprocess.run([exe, mesh_path, rba_path], check=True)


def write_obs_file(obs_path, obs_count, obs_x, obs_y, obs_z,
                   pol_x, pol_y, pol_z, freq_arr, ray_arr):
    """Write the binary .obs file in MATLAB-compatible layout."""
    with open(obs_path, 'wb') as f:
        # write observer count as uint32
        f.write(struct.pack('<I', obs_count))
        for k in range(obs_count):
            # position
            f.write(struct.pack('<f', obs_x[k]))
            f.write(struct.pack('<f', obs_y[k]))
            f.write(struct.pack('<f', obs_z[k]))
            # polarization
            f.write(struct.pack('<f', pol_x[k]))
            f.write(struct.pack('<f', pol_y[k]))
            f.write(struct.pack('<f', pol_z[k]))
            # frequency
            f.write(struct.pack('<f', freq_arr[k]))
            # rays-per-wavelength
            f.write(struct.pack('<I', ray_arr[k]))


def generate_obs_file(obs_file, obs_count, az_range, el_range, radius,
                      pol, freq, rpl):
    """Compute observer positions, polarization, then write .obs file."""
    az = np.linspace(az_range[0], az_range[1], obs_count, endpoint=False)
    el = np.linspace(el_range[0], el_range[1], obs_count, endpoint=False)
    az_rad = np.deg2rad(az)
    el_rad = np.deg2rad(el)

    # Cartesian coordinates
    obs_x = radius * np.cos(el_rad) * np.cos(az_rad)
    obs_y = radius * np.cos(el_rad) * np.sin(az_rad)
    obs_z = radius * np.sin(el_rad)

    # polarization arrays as float32
    pol_x = np.full(obs_count, pol[0], dtype=np.float32)
    pol_y = np.full(obs_count, pol[1], dtype=np.float32)
    pol_z = np.full(obs_count, pol[2], dtype=np.float32)

    # frequency and ray density
    freq_arr = np.full(obs_count, freq, dtype=np.float32)
    ray_arr  = np.full(obs_count, rpl,  dtype=np.uint32)

    obs_path = os.path.join(OBS_FOLDER, obs_file)
    write_obs_file(obs_path, obs_count,
                   obs_x.astype(np.float32), obs_y.astype(np.float32), obs_z.astype(np.float32),
                   pol_x, pol_y, pol_z,
                   freq_arr, ray_arr)

    return az


def run_monorcs(rba_path, obs_path, rcs_path):
    """Run MonoRCS.exe to compute monostatic RCS."""
    exe = os.path.join(EXE_FOLDER, 'MonoRCS.exe')
    subprocess.run([exe, rba_path, obs_path, rcs_path], check=True)


def load_rcs(rcs_path):
    """Load a binary .rcs file: uint32 count + sequence of float32."""
    with open(rcs_path, 'rb') as f:
        count = struct.unpack('<I', f.read(4))[0]
        data  = np.fromfile(f, dtype=np.float32, count=count)
    return data


def plot_rcs(angles_deg, rcs_vals, title, out_png):
    """Generate a polar plot of RCS (dB) vs. angle and save to PNG."""
    theta = np.deg2rad(angles_deg)
    r_dB  = 10 * np.log10(rcs_vals)

    fig = plt.figure(figsize=(6,6))
    ax  = fig.add_subplot(111, projection='polar')
    ax.plot(theta, r_dB, linewidth=1.5)
    ax.set_thetagrids(np.arange(0,360,45))
    ax.set_rmin(r_dB.min()-5)
    ax.set_rmax(r_dB.max()+5)
    ax.set_title(title, va='bottom')
    ax.set_ylabel('RCS (dB·m²)', labelpad=15)
    ax.grid(True)
    plt.tight_layout()
    plt.savefig(out_png, dpi=300)
    print(f"Saved: {out_png}")


def main():
    mesh_file, obs_count, az_range, el_range, radius, pol, freq, rpl = get_user_inputs()

    mesh_path = os.path.join(MESH_FOLDER, mesh_file)
    shape, _ = os.path.splitext(mesh_file)
    rba_path = f"{shape}.rba"
    obs_file = f"{shape}_{obs_count}obs.obs"
    rcs_file = f"{shape}.rcs"
    png_file = f"{shape}_{obs_count}obs_rcs.png"

    make_rba(mesh_path, rba_path)
    angles = generate_obs_file(obs_file, obs_count, az_range, el_range, radius, pol, freq, rpl)
    run_monorcs(rba_path, os.path.join(OBS_FOLDER, obs_file), rcs_file)
    rcs_vals = load_rcs(rcs_file)
    title = f"Monostatic RCS of {shape} @{freq/1e9:.1f} GHz"
    plot_rcs(angles, rcs_vals, title, png_file)

if __name__ == '__main__':
    main()
