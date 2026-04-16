import pandas as pd
import neurokit2 as nk
import matplotlib.pyplot as plt
import os

def run_ecg_analysis(input_file="data/ecg_1000hz.csv", sampling_rate=1000, output_dir="results"):
    # Create directory for results if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    print(f"Loading data from {input_file}...")
    data = pd.read_csv(input_file)

    # Assume the first column is the ECG signal if not named
    ecg_signal = data.iloc[:, 0]

    print("Processing ECG signal...")
    # Clean and find peaks
    signals, info = nk.ecg_process(ecg_signal, sampling_rate=sampling_rate)

    # Summary of results
    hr_mean = signals["ECG_Rate"].mean()
    peaks_count = len(info["ECG_R_Peaks"])

    print("-" * 30)
    print("ECG ANALYSIS SUMMARY")
    print(f"Number of R-peaks detected: {peaks_count}")
    print(f"Average Heart Rate: {hr_mean:.2f} bpm")
    print("-" * 30)

    # Save summary to file
    with open(f"{output_dir}/ecg_summary.txt", "w") as f:
        f.write("ECG ANALYSIS SUMMARY\n")
        f.write(f"Number of R-peaks detected: {peaks_count}\n")
        f.write(f"Average Heart Rate: {hr_mean:.2f} bpm\n")

    # Visualize
    print("Generating plot...")
    nk.ecg_plot(signals, info=info)
    plt.savefig(f"{output_dir}/ecg_analysis_plot.png")
    plt.close()
    print(f"Results saved in '{output_dir}/' directory.")

if __name__ == "__main__":
    # If data doesn't exist in expected path, try to find it
    if not os.path.exists("data/ecg_1000hz.csv"):
        print("Data file not found at 'data/ecg_1000hz.csv'. Please ensure the path is correct.")
    else:
        run_ecg_analysis()
