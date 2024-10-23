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
    root_files = find_root_files_in_directories()

    charges = [5,15,20,30]

    if not root_files:
        print("No ROOT files found in the subdirectories.")
        sys.exit(1)
    else:
        print(f"Found {len(root_files)} ROOT files.")

    for i, file in enumerate(root_files):
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
        txtout = open(f'{path}fit_{filename}.txt','w')
        for charge in charges:
            txtout.write(f'#### Results for charge = {charge} ####\n')
            canvas  = ROOT.TCanvas('c1')
            canvas.cd()
            histname = f"toa_tot_{charge}"
            hist2d = roottemp.Get(histname)
            clean_hist(hist2d, module)
            if charge == 30 and testdraw:
                canvas2 = ROOT.TCanvas('c2')
                hist2d.DrawCopy()
                canvas2.SaveAs(f'test{i}.png')
            profile = hist2d.ProfileX(f"toa_tot_{charge}_prof")
            profile.GetYaxis().SetTitle("ToA mean (a.u.)")
            if testdraw:
                profile.Draw()
            lowedges = []
            for iter in range(1,profile.GetNbinsX()+1):
                lowedges.append(profile.GetXaxis().GetBinLowEdge(iter))
            minval = get_minval(profile,0.,160.)
            print(f"Profile '{profile.GetName()}' saved to the ROOT file")
            fitfunc = ROOT.TF1(f'fitfunc_{charge}','[a0]+[a1]*x+[a2]*pow(x,2)',minval,160.)
            fit_result = profile.Fit(fitfunc,'RS')
            try:
                for iter in range(fit_result.NPar()):
                    parname = fit_result.GetParameterName(iter)
                    parval = fit_result.Parameter(iter)
                    parerr = fit_result.ParError(iter)
                    txtout.write(f'Parameter {parname} = {parval:.3f} +- {parerr:.3f}\n')
                txtout.write('\nCovariance Matrix:\n')
                for iter1 in range(fit_result.NPar()):
                    for iter2 in range(fit_result.NPar()):
                        covelem = fit_result.CovMatrix(iter1,iter2)
                        txtout.write(f'{covelem:.3f}\t')
                    txtout.write('\n')
                chi2 = fit_result.Chi2()
                ndf = fit_result.Ndf()
                txtout.write(f'Chi2: {chi2:.3f}\tNDF: {ndf}\t\tChi2/NDF: {chi2/ndf:.3f}\n')
                fit_result.Write(f"toa_tot_{charge}_fit", ROOT.TObject.kOverwrite)
            except:
                print("Cannot save fit results")
                txtout.write("Cannot save fit results")
            profile.Write(f"toa_tot_{charge}_prof", ROOT.TObject.kOverwrite)
            canvas.Close()
            txtout.write('\n\n\n')
        
        roottemp.Close()
        txtout.close()

    print('End of fitting ToA-ToT histograms')
    end_time = time.time()
    elaps_time = end_time - start_time
    print(f"Execution time: {elaps_time:.3f} seconds")
    sys.exit(0)