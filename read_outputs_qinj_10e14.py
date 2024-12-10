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
module_id = 21 #43
#timestamps_unirr_negtemp = ["2024-10-01-11-55-39","2024-10-01-12-07-27","2024-10-01-12-16-44","2024-10-01-12-28-02","2024-10-01-12-37-39", "2024-10-01-12-48-40", "2024-10-01-13-00-17"]  # good for series at -20C, unirradiated
timestamps_10e14_negtemp = ["2024-10-10-15-00-22","2024-10-10-15-23-42","2024-10-10-15-43-55","2024-10-10-16-00-51","2024-10-10-16-16-17","2024-10-10-17-57-44","2024-10-10-18-09-56"]  # good for series at -20C, 10e14    -->     omitted "2024-10-10-18-17-57" measurement @400V due to strange curves
timestamps = timestamps_10e14_negtemp
dose = "10E14"
fit_options = "QR+"
current_10e14_negtemp = [0,4.,4.,4.7,7.1,9.7,9.8,15.3,27.3]
current = current_10e14_negtemp


dir_path = "./module_test/outputs/"
path_results_qinj = "./module_test/results/" + str(module_id) + "/"

if module_id == 43:
    outdir = "2x2UFSD4_W17_T9_-20C_15E14/"
else:
    outdir = "2x2UFSD4_W17_T9_-20C_10e14/"
if not os.path.isdir(outdir):
    os.mkdir(outdir)
    
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
lowLim_left, highLim_left = [100,100,100,120,120,140,150], [135,140,145,155,165,170,185] # good for series at -20C, 10e14
lowLim_right = [[140,200,240,330], [135,190,240,320], [145,160,180,210], [145,178,190,220], [160,180,200,240], [170,190,210,250], [180,210,230,270]] 
highLim_right = [[170,230,280,370], [170,240,280,360], [210,220,245,280], [200,240,250,295], [190,230,260,300], [200,240,270,310], [220,250,280,330]] # good for series at -20C, 10e14

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
