import pandas as pd
import neurokit2 as nk
import matplotlib.pyplot as plt
import os

def run_multimodal_analysis(input_file="data/bio_resting_5min_100hz.csv", sampling_rate=100, output_dir="results"):
    # Create directory for results if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    print(f"Loading data from {input_file}...")
    data = pd.read_csv(input_file)

    # This dataset contains ECG, PPG, and RSP
    print("Processing multimodal signals...")
    # bio_process handles multiple modalities and calculates cross-modal metrics like RSA
    signals, info = nk.bio_process(ecg=data["ECG"], ppg=data["PPG"], rsp=data["RSP"], sampling_rate=sampling_rate)

    # Summary of results
    hr_mean = signals["ECG_Rate"].mean()
    rr_mean = signals["RSP_Rate"].mean()
    rsa_mean = signals["RSA_P2T"].mean()

    print("-" * 30)
    print("MULTIMODAL ANALYSIS SUMMARY")
    print(f"Average Heart Rate: {hr_mean:.2f} bpm")
    print(f"Average Respiration Rate: {rr_mean:.2f} breaths/min")
    print(f"Average RSA (Peak-to-Trough): {rsa_mean:.4f}")
    print("-" * 30)

    # Save summary to file
    with open(f"{output_dir}/multimodal_summary.txt", "w") as f:
        f.write("MULTIMODAL ANALYSIS SUMMARY\n")
        f.write(f"Average Heart Rate: {hr_mean:.2f} bpm\n")
        f.write(f"Average Respiration Rate: {rr_mean:.2f} breaths/min\n")
        f.write(f"Average RSA (Peak-to-Trough): {rsa_mean:.4f}\n")

    # Visualize - since bio_plot is not available, we use signal_plot or manual plotting
    print("Generating plot...")
    # We plot a segment of the processed signals
    signals.iloc[:1000][["ECG_Clean", "PPG_Clean", "RSP_Clean"]].plot(subplots=True)
    plt.savefig(f"{output_dir}/multimodal_signals_plot.png")
    plt.close()
    print(f"Results saved in '{output_dir}/' directory.")

if __name__ == "__main__":
    if not os.path.exists("data/bio_resting_5min_100hz.csv"):
        print("Data file not found. Please ensure the path is correct.")
    else:
        run_multimodal_analysis()
