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

        keys = roottemp.GetListOfKeys()
        for key in keys:
            obj_name = key.GetName()
            obj_type = key.GetClassName()
            if ('Corrected' in obj_name) and ("TH2" in obj_type):
                canvas = ROOT.TCanvas()
                th2_corr = roottemp.Get(obj_name)
                distr_name = obj_name.replace('vth','distrib')
                distr_name = distr_name.replace('_Corrected','')
                toa_distr = th2_corr.ProjectionY(name=distr_name)
                toa_distr.DrawCopy()
                min = 100
                max = 250 if module==43 else 300
                fitfunc = ROOT.TF1(f'fitfunc','gaus(0)',min,max)
                fit_result = toa_distr.Fit(fitfunc,'RS')
                toa_distr.Write(distr_name,ROOT.TObject.kOverwrite)
        roottemp.Close()