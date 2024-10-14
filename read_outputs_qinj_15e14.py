import json
import os
import ROOT
import numpy as np
from re import search
from time import mktime
from datetime import datetime


STOP = 100

def parse_file(filename: str):
    with open(filename, 'r') as f:
        data = json.load(f)
    return data

# Returns the index at the point closest to the half maximum of the hits array
def find_first_HM(vth: np.array, hits: np.array) -> int:
    half_max_hit = hits.max() / 2.
    idx = (np.abs(hits - half_max_hit)).argmin()
    return idx

# Extracts bias, temperature, and pixel from the directory path
def extract_info(s: str):
    voltage_match = search(r'(\d+V)', s)
    voltage = voltage_match.group(1) if voltage_match else None

    temperature_match = search(r'(-?\d+C)', s)
    temperature = temperature_match.group(1) if temperature_match else None

    pixel_match = search(r'(\d+-\d+)', s)
    pixel = pixel_match.group(1) if pixel_match else None

    return voltage, temperature, pixel

# Module ID and list of timestamps to process
module_id = 43 #43
#timestamps_unirr_negtemp = ["2024-10-01-11-55-39","2024-10-01-12-07-27","2024-10-01-12-16-44","2024-10-01-12-28-02","2024-10-01-12-37-39", "2024-10-01-12-48-40", "2024-10-01-13-00-17"]  # good for series at -20C, unirradiated
timestamps_15e14_negtemp = ["2024-10-11-10-08-23","2024-10-11-10-26-15","2024-10-11-10-34-44","2024-10-11-10-48-25","2024-10-11-11-04-02","2024-10-11-11-15-51","2024-10-11-11-27-32","2024-10-11-11-38-40","2024-10-11-11-49-17","2024-10-11-12-00-52"]  # good for series at -20C, 15e14
timestamps = timestamps_15e14_negtemp
dose = "15E14"
fit_options = "QR+"
current_15e14_negtemp = [0., 4.7, 6.3, 8.2, 8.7, 11.8, 16.5, 23.1, 33.5, 41.6]
current = current_15e14_negtemp

dir_path = "/home/teststandws/module_test_sw_Sept2024/module_test_sw/outputs/"
path_results_qinj = "/home/teststandws/module_test_sw_Sept2024/module_test_sw/results/" + str(module_id) + "/"

if module_id == 43:
    outdir = "2x2UFSD4_W17_T9_-20C_15E14/"
else:
    outdir = "2x2UFSD4_W17_T9_-20C_10e14/"
    
# Find corresponding voltage, temperature, and pixel information
# Assumes the user is smart enought to provide timestamps of the same series
all_dirs_there = [entry for entry in os.listdir(path_results_qinj) if os.path.isdir(os.path.join(path_results_qinj, entry))]
for dir in all_dirs_there:
    if timestamps[0] in dir:
        voltage, temperature, pixel = extract_info(dir.replace(timestamps[0], ""))

# Create the output ROOT file
outfilename = f"{outdir}results_mod{str(module_id)}_{pixel}_{dose}_{temperature}.root"
outFile = ROOT.TFile.Open(outfilename, 'RECREATE')
tree = ROOT.TTree("qinj_results", "qinj_results")

# Variables to store data in the TTree
t_charge = np.zeros(1, dtype=int)
t_width = np.zeros(1, dtype=float)
t_HM_left = np.zeros(1, dtype=float)
t_sigma_left = np.zeros(1, dtype=float)
t_sigma_right = np.zeros(1, dtype=float)
t_timestamp = np.zeros(1, dtype=float)
t_bias = np.zeros(1, dtype=int)
t_current = np.zeros(1, dtype=float)

# Define branches
tree.Branch("charge", t_charge, "charge/I")
tree.Branch("width", t_width, "width/D")
tree.Branch("HM_left", t_HM_left, "HM_left/D")
tree.Branch("sigma_left", t_sigma_left, "sigma_left/D")
tree.Branch("sigma_right", t_sigma_right, "sigma_right/D")
tree.Branch("timestamp", t_timestamp, "timestamp/D")
tree.Branch("voltage", t_bias, "voltage/I")
if len(current):
    tree.Branch("current", t_current, "current/D")

#lowLim_left, highLim_left = 350, 388 # good for series at -20C, unirradiated
#lowLim_right, highLim_right = [380., 430., 410., 500.], [450., 485., 520., 580.] # good for series at -20C, unirradiated
lowLim_left, highLim_left = [330,330,350,360,360,370,380,400,440,460], [385,395,400,400,407,425,425,440,470,490] # good for series at -20C, 15e14
lowLim_right = [[380,400,420,470], [395,410,450,470], [395,400,430,470], [400,410,435,480], [405,420,440,480], [425,435,460,500], [420,460,490,520], [440,455,480,530], [470,485,530,520], [485,520,530,580]] 
highLim_right = [[440,480,510,540], [455,490,510,560], [470,500,530,560], [440,480,515,550], [460,495,530,580], [470,515,535,590], [460,520,550,600], [510,520,580,600], [530,560,585,640], [540,580,610,660]] # good for series at -20C, 15e14

# Loop through all timestamps
for j, timestamp in enumerate(timestamps):

    mg = ROOT.TMultiGraph()
    legend = ROOT.TLegend(0.75, 0.75, 0.9, 0.9)
    canvas = ROOT.TCanvas("canvas", "S curve for Qinj", 800, 600)

    filepath = dir_path + str(module_id) + "/" + timestamp + "/"
    
    # Find corresponding voltage, temperature, and pixel information
    all_dirs_there = [entry for entry in os.listdir(path_results_qinj) if os.path.isdir(os.path.join(path_results_qinj, entry))]
    for dir in all_dirs_there:
        if timestamp in dir:
            voltage, temperature, pixel = extract_info(dir.replace(timestamp, ""))

    # Find all json files for the current timestamp
    json_files = [file for file in os.listdir(filepath) if file.endswith('.json')]

    # Lists to store the results for this timestamp
    charges, width, width_norm, sigma_left, sigma_right, HM_left = [], [], [], [], [], []

    # Process each json file for this timestamp
    for i, file in enumerate(json_files):
        charges.append(float(file.split('_')[-1].split('.')[0]))  # Extract charge from filename

    # Sort files based on the charge values
    charges, json_files = zip(*sorted(list(zip(charges, json_files)), key=lambda x: x[0]))

    for i, file in enumerate(json_files):
        data = parse_file(filepath + file)

        vth = np.array(data['vth'], dtype='float64')  # Convert to numpy array of type float64
        hits = np.array(data['hits'], dtype='float64')  # Convert to numpy array of type float64

        # Create TGraph with vth and hits data
        graph_hits = ROOT.TGraph(len(vth), vth, hits)
        fit_functions_left = ROOT.TF1(f"fit_left_{timestamp}_{i}", "gaus", lowLim_left[j], highLim_left[j])
        fit_functions_left.SetLineColor(i + 1)

        fit_functions_right = ROOT.TF1(f"fit_right_{timestamp}_{i}", "TMath::Erfc((x-[0])/[1])*[2]+[3]", lowLim_right[j][i], highLim_right[j][i])
        fit_functions_right.SetLineColor(i + 1)
        fit_functions_right.SetParameters((lowLim_right[j][i] + highLim_right[j][i]) / 2., 20., 8., 4.)

        # Perform the fits
        graph_hits.Fit(fit_functions_left, fit_options)
        graph_hits.Fit(fit_functions_right, fit_options)

        # Set graph properties
        graph_hits.SetMarkerStyle(20)
        graph_hits.SetMarkerColor(i + 1)
        graph_hits.SetLineColor(i + 1)

        # Compute and store relevant variables
        x_left = fit_functions_left.GetParameter(1) - fit_functions_left.GetParameter(2) * ROOT.TMath.Sqrt(2 * ROOT.TMath.Log(2))
        x_right = fit_functions_right.GetParameter(0)
        width.append(abs(x_left - x_right))
        sigma_left.append(fit_functions_left.GetParameter(2))
        sigma_right.append(fit_functions_right.GetParameter(1))
        HM_left.append(x_left)

        # Add graph to the multigraph
        mg.Add(graph_hits)
        legend.AddEntry(graph_hits, f'{charges[i]} fC', 'lp')

        # Fill the TTree
        t_charge[0] = charges[i]
        t_width[0] = width[i]
        t_sigma_left[0] = sigma_left[i]
        t_sigma_right[0] = sigma_right[i]
        t_HM_left[0] = HM_left[i]
        t_timestamp[0] = float(mktime(datetime.strptime(timestamp, "%Y-%m-%d-%H-%M-%S").timetuple()))
        t_bias[0] = int(voltage.replace("V",""))
        t_current[0] = current[j]
        tree.Fill()

    # Draw the multigraph
    mg.Draw("AP")
    mg.SetTitle("S curve for Qinj; Vth; Hit rate")

    # Draw the legend
    legend.Draw()

    # Update and show the canvas
    canvas.Update()
    canvas.Draw()
    canvas.SaveAs(f"{outdir}Qinj_vs_Vth_{voltage}.png")
    if j == STOP:
        break
    print(j)
    
# Write the TTree and close the file
tree.Write()
outFile.Close()

print(f"Data saved to {outfilename}")

input('press ENTER to quit')
