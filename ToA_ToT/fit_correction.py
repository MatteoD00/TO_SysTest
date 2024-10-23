import json
import os
import sys
import ROOT
import numpy as np
from re import search
from time import mktime
from datetime import datetime
import time
import matplotlib.pyplot as plt
import math
import statistics

# Finding ROOT files in directories
def find_root_files_in_directories():
    root_files = []
    current_dir = os.getcwd()

    for dirpath, dirnames, filenames in os.walk(current_dir):
        if dirpath != current_dir:
            for file in filenames:
                if file.endswith(".root"):
                    full_path = os.path.join(dirpath, file)
                    root_files.append(full_path)

    return root_files

# Find minimum on X axis
def get_minval(profile: ROOT.TH1, x_low: float, x_high: float):
    bin_low = profile.GetXaxis().FindBin(x_low)
    bin_high = profile.GetXaxis().FindBin(x_high)

    min_value = float('inf')
    min_bin = -1

    for bin in range(bin_low,bin_high+1):
        bin_cont = profile.GetBinContent(bin)
        if bin_cont < min_value:
            min_value = bin_cont
            min_bin = bin
    minval = profile.GetXaxis().GetBinLowEdge(min_bin)
    return minval

# Delete noise bins
def clean_hist(hist2d: ROOT.TH2, module: int):
    #threshold = 2.
    x_bins = hist2d.GetNbinsX()
    y_bins = hist2d.GetNbinsY()
    if module == 43:
        y_high = hist2d.GetYaxis().FindBin(250.)
        y_low = hist2d.GetYaxis().FindBin(70.)
    else:
        y_high = hist2d.GetYaxis().FindBin(350.)
        y_low = hist2d.GetYaxis().FindBin(100.)
    for x_bin in range(1, x_bins+1):
        for y_bin in range(1, y_bins+1):
            bin_cont = hist2d.GetBinContent(x_bin, y_bin)
            if bin_cont == 1 or (y_bin > (y_high + 1.2 * x_bin)) or (y_bin < 0.5 * x_bin):
                hist2d.SetBinContent(x_bin, y_bin, 0)

if __name__ == "__main__":
    start_time = time.time()
    testdraw = False
    ROOT.gStyle.SetOptStat(0)
    charges = [5,15,20,30]
    # Extract list of ROOT files
    root_files = find_root_files_in_directories()
    if not root_files:
        print("No ROOT files found in the subdirectories.")
        sys.exit(1)
    else:
        print(f"Found {len(root_files)} ROOT files.")

    for i, file in enumerate(root_files):
        # Extract info and ROOT file
        filename = os.path.basename(file)
        print('\n'+('#'*70))
        print(f'Open file {filename}')
        fluence_match = search(r'(\d+e\d+)', file)
        fluence = fluence_match.group(0)
        module = 21
        if fluence in ['0e14','15e14']:
            module = 43
        roottemp = ROOT.TFile(file,"UPDATE")
        path = file.replace(filename,'')
        filename = filename.replace('.root','')
        jdict = {}
        for charge in charges:
            jdict[charge] = {
                'parname': [],
                'parval': [],
                'parerr': [],
                'Chi2': 0,
                'NDF': 0,
            }
            # Get 2D histogram ToA vs ToT
            canvas  = ROOT.TCanvas('c1')
            canvas.cd()
            histname = f"toa_tot_{charge}"
            hist2d = roottemp.Get(histname)
            # Clear histogram from noise hits
            clean_hist(hist2d, module)
            if charge == 30 and testdraw:
                canvas2 = ROOT.TCanvas('c2')
                hist2d.DrawCopy()
                canvas2.SaveAs(f'{path}hist_{filename}_cleaned.png')
            # Extract 1D profile
            profile = hist2d.ProfileX(f"toa_tot_{charge}_prof")
            profile.GetYaxis().SetTitle("ToA mean (a.u.)")
            if testdraw:
                profile.Draw()
            # Fit function from minimum
            minval = get_minval(profile,0.,160.)
            print(f"Profile '{profile.GetName()}' saved to the ROOT file")
            fitfunc = ROOT.TF1(f'fitfunc_{charge}','[a0]+[a1]*x+[a2]*pow(x,2)',minval,160.)
            fit_result = profile.Fit(fitfunc,'RS')
            # Save fit results
            try:
                npar = fit_result.NPar()
                for iter in range(npar):
                    jdict[charge]['parname'].append(fit_result.GetParameterName(iter))
                    jdict[charge]['parval'].append(fit_result.Parameter(iter))
                    jdict[charge]['parerr'].append(fit_result.ParError(iter))
                jdict[charge]['Chi2'] = fit_result.Chi2()
                jdict[charge]['NDF'] = fit_result.Ndf()
                fit_result.Write(f"toa_tot_{charge}_fit", ROOT.TObject.kOverwrite)
            except:
                print("Cannot save fit results")
                for iter in range(3):
                    jdict[charge]['parname'].append(0)
                    jdict[charge]['parval'].append(0)
                    jdict[charge]['parerr'].append(0)
                jdict[charge]['Chi2'] = 0
                jdict[charge]['NDF'] = 0

            # Save profile plot with fit
            profile.Write(f"toa_tot_{charge}_prof", ROOT.TObject.kOverwrite)
            canvas.Close()
        roottemp.Close()
        with open(f'{path}fit_{filename}.json','w') as json_file:
            json.dump(jdict, json_file, indent=4)

    print('End of fitting ToA-ToT histograms')
    end_time = time.time()
    elaps_time = end_time - start_time
    print(f"Execution time: {elaps_time:.3f} seconds")
    sys.exit(0)