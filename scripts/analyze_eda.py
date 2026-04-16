import pandas as pd
import neurokit2 as nk
import matplotlib.pyplot as plt
import os

def run_eda_analysis(input_file="data/bio_eventrelated_100hz.csv", sampling_rate=100, output_dir="results"):
    # Create directory for results if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    print(f"Loading data from {input_file}...")
    data = pd.read_csv(input_file)

    if "EDA" not in data.columns:
        print("EDA column not found in dataset.")
        return

    eda_signal = data["EDA"]

    print("Processing EDA signal...")
    # Decompose EDA into tonic and phasic components
    signals, info = nk.eda_process(eda_signal, sampling_rate=sampling_rate)

    # Summary of results
    scr_peaks = len(info["SCR_Peaks"])
    tonic_mean = signals["EDA_Tonic"].mean()

    print("-" * 30)
    print("EDA ANALYSIS SUMMARY")
    print(f"Number of Skin Conductance Responses (SCR) peaks: {scr_peaks}")
    print(f"Average Tonic Component Level: {tonic_mean:.4f}")
    print("-" * 30)

    # Save summary to file
    with open(f"{output_dir}/eda_summary.txt", "w") as f:
        f.write("EDA ANALYSIS SUMMARY\n")
        f.write(f"Number of Skin Conductance Responses (SCR) peaks: {scr_peaks}\n")
        f.write(f"Average Tonic Component Level: {tonic_mean:.4f}\n")

    # Visualize
    print("Generating plot...")
    nk.eda_plot(signals, info=info)
    plt.savefig(f"{output_dir}/eda_analysis_plot.png")
    plt.close()
    print(f"Results saved in '{output_dir}/' directory.")

if __name__ == "__main__":
    if not os.path.exists("data/bio_eventrelated_100hz.csv"):
        print("Data file not found. Please ensure the path is correct.")
    else:
        run_eda_analysis()
