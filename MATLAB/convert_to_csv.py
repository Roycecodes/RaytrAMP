import os
import struct
import numpy as np

folder_path = "./datafiles/rcs"
output_folder = "./datafiles/csv"
os.makedirs(output_folder, exist_ok=True)

def load_rcs_file(filepath):
    with open(filepath, 'rb') as f:
        count_bytes = f.read(4)
        (rcs_count,) = struct.unpack('I', count_bytes)
        rcs_bytes = f.read(rcs_count * 4)
        rcs_values = struct.unpack(f'{rcs_count}f', rcs_bytes)
    return np.array(rcs_values, dtype=np.float32)

def rcs_to_csv(input_path, output_path):
    rcs_values = load_rcs_file(input_path)

    # Convert to dB scale: 10 * log10(rcs)
    # Avoid log(0) by replacing zero or negative values with a small positive number
    safe_rcs = np.clip(rcs_values, a_min=1e-10, a_max=None)
    rcs_dB = 10 * np.log10(safe_rcs)

    count = len(rcs_dB)
    phi_values = np.linspace(0, 360, count, endpoint=False)
    combined = np.column_stack((phi_values, rcs_dB))
    np.savetxt(output_path, combined, delimiter=',')

if __name__ == "__main__":
    # List all .rcs files in the folder
    rcs_files = [f for f in os.listdir(folder_path) if f.endswith('.rcs')]

    if not rcs_files:
        print("No .rcs files found.")
        exit()

    # Show available files with index
    print("Available .rcs files:")
    for idx, file in enumerate(rcs_files):
        print(f"{idx}: {file}")

    # Prompt user for file index
    x = int(input("Index of file to convert: "))

    # Get file paths
    input1 = os.path.join(folder_path, rcs_files[x])
    output1 = os.path.join(output_folder, rcs_files[x].replace('.rcs', '.csv'))

    # Convert to CSV (with dB)
    rcs_to_csv(input1, output1)

    print(f"Converted:\n - {input1} -> {output1}")
