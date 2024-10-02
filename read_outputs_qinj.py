import json
from os import listdir
import ROOT
import numpy as np

def parse_file(filename: str):
    with open(filename, 'r') as f:
        data = json.load(f)
    return data
#returns the index at the point closest to the half maximum of the hits array
def find_first_HM(vth: np.array, hits: np.array) -> int:
    half_max_hit = hits.max()/2.
    idx = (np.abs(hits - half_max_hit)).argmin()
    return idx


# Module ID and timestamp
module_id = 43
timestamp = "2024-10-01-13-00-17/"
dir_path = "../from_systest_pc/outputs/" + str(module_id) + "/" + timestamp

# Find all json files
json_files = [file for file in listdir(dir_path) if file.endswith('.json')]

#lists with the results
charges, width, width_norm, sigma_left, sigma_right = [], [], [], [], []

mg = ROOT.TMultiGraph()
legend = ROOT.TLegend(0.75, 0.75, 0.9, 0.9)
canvas = ROOT.TCanvas("canvas", "S curve for Qinj", 800, 600)
graphs = []
fit_functions_left, fit_functions_right = [], []
lowLim_left, highLim_left = 350,388
lowLim_right, highLim_right = [430.,500.,380.,410.],[480.,580.,420.,500.]

# Loop through each json file
for i, file in enumerate(json_files):
    charges.append(float(file.split('_')[-1].split('.')[0]))  # Extract charge from filename
    
    data = parse_file(dir_path + file)

    vth = np.array(data['vth'], dtype='float64')  # Convert to numpy array of type float64
    hits = np.array(data['hits'], dtype='float64')  # Convert to numpy array of type float64

    # Create TGraph with vth and hits data
    graphs.append(ROOT.TGraph(len(vth), vth, hits))
    fit_functions_left.append(ROOT.TF1(f"fit_left{i}","gaus",lowLim_left, highLim_left))
    fit_functions_left[i].SetLineColor(i+1)
    #fit_functions_left[i].SetParameter(0,(lowLim_left+highLim_left)/2.)
    #fit_functions_left[i].SetParameter(1,20)
    #fit_functions_left[i].SetParameter(2,8.)
    #fit_functions_left[i].SetParameter(3,4.)

    fit_functions_right.append(ROOT.TF1(f"fit_right{i}","TMath::Erfc((x-[0])/[1])*[2]+[3]",lowLim_right[i], highLim_right[i]))
    fit_functions_right[i].SetLineColor(i+1)
    fit_functions_right[i].SetParameters((lowLim_right[i]+highLim_right[i])/2.,20.,8.,4.)

    graphs[i].Fit(fit_functions_left[i],'R+')
    graphs[i].Fit(fit_functions_right[i],'R+')

    # Set graph properties (e.g., title, markers)
    graphs[i].SetMarkerStyle(20)
    graphs[i].SetMarkerColor(i + 1)  # Different color for each graph
    graphs[i].SetLineColor(i + 1)  # Same color for the line


    x_left = fit_functions_left[i].GetParameter(1)-fit_functions_left[i].GetParameter(2)*ROOT.TMath.Sqrt(2*ROOT.TMath.Log(2))
    x_right = fit_functions_right[i].GetParameter(0)
    width.append(abs(x_left-x_right))
    width_norm.append(width[i]/charges[i])
    sigma_left.append(fit_functions_left[i].GetParameter(2))
    sigma_right.append(fit_functions_right[i].GetParameter(1))


results_zipped = list(zip(charges, width, width_norm, sigma_left, sigma_right))
results_zipped_ordered = sorted(results_zipped, key=lambda x: x[0])

print(results_zipped_ordered)

charges_sorted, width_sorted, width_norm_sorted, sigma_left_sorted, sigma_right_sorted = zip(*results_zipped_ordered)

for i, graph in enumerate(graphs_sorted):
    # Add graph to TMultiGraph
    mg.Add(graph)
    
    # Add entry to legend
    legend.AddEntry(graph, f'{charges_sorted[i]} fC', 'lp')
# some drawing
# Draw all graphs in TMultiGraph
mg.Draw("AP")
mg.SetTitle("S curve for Qinj; Vth; Hit rate")

# Draw legend
legend.Draw()

# Show the canvas
canvas.Update()
canvas.Draw()

input('press ENTER to quit')