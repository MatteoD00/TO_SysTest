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
        """else:
            mean.append(0)
            devstd.append(0)
            vth.append(datavth[i])"""
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
    fluence = fluence_match.group(0) if fluence_match else None

    return voltage, temperature, pixel, fluence

# Search for the correct timestamp in the directory
def find_info(respath, timestamp):
    dirlist = os.listdir(respath)
    for dir in dirlist:
        if timestamp in dir:
            voltage, temperature, pixel, fluence = extract_info(dir.replace(timestamp,""))
            return voltage, temperature, pixel, fluence


# Main part of the script
if __name__ == "__main__":
    root_files = find_root_files_in_directories()

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

    #Uncomment the timestamps for the sensor you want to analyse and select correct readout module
    timestamps = ["2024-10-10-18-09-56","2024-10-10-18-17-57","2024-10-10-17-57-44","2024-10-10-16-16-17","2024-10-10-16-00-51","2024-10-10-15-43-55","2024-10-10-15-23-42","2024-10-10-15-00-22"]  # FBK 10e14 - module 21
    #timestamps = ["2024-10-01-15-36-16","2024-10-01-15-45-50","2024-10-01-16-03-51","2024-10-01-16-13-50","2024-10-01-16-23-04","2024-10-01-16-37-34","2024-10-01-17-09-52"]    #FBK 6e14 - module21
    #timestamps = ["2024-10-11-10-08-23","2024-10-11-10-26-15","2024-10-11-10-34-44","2024-10-11-10-48-25","2024-10-11-11-04-02","2024-10-11-11-15-51","2024-10-11-11-27-32","2024-10-11-11-38-40","2024-10-11-11-49-17","2024-10-11-12-00-52"]   # FBK 15e14 - module 43
    #timestamps = ["2024-09-24-13-59-35","2024-09-24-13-37-58","2024-09-24-13-30-25","2024-09-24-13-19-01","2024-09-24-12-48-32","2024-09-24-12-33-41","2024-09-24-12-25-41","2024-09-24-11-48-32","2024-09-24-11-40-27","2024-09-24-11-26-18"] # FBK unirr - module 43
    timecode = [datetime.timestamp(datetime.strptime(timestamp,"%Y-%m-%d-%H-%M-%S")) for timestamp in timestamps]
    module = 21
    dirpath = f"./module_test/outputs/{module}/"
    respath = dirpath.replace("outputs","results")
    timestamps.sort()
    data = []
    counts = []
    bins = []
    if not os.path.isdir("ToA_ToT"):
        os.mkdir("ToA_ToT")
    for time_i, timestamp in enumerate(timestamps):
        rootdata = []
        for file_name, dataitem in file_data.items():
            if abs(dataitem['timestamp'][0] - timecode[time_i]) < 10:
                rootdata = list(zip(*dataitem.values()))
        #fig1, (histToA, histToT) = plt.subplots(2,4,figsize=(16,9),dpi=300)
        canv1 = ROOT.TCanvas('canv1','canv1',2000,1000)
        canv1.Divide(4,2)
        fig2, (ToA_mean,ToT_mean) = plt.subplots(1,2,figsize=(16,9),dpi=300)
        #fig3, ax = plt.subplots(2,2,figsize=(16,9),dpi=300)
        canv3 = ROOT.TCanvas('canv3','canv3',1400,1050)
        canv3.Divide(2,2)
        voltage, temperature, pixel, fluence = find_info(respath, timestamp)
        rootfile = ROOT.TFile(f'ToA_ToT/FBK_{fluence}/{timecode[time_i]}_{voltage}.root','RECREATE')
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
            for elements in rootdata:
                if elements[0] == charge:
                    width = elements[1]
                    HM_left = elements[2] 
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
            if charge == 5:
                endpoint = 800
            else:
                endpoint = 450
            canv1.cd(j+1)
            hist_toa_vth.append(ROOT.TH2F(f'toa_vth_{charge}',f'Charge: {charge}fC',100,np.min(vth_a),np.max(vth_a),100,np.min(toa_flat),max(np.max(toa_flat),800)))
            for iter in range(len(vth_a)):
                hist_toa_vth[j].Fill(vth_a[iter],toa_flat[iter])
            hist_toa_vth[j].GetXaxis().SetTitle('Vth (a.u.)')
            hist_toa_vth[j].GetYaxis().SetTitle('ToA (a.u.)')
            hist_toa_vth[j].Draw('COLZ')
            lineLeftA.append(ROOT.TLine(HM_left,np.min(toa_flat),HM_left,max(np.max(toa_flat),800)))
            lineWidthA.append(ROOT.TLine(HM_left+width,np.min(toa_flat),HM_left+width,max(np.max(toa_flat),800)))
            lineLeftA[j].Draw()
            lineWidthA[j].Draw()
            canv1.cd(j+5)
            hist_tot_vth.append(ROOT.TH2F(f'tot_vth_{charge}',f'Charge: {charge}fC',100,np.min(vth_t),np.max(vth_t),100,np.min(tot_flat),max(np.max(tot_flat),250)))
            for iter in range(len(vth_t)):
                hist_tot_vth[j].Fill(vth_t[iter],tot_flat[iter])
            hist_tot_vth[j].GetXaxis().SetTitle('Vth (a.u.)')
            hist_tot_vth[j].GetYaxis().SetTitle('ToT (a.u.)')
            hist_tot_vth[j].Draw('COLZ')
            lineLeftT.append(ROOT.TLine(HM_left,np.min(tot_flat),HM_left,max(np.max(tot_flat),250)))
            lineWidthT.append(ROOT.TLine(HM_left+width,np.min(tot_flat),HM_left+width,max(np.max(tot_flat),800)))
            lineLeftT[j].Draw()
            lineWidthT[j].Draw()
            canv1.Update()
            ToA_mean.plot(vth_amean,mean_a,color=colors[charge],label=charge)
            ToA_mean.set_xlabel("Vth")
            ToA_mean.set_ylabel("ToA_mean")
            ToT_mean.plot(vth_tmean,mean_t,color=colors[charge],label=charge)
            ToT_mean.set_xlabel("Vth")
            ToT_mean.set_ylabel("ToT_mean")
            canv3.cd(j+1)
            hist_toa_tot.append(ROOT.TH2F(f'toa_tot_{charge}',f'Charge: {charge}',100,(np.min(tot_flat)),max(np.max(tot_flat),250),100,np.min(toa_flat),max(np.max(toa_flat),endpoint)))
            for iter in range(len(tot_flat)):
                hist_toa_tot[j].Fill(tot_flat[iter],toa_flat[iter])
            hist_toa_tot[j].GetXaxis().SetTitle('ToT (a.u)')
            hist_toa_tot[j].GetYaxis().SetTitle('ToA (a.u)')
            hist_toa_tot[j].Draw('COLZ')
            canv3.Update()
        ToA_mean.legend()
        ToT_mean.legend()
        title = f"{timestamp} \n Pixel:{pixel} Bias:{voltage} Temp:{temperature} Fluence:{fluence}"
        #fig1.suptitle(title)
        fig2.suptitle(title)
        #fig3.suptitle(title)
        if not voltage:
            voltage = "?"
        if not fluence:
            fluence = "0e14"
        if not os.path.isdir(f"ToA_ToT/FBK_{fluence}"):
            os.mkdir(f"ToA_ToT/FBK_{fluence}")
        canv1.SaveAs(f"ToA_ToT/FBK_{fluence}/{timestamp}_mod{module}_bias{voltage}_f{fluence}_hist2d.png")
        #fig1.savefig(f"ToA_ToT/FBK_{fluence}/{timestamp}_mod{module}_bias{voltage}_f{fluence}_hist2d.png",dpi=300)
        #plt.close(fig1)
        fig2.savefig(f"ToA_ToT/FBK_{fluence}/{timestamp}_mod{module}_bias{voltage}_f{fluence}_mean.png",dpi=300)
        plt.close(fig2)
        #fig3.savefig(f"ToA_ToT/FBK_{fluence}/{timestamp}_mod{module}_bias{voltage}_f{fluence}_ToAvsToT.png",dpi=300)
        #plt.close(fig3)
        canv3.SaveAs(f"ToA_ToT/FBK_{fluence}/{timestamp}_mod{module}_bias{voltage}_f{fluence}_ToAvsToT.png")
        canv1.Close()
        canv3.Close()
        rootfile.Write()
        rootfile.Close()

    print(f"Saved all the images in FBK_{fluence}...")
