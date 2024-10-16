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

def find_info(respath, timestamp):
    dirlist = os.listdir(respath)
    for dir in dirlist:
        if timestamp in dir:
            voltage, temperature, pixel, fluence = extract_info(dir.replace(timestamp,""))
            return voltage, temperature, pixel, fluence

colors = ['green','blue','red','black']
charges = [5,15,20,30]

#Uncomment the timestamps for the sensor you want to analyse and select correct readout module
timestamps = ["2024-10-10-18-09-56","2024-10-10-18-17-57","2024-10-10-17-57-44","2024-10-10-16-16-17","2024-10-10-16-00-51","2024-10-10-15-43-55","2024-10-10-15-23-42","2024-10-10-15-00-22"]  # FBK 10e14 - module 21
#timestamps = ["2024-10-01-15-36-16","2024-10-01-15-45-50","2024-10-01-16-03-51","2024-10-01-16-13-50","2024-10-01-16-23-04","2024-10-01-16-37-34","2024-10-01-17-09-52"]    #FBK 6e14 - module21
#timestamps = ["2024-10-11-10-08-23","2024-10-11-10-26-15","2024-10-11-10-34-44","2024-10-11-10-48-25","2024-10-11-11-04-02","2024-10-11-11-15-51","2024-10-11-11-27-32","2024-10-11-11-38-40","2024-10-11-11-49-17","2024-10-11-12-00-52"]   # FBK 15e14 - module 43
#timestamps = ["2024-09-24-13-59-35","2024-09-24-13-37-58","2024-09-24-13-30-25","2024-09-24-13-19-01","2024-09-24-12-48-32","2024-09-24-12-33-41","2024-09-24-12-25-41","2024-09-24-11-48-32","2024-09-24-11-40-27","2024-09-24-11-26-18"] # FBK unirr - module 43
module = 21
dirpath = f"/home/teststandws/module_test_sw_Sept2024/module_test_sw/outputs/{module}/"
respath = dirpath.replace("outputs","results")

data = []
counts = []
bins = []
if not os.path.isdir("ToA_ToT"):
    os.mkdir("ToA_ToT")
for timestamp in timestamps:
    fig1, (histToA, histToT) = plt.subplots(2,4,figsize=(16,9),dpi=300)
    fig2, (ToA_mean,ToT_mean) = plt.subplots(1,2,figsize=(16,9),dpi=300)
    voltage, temperature, pixel, fluence = find_info(respath, timestamp)
    for j, charge in enumerate(charges):
        file = f"Qinj_scan_ETROC_0_L1A_501_{charge}.json"
        with open(dirpath+timestamp+'/'+file, 'r') as f:
            data = json.load(f)
        datatoa = data['toa']
        datatot = data['tot']
        datavth = data['vth']
        toa_flat = [item for sublist in datatoa for item in sublist]
        tot_flat = [item for sublist in datatot for item in sublist]
        vth_a = np.repeat(datavth, [len(sublist) for sublist in datatoa])
        vth_t = np.repeat(datavth, [len(sublist) for sublist in datatoa])
        mean_a, std_a, vth_amean, list_a = eval_list(datatoa, datavth)
        mean_t, std_t, vth_tmean, list_t = eval_list(datatot, datavth)
        if j == 0:
            endpoint = 800
        else:
            endpoint = 500
        histToA[j].hist2d(vth_a,toa_flat,bins=(100,100),range=(None,(200,endpoint)),cmap='YlOrRd')
        histToA[j].set_xlabel("Vth")
        histToA[j].set_ylabel("ToA")
        histToA[j].set_title(f"Charge: {charge}fC")
        histToT[j].hist2d(vth_t,tot_flat,bins=(100,100),range=(None,(0,250)),cmap='YlOrRd')
        histToT[j].set_xlabel("Vth")
        histToT[j].set_ylabel("ToT")
        
        ToA_mean.plot(vth_amean,mean_a,color=colors[j],label=charge)
        ToA_mean.set_xlabel("Vth")
        ToA_mean.set_ylabel("ToA_mean")
        ToT_mean.plot(vth_tmean,mean_t,color=colors[j],label=charge)
        ToT_mean.set_xlabel("Vth")
        ToT_mean.set_ylabel("ToT_mean")
    ToA_mean.legend()
    ToT_mean.legend()
    title = f"{timestamp} \n Pixel:{pixel} Bias:{voltage} Temp:{temperature} Fluence:{fluence}"
    fig1.suptitle(title)
    fig2.suptitle(title)
    if not voltage:
        voltage = "?"
    if not fluence:
        fluence = "0e14"
    fig1.savefig(f"ToA_ToT/{timestamp}_mod{module}_bias{voltage}_f{fluence}_hist2d.png",dpi=300)
    fig2.savefig(f"ToA_ToT/{timestamp}_mod{module}_bias{voltage}_f{fluence}_mean.png",dpi=300)
    