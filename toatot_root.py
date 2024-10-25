import json
import os
import ROOT
import numpy as np
from re import search
from time import mktime
from datetime import datetime
import matplotlib.pyplot as plt
import math
import statistics

#Evaluate mean and std dev of ToA or ToT at each value of Vth
def eval_list(data, datavth):
    mean = []
    devstd = []
    vth = []
    l = []
    for i, sublist in enumerate(data):
        if len(sublist)>0:
            mean.append(sum(sublist)/len(sublist))
            std = 0
            vth.append(datavth[i])
            for item in sublist:
                l.append(item)
                std += ((item-mean[-1])**2)/len(sublist)
            devstd.append(math.sqrt(std))
    return mean, devstd, vth, l

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

# Extract information about the experimental condition from file name
def extract_info(s: str):
    voltage_match = search(r'(\d+V)', s)
    voltage = voltage_match.group(1) if voltage_match else None

    temperature_match = search(r'(-?\d+C)', s)
    temperature = temperature_match.group(1) if temperature_match else None

    pixel_match = search(r'(\d+-\d+)', s)
    pixel = pixel_match.group(1) if pixel_match else None

    fluence_match = search(r'(\d+e\d+)', s)
    fluence = fluence_match.group(0) if fluence_match else '0e14'

    return voltage, temperature, pixel, fluence

# Search for the correct timestamp in the directory
def find_info(respath, timestamp):
    dirlist = os.listdir(respath)
    for dir in dirlist:
        if timestamp in dir:
            voltage, temperature, pixel, fluence = extract_info(dir.replace(timestamp,""))
            return voltage, temperature, pixel, fluence

# Make plots applying ToA correction for different ToT values
def correct_toa(toa_flat: np.array, tot_flat: np.array, vth_a: np.array, vth_t: np.array, timestamp: str, fluence: str, voltage: str, charge: int):
    with open(f'ToA_ToT/FBK_{fluence}/fit_{timestamp}_{voltage}.json','r') as jfile:
        data = json.load(jfile)
    parname = data[str(charge)]['parname']
    parval = data[str(charge)]['parval']
    parerr = data[str(charge)]['parerr']
    toa_flat_corr = []
    for iter in range(len(toa_flat)):
        toa_flat_corr.append(toa_flat[iter] - parval[1]*tot_flat[iter] - parval[2]*tot_flat[iter]*tot_flat[iter])
    return toa_flat_corr

# Main part of the script
if __name__ == "__main__":
    ROOT.gStyle.SetOptStat(0)
    root_files = find_root_files_in_directories()
    # Decide wether to apply time walk correction or not
    correct_bool = False

    # Initialize a dictionary to store data by file
    file_data = {}

    if not root_files:
        print("No ROOT files found in the subdirectories.")
    else:
        print(f"Found {len(root_files)} ROOT files.")

    for i, file_name in enumerate(root_files):
        #print(f"Processing file: {file_name}")

        # Initialize data storage for each file
        file_data[file_name] = {
            "charge": [],
            "width": [],
            "HM_left": [],
            "timestamp": [],
        }

        file = ROOT.TFile(file_name)
        tree = file.Get("qinj_results")

        if not tree:
            print(f"Tree 'qinj_results' not found in {file_name}")
            continue 

        for entry in tree:
            # Append data to the lists within the dictionary for this file
            file_data[file_name]["charge"].append(entry.charge)
            file_data[file_name]["width"].append(entry.width)
            file_data[file_name]["HM_left"].append(entry.HM_left)
            file_data[file_name]["timestamp"].append(entry.timestamp)

        file.Close()   

    colors = {5:'green',15:'blue',20:'red',30:'black'}
    charges = [5,15,20,30]

    # Choose sensor from dictionary to set correct timestamps and module
    dictsens = {
        'FBK_10e14': {
            'timestamps': ["2024-10-10-15-00-22","2024-10-10-15-23-42","2024-10-10-15-43-55","2024-10-10-16-00-51","2024-10-10-16-16-17","2024-10-10-17-57-44","2024-10-10-18-09-56"],
            'module': 21
        },
        'FBK_6e14': {
            'timestamps': ["2024-10-01-17-09-52","2024-10-01-15-36-16","2024-10-01-15-45-50","2024-10-01-16-03-51","2024-10-01-16-13-50","2024-10-01-16-23-04","2024-10-01-16-37-34"],
            'module': 21
        },
        'FBK_15e14': {
            'timestamps': ["2024-10-11-10-08-23","2024-10-11-10-26-15","2024-10-11-10-34-44","2024-10-11-10-48-25","2024-10-11-11-04-02","2024-10-11-11-15-51","2024-10-11-11-27-32","2024-10-11-11-38-40","2024-10-11-11-49-17","2024-10-11-12-00-52"],
            'module': 43
        },
        'FBK_0e14': {
            'timestamps': ["2024-10-01-11-55-39","2024-10-01-12-07-27","2024-10-01-12-16-44","2024-10-01-12-28-02","2024-10-01-12-37-39", "2024-10-01-12-48-40", "2024-10-01-13-00-17"],
            'module': 43
        }
    }
    sens = 'FBK_15e14'
    timestamps = dictsens[sens]['timestamps']
    timecode = [datetime.timestamp(datetime.strptime(timestamp,"%Y-%m-%d-%H-%M-%S")) for timestamp in timestamps]
    module = dictsens[sens]['module']
    dirpath = f"./module_test/outputs/{module}/"
    respath = dirpath.replace("outputs","results")
    timecode.sort()
    data = []
    counts = []
    bins = []
    if not os.path.isdir("ToA_ToT"):
        os.mkdir("ToA_ToT")
    for time_i, timestamp in enumerate(timestamps):
        rootdata = []
        # Extract data from rootfiles and select the file with the current timestamp
        for file_name, dataitem in file_data.items():
            if timecode[time_i] in dataitem['timestamp']:
                rootdata = list(zip(*dataitem.values()))
        # Prepare canvas and lists for analysis
        canv1 = ROOT.TCanvas('canv1','canv1',2000,1000)
        canv1.Divide(4,2)
        fig2, (ToA_mean,ToT_mean) = plt.subplots(1,2,figsize=(16,9),dpi=300)
        canv3 = ROOT.TCanvas('canv3','canv3',1400,1050)
        canv3.Divide(2,2)
        voltage, temperature, pixel, fluence = find_info(respath, timestamp)
        rootfile = ROOT.TFile(f'ToA_ToT/FBK_{fluence}/{timestamp}_{voltage}.root','UPDATE')
        hist_toa_vth = []
        hist_tot_vth = []
        hist_toa_tot = []
        lineLeftA = []
        lineWidthA = []
        lineLeftT = []
        lineWidthT = []
        for j, charge in enumerate(charges):
            width = 0
            HM_left = 0
            # Extract width and HM_left to draw lines
            for elements in rootdata:
                if elements[0] == charge and elements[3] == timecode[time_i]:
                    width = elements[1]
                    HM_left = elements[2] 
            # Read data from JSON file and manipulate into NUMPY arrays
            file = f"Qinj_scan_ETROC_0_L1A_501_{charge}.json"
            with open(dirpath+timestamp+'/'+file, 'r') as f:
                data = json.load(f)
            datatoa = data['toa']
            datatot = data['tot']
            datavth = data['vth']
            toa_flat = np.array([item for sublist in datatoa for item in sublist])
            tot_flat = np.array([item for sublist in datatot for item in sublist])
            vth_a = np.repeat(datavth, [len(sublist) for sublist in datatoa])
            vth_t = np.repeat(datavth, [len(sublist) for sublist in datatoa])
            mean_a, std_a, vth_amean, list_a = eval_list(datatoa, datavth)
            mean_t, std_t, vth_tmean, list_t = eval_list(datatot, datavth)
            if correct_bool:
                toa_flat_corr = correct_toa(toa_flat,tot_flat,vth_a,vth_t,timestamp,fluence,voltage,charge)
            if charge == 5:
                endpoint = 800
            else:
                endpoint = 450
            # Fill 2D histograms for ToX vs Vth
            canv1.cd(j+1)
            hist_toa_vth.append(ROOT.TH2F(f"toa_vth_{charge}{'_Corrected' if correct_bool else ''}",f'Charge: {charge}fC\t {'Corrected' if correct_bool else ''}',100,min(np.min(vth_a),HM_left-20),max(np.max(vth_a),HM_left+width+20),100,np.min(toa_flat),max(np.max(toa_flat),800)))
            for iter in range(len(vth_a)):
                if correct_bool:
                    hist_toa_vth[j].Fill(vth_a[iter],toa_flat_corr[iter])                
                else:
                    hist_toa_vth[j].Fill(vth_a[iter],toa_flat[iter])
            hist_toa_vth[j].GetXaxis().SetTitle('Vth (a.u.)')
            hist_toa_vth[j].GetYaxis().SetTitle('ToA (a.u.)')
            hist_toa_vth[j].Draw('COLZ')
            hist_toa_vth[j].Write(f"toa_vth_{charge}{'_Corrected' if correct_bool else ''}",ROOT.TObject.kOverwrite)
            lineLeftA.append(ROOT.TLine(HM_left,np.min(toa_flat),HM_left,max(np.max(toa_flat),800)))
            lineWidthA.append(ROOT.TLine(HM_left+width,np.min(toa_flat),HM_left+width,max(np.max(toa_flat),800)))
            lineLeftA[j].SetLineWidth(2)
            lineLeftA[j].SetLineColor(ROOT.kGreen)
            lineLeftA[j].Draw('same')
            lineWidthA[j].SetLineWidth(2)
            lineWidthA[j].SetLineColor(ROOT.kRed)
            lineWidthA[j].Draw('same')
            canv1.cd(j+5)
            hist_tot_vth.append(ROOT.TH2F(f'tot_vth_{charge}',f'Charge: {charge}fC',100,min(np.min(vth_t),HM_left-20),max(np.max(vth_t),HM_left+width+20),100,np.min(tot_flat),max(np.max(tot_flat),250)))
            for iter in range(len(vth_t)):
                hist_tot_vth[j].Fill(vth_t[iter],tot_flat[iter])
            hist_tot_vth[j].GetXaxis().SetTitle('Vth (a.u.)')
            hist_tot_vth[j].GetYaxis().SetTitle('ToT (a.u.)')
            hist_tot_vth[j].Draw('COLZ')
            hist_tot_vth[j].Write(f'tot_vth_{charge}',ROOT.TObject.kOverwrite)
            lineLeftT.append(ROOT.TLine(HM_left,np.min(tot_flat),HM_left,max(np.max(tot_flat),250)))
            lineWidthT.append(ROOT.TLine(HM_left+width,np.min(tot_flat),HM_left+width,max(np.max(tot_flat),250)))
            lineLeftT[j].SetLineWidth(2)
            lineLeftT[j].SetLineColor(ROOT.kGreen)
            lineLeftT[j].Draw('same')
            lineWidthT[j].SetLineWidth(2)
            lineWidthT[j].SetLineColor(ROOT.kRed)
            lineWidthT[j].Draw('same')
            canv1.Update()
            # Plot the average of ToX for any given Vth
            ToA_mean.plot(vth_amean,mean_a,color=colors[charge],label=f'{charge} fC')
            ToA_mean.set_xlabel("Vth")
            ToA_mean.set_ylabel("ToA_mean")
            ToT_mean.plot(vth_tmean,mean_t,color=colors[charge],label=f'{charge} fC')
            ToT_mean.set_xlabel("Vth")
            ToT_mean.set_ylabel("ToT_mean")
            # Fill 2D histograms for ToA vs ToT
            canv3.cd(j+1)
            hist_toa_tot.append(ROOT.TH2F(f'toa_tot_{charge}',f'Charge: {charge}fC',100,(np.min(tot_flat)),max(np.max(tot_flat),250),100,np.min(toa_flat),max(np.max(toa_flat),endpoint)))
            for iter in range(len(tot_flat)):
                hist_toa_tot[j].Fill(tot_flat[iter],toa_flat[iter])
            hist_toa_tot[j].GetXaxis().SetTitle('ToT (a.u)')
            hist_toa_tot[j].GetYaxis().SetTitle('ToA (a.u)')
            hist_toa_tot[j].Draw('COLZ')
            hist_toa_tot[j].Write(f'toa_tot_{charge}',ROOT.TObject.kOverwrite)
            canv3.Update()
        ToA_mean.legend()
        ToT_mean.legend()
        title = f"{timestamp} \n Pixel:{pixel} Bias:{voltage} Temp:{temperature} Fluence:{fluence}"
        fig2.suptitle(title)
        if not voltage:
            voltage = "?"
        if not fluence:
            fluence = "0e14"
        # Save figures
        if not os.path.isdir(f"ToA_ToT/FBK_{fluence}"):
            os.mkdir(f"ToA_ToT/FBK_{fluence}")
        canv1.SaveAs(f"ToA_ToT/FBK_{fluence}/{timestamp}_mod{module}_bias{voltage}_f{fluence}{'_corrected' if correct_bool else ''}_hist2d.png")
        fig2.savefig(f"ToA_ToT/FBK_{fluence}/{timestamp}_mod{module}_bias{voltage}_f{fluence}_mean.png",dpi=300)
        plt.close(fig2)
        canv3.SaveAs(f"ToA_ToT/FBK_{fluence}/{timestamp}_mod{module}_bias{voltage}_f{fluence}_ToAvsToT.png")
        canv1.Close()
        canv3.Close()
        rootfile.Close()

    print(f"Saved all the images in FBK_{fluence}...")