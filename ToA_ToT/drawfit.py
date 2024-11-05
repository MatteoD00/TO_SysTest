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

# Main part of the script
if __name__ == "__main__":
    fluences = ['0e14','6e14','10e14','15e14']
    charges = [15,20,30]
    colors = {5:'green',15:'blue',20:'red',30:'black'}
    fig1, sigma_plots = plt.subplots(2,2)
    fig2, mean_plots = plt.subplots(2,2)
    for i,fluence in enumerate(fluences):
        sigma_plots[i//2,i%2].set_title(f'Fluence: {fluence}')
        sigma_plots[i//2,i%2].set_xlabel('Vbias [V]')
        sigma_plots[i//2,i%2].set_ylabel('Sigma ToA [a.u.]')
        mean_plots[i//2,i%2].set_title(f'Fluence: {fluence}')
        mean_plots[i//2,i%2].set_xlabel('Vbias [V]')
        mean_plots[i//2,i%2].set_ylabel('Mean ToA [a.u.]')
        data = {}
        with open(f'FBK_{fluence}/fit_results.json','r') as jsonfile:
            data = json.load(jsonfile)
        voltages = data['voltages']
        means = {}
        sigmas = {}
        for charge in charges:
            means[charge] = data[str(charge)]['means']
            sigmas[charge] = data[str(charge)]['sigmas']
            sigma_plots[i//2,i%2].plot(voltages,sigmas[charge],color=colors[charge],label=f'{charge} fC')
            mean_plots[i//2,i%2].plot(voltages,means[charge],color=colors[charge],label=f'{charge} fC')
        sigma_plots[i//2,i%2].legend()
        mean_plots[i//2,i%2].legend()
    fig1.savefig('sigma_plot.jpg',dpi=300)
    fig2.savefig('mean_plot.jpg',dpi=300)
    plt.show()      