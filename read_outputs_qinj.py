import json
import os
import ROOT
import numpy as np
from re import search

def parse_file(filename: str):
    with open(filename, 'r') as f:
        data = json.load(f)
    return data
#returns the index at the point closest to the half maximum of the hits array
def find_first_HM(vth: np.array, hits: np.array) -> int:
    half_max_hit = hits.max()/2.
    idx = (np.abs(hits - half_max_hit)).argmin()
    return idx

#gets bias, temperature and pixel from the directory path
def extract_info(s: str):
    # Extract voltage (e.g., "300V")
    voltage_match = search(r'(\d+V)', s)
    voltage = voltage_match.group(1) if voltage_match else None

    # Extract temperature (e.g., "-20C")
    temperature_match = search(r'(-?\d+C)', s)
    temperature = temperature_match.group(1) if temperature_match else None

    # Extract pixel row and column (e.g., "15-8")
    pixel_match = search(r'(\d+-\d+)', s)
    pixel = pixel_match.group(1) if pixel_match else None

    return voltage, temperature, pixel


# Module ID and timestamp
module_id = 43
timestamps = []
timestamp = "2024-10-01-11-55-39"
dir_path = "../from_systest_pc/outputs/"
filepath = dir_path + str(module_id) + "/" + timestamp + "/"

#to be recovered inside the results/ directory 
path_results_qinj = "../from_systest_pc/results/"+str(module_id)+"/"
all_dirs_there = [entry for entry in os.listdir(path_results_qinj) if os.path.isdir(os.path.join(path_results_qinj, entry))]
for dir in all_dirs_there:
    if timestamp in dir:
        voltage, temperature, pixel = extract_info(dir.replace(timestamp,""))

dose = "0E14" #"6E14"
outfilename = f"results_mod{str(module_id)}_{pixel}_{dose}.root"

# Find all json files
json_files = [file for file in os.listdir(filepath) if file.endswith('.json')]

#lists with the results
charges, width, width_norm, sigma_left, sigma_right = [], [], [], [], []

mg = ROOT.TMultiGraph()
legend = ROOT.TLegend(0.75, 0.75, 0.9, 0.9)
canvas = ROOT.TCanvas("canvas", "S curve for Qinj", 800, 600)
graphs = []
fit_functions_left, fit_functions_right = [], []
lowLim_left, highLim_left = 350,388

lowLim_right, highLim_right = [380.,430.,410.,500.],[420.,480.,520.,580.]

# Loop through each json file
for i, file in enumerate(json_files):
    charges.append(float(file.split('_')[-1].split('.')[0]))  # Extract charge from filename

print(json_files)
#sorting the files based on the charges order  
charges, json_files = zip(*sorted(list(zip(charges, json_files)), key=lambda x: x[0]))

for i, file in enumerate(json_files):
    data = parse_file(filepath + file)

    vth = np.array(data['vth'], dtype='float64')  # Convert to numpy array of type float64
    hits = np.array(data['hits'], dtype='float64')  # Convert to numpy array of type float64

    # Create TGraph with vth and hits data
    graph_hits = ROOT.TGraph(len(vth), vth, hits)
    fit_functions_left.append(ROOT.TF1(f"fit_left{i}","gaus",lowLim_left, highLim_left))
    fit_functions_left[i].SetLineColor(i+1)
    #fit_functions_left[i].SetParameter(0,(lowLim_left+highLim_left)/2.)
    #fit_functions_left[i].SetParameter(1,20)
    #fit_functions_left[i].SetParameter(2,8.)
    #fit_functions_left[i].SetParameter(3,4.)

    fit_functions_right.append(ROOT.TF1(f"fit_right{i}","TMath::Erfc((x-[0])/[1])*[2]+[3]",lowLim_right[i], highLim_right[i]))
    fit_functions_right[i].SetLineColor(i+1)
    fit_functions_right[i].SetParameters((lowLim_right[i]+highLim_right[i])/2.,20.,8.,4.)

    graph_hits.Fit(fit_functions_left[i],'QR+')
    graph_hits.Fit(fit_functions_right[i],'QR+')

    # Set graph properties (e.g., title, markers)
    graph_hits.SetMarkerStyle(20)
    graph_hits.SetMarkerColor(i + 1)  # Different color for each graph
    graph_hits.SetLineColor(i + 1)  # Same color for the line

    #computing and storing relevand variables
    x_left = fit_functions_left[i].GetParameter(1)-fit_functions_left[i].GetParameter(2)*ROOT.TMath.Sqrt(2*ROOT.TMath.Log(2))
    x_right = fit_functions_right[i].GetParameter(0)
    width.append(abs(x_left-x_right))
    width_norm.append(width[i]/charges[i])
    sigma_left.append(fit_functions_left[i].GetParameter(2))
    sigma_right.append(fit_functions_right[i].GetParameter(1))

    mg.Add(graph_hits)
    legend.AddEntry(graph_hits, f'{charges[i]} fC', 'lp')

mg.Draw("AP")
mg.SetTitle("S curve for Qinj; Vth; Hit rate")

# Draw legend
legend.Draw()

# Show the canvas
canvas.Update()
canvas.Draw()


# Adding the obtained info to a root file with the timestamp as reference
outFile =  ROOT.TFile.Open(outfilename,'RECREATE')
tree = ROOT.TTree("qinj_results", "qinj_results")
t_charge = np.zeros(1, dtype=int)
t_width = np.zeros(1, dtype=float)
t_width_norm = np.zeros(1, dtype=float)
t_sigma_left = np.zeros(1, dtype=float)
t_sigma_right = np.zeros(1, dtype=float)

from time import mktime
from datetime import datetime
#t_timestamp = ROOT.std.string(timestamp) 
t_timestamp = np.zeros(1, dtype=float) # not human readable, just a float for making graphs
timestamp_float = float(mktime(datetime.strptime(timestamp, "%Y-%m-%d-%H-%M-%S").timetuple()))
# Step
tree.Branch("charge", t_charge, "charge/I")
tree.Branch("width", t_width, "width/D")
tree.Branch("width_norm", t_width_norm, "width_norm/D")
tree.Branch("sigma_left", t_sigma_left, "sigma_left/D")
tree.Branch("sigma_right", t_sigma_right, "sigma_right/D")
tree.Branch("timestamp", t_timestamp, "timestamp/D")
for i in range(len(charges)):
    t_charge[0] =  charges[i]
    t_width[0] = width[i]
    t_width_norm[0] = width_norm[i]
    t_sigma_left[0] = sigma_left[i]
    t_sigma_right[0] = sigma_right[i]
    t_timestamp[0] = timestamp_float
    tree.Fill()
tree.Write()
outFile.Close()

input('press ENTER to quit')