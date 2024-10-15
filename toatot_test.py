import json
import os
import ROOT
import numpy as np
from re import search
from time import mktime
from datetime import datetime
import matplotlib.pyplot as plt

def eval_list(data, datavth):
    mean = []
    devstd = []
    vth = []
    l = []
    for i, sublist in enumerate(data):
        if len(sublist)>0:
            mean.append(np.mean(sublist))
            devstd.append(np.std(sublist))
            vth.append(datavth[i])
            for item in sublist:
                l.append(item)
        else:
            mean.append(0)
            devstd.append(0)
            vth.append(datavth[i])
    return mean, devstd, vth, l

colors = ['green','blue','red','black']
dirpath = dir_path = "/home/teststandws/module_test_sw_Sept2024/module_test_sw/outputs/21/"
timestamp = "2024-10-10-15-00-22/"
figure, (axSt, axErr) = plt.subplots(2,2)
charges = [5,15,20,30]
data = []
counts = []
bins = []
for j, charge in enumerate(charges):
    file = f"Qinj_scan_ETROC_0_L1A_501_{charge}.json"
    with open(dirpath+timestamp+file, 'r') as f:
        data = json.load(f)
    datatoa = data['toa']
    datatot = data['tot']
    datavth = data['vth']
    mean_a, std_a, vth_a, list_a = eval_list(datatoa, datavth)
    mean_t, std_t, vth_t, list_t = eval_list(datatot, datavth)
    counts_a, bins_a = np.histogram(list_a,bins=100,range=(0,1000))
    counts_t, bins_t = np.histogram(list_t, bins=100, range=(0,600))
    axSt[0].stairs(counts_a, bins_a,color=colors[j],label=(str(charge)+"fC"))
    axSt[1].stairs(counts_t, bins_t,color=colors[j],label=(str(charge)+"fC"))
    axSt[0].set_xlabel('ToA')
    axSt[0].set_ylabel('counts')
    axSt[1].set_xlabel('ToT')
    axSt[1].set_ylabel('counts')
    axErr[0].plot(vth_a, mean_a,color=colors[j],label=(str(charge)+"fC"))
    axErr[0].set_xlabel('Vth')
    axErr[0].set_xlim(100,400)
    axErr[0].set_ylabel('ToA')
    axErr[1].plot(vth_t, mean_t,color=colors[j],label=(str(charge)+"fC"))
    axErr[1].set_xlabel('Vth')
    axErr[1].set_xlim(100,400)
    axErr[1].set_ylabel('ToT')
figure.suptitle(timestamp)
plt.show()