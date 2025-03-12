import os
import re
import ROOT
import argparse
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
#import mplhep as hep

LOW_TEMP = False
ALL = False

# Dose extraction from filename
def extract_dose(input_string, verbose : bool = False):
    if verbose:
        print(f"Found file {input_string} --> extract fluence through regex")
    # Extract the filename from the path
    filename = os.path.basename(input_string)
    # Using regex to find the pattern of a number before and after 'E' or 'e'
    match = re.search(r'(\d+)[eE](\d+)', filename)
    
    if match:
        before_e = int(match.group(1))
        after_e = int(match.group(2))
        if after_e != 14:
            print(f"The data was saved using a dose multiplier different than 10e14, please check it. Datafile: {input_string}")
        return before_e
    else:
        return None  # In case there's no match

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

def linear(x, m, q):
    return x * m + q

# Main part of the script
if __name__ == "__main__":
    argParser = argparse.ArgumentParser(description='Argument parser')
    argParser.add_argument('--xvar',action='store',default=None,type=str,help='Define x variable to plot')
    argParser.add_argument('--yvar',action='store',default=None,type=str,help='Define y variable to plot')
    argParser.add_argument('--low_temp', action='store',default=None,type=int,help='Select RoomT or Cold measurements')
    argParser.add_argument('--group_plot',action='store_true',default=False,help='Plot average and std values instead of scatter')
    args = argParser.parse_args()
    root_files = find_root_files_in_directories()
    if args.low_temp is not None:
        LOW_TEMP = bool(args.low_temp)
    # Initialize a dictionary to store data by file
    file_data = {}

    colors = ('blue','red','green','orange')
    if not root_files:
        print("No ROOT files found in the subdirectories.")
    else:
        print(f"Found {len(root_files)} ROOT files.")

    for i, file_name in enumerate(root_files):
        #print(f"Processing file: {file_name}")
        if 'HPK' in file_name:
            continue
        # Initialize data storage for each file
        file_data[file_name] = {
            "dose": extract_dose(file_name),
            "temperature": 22 if "roomT" in file_name else -20,
            "light": "on" if "lighton" in file_name else "off",
            "charge": [],
            "width": [],
            "HM_left": [],
            "sigma_left": [],
            "sigma_right": [],
            "timestamp": [],
            "voltage": [],
            "current": []
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
            file_data[file_name]["sigma_left"].append(entry.sigma_left)
            file_data[file_name]["sigma_right"].append(entry.sigma_right)
            file_data[file_name]["timestamp"].append(entry.timestamp)
            file_data[file_name]["voltage"].append(entry.voltage)
            file_data[file_name]["current"].append(entry.current)

        file.Close()   

    plt.figure(figsize=(11,8))
    
    y_plot = "HM_left" #"width" #"HM_left"
    if args.yvar in ['width','HM_left']:
        y_plot = args.yvar
    x_plot = "current"  #"current" #"charge"
    if args.xvar in ['current','charge']:
        x_plot = args.xvar

    
    Title_x_axis = ""
    if x_plot == "current":
        Title_x_axis = "Current (uA)"
    if x_plot == "charge":
        Title_x_axis = "Charge (fC)"

    Title_y_axis = ""
    if y_plot == "width":
        Title_y_axis = "width (A.U.)"
    if y_plot == "HM_left":
        Title_y_axis = "x_left (A.U.)"
    if y_plot == "current":
        Title_y_axis = "Current (uA)"
    
    if ALL:
        filtered_data = file_data
        for file_name, data in filtered_data.items():
            i += 1
            plt.scatter(data[x_plot], data[y_plot], label=f"{extract_dose(file_name)}e14 $n_{{eq}}/cm^2$ - {data['temperature']}C - {data['light']}")
            plt.xlabel(Title_x_axis)
            plt.ylabel(Title_y_axis)
        if y_plot == "width":
            plt.title(f"Width for all sensors")
        if y_plot == "HM_left":
            plt.title(f"Signal Vth position (HM left) for all sensors")
        plt.legend(title="Dose - Temperature - Light",loc='best')
        plt.savefig(f'{os.getcwd()}/Plots_thesis/{y_plot}_{x_plot}.png')
        #plt.show()
        plt.close()
    else:
        if LOW_TEMP:
            filtered_data = {fname: data for fname, data in file_data.items() if data["temperature"] < 0}

            plt.figure(figsize=(11,8))
            i = 0
            order = [1,2,0]
            for file_name, data in filtered_data.items():
                if  '_0E14' in file_name: #y_plot == 'width' and
                    continue
                if not args.group_plot:
                    plt.scatter(data[x_plot], data[y_plot], color=colors[i], label=fr"{extract_dose(file_name, True)}e14 $n_{{eq}}/cm^2$")
                else:
                    x_unique = np.unique(data[x_plot])
                    y_mean = []
                    y_std = []
                    for x in x_unique:
                        mask = np.array(data[x_plot]) == x
                        if isinstance(mask, np.ndarray) and mask.dtype != bool:
                            mask = mask.astype(bool)  # Force boolean type if needed
                        y_arr = np.array(data[y_plot])[mask]
                        if np.any(mask):
                            y_mean.append(np.mean(y_arr))
                            y_std.append(np.std(y_arr))
                        else:
                            y_mean.append(np.nan)
                            y_std.append(np.nan)
                    plt.errorbar(x_unique, y_mean, y_std, fmt='o', color=colors[i], label=fr"{extract_dose(file_name, True)}e14 $n_{{eq}}/cm^2$")
                    p0 = [1,0]
                    popt, pcov = curve_fit(linear,data[x_plot],data[y_plot],p0)
                    x_curve = np.linspace(np.min(data[x_plot])-1,np.max(data[x_plot])+1,500)
                    plt.plot(x_curve,linear(x_curve,popt[0],popt[1]),color = colors[i], linestyle = '--', label = fr"Fit {extract_dose(file_name, True)}e14 $n_{{eq}}/cm^2$")
                i += 1
                plt.xlabel(Title_x_axis,fontsize='x-large')
                plt.ylabel(Title_y_axis,fontsize='x-large')
            handles, labels = plt.gca().get_legend_handles_labels()
            if y_plot == "HM_left":
                plt.title(f"Signal baseline (HM left) for irradiated sensors data \n Acquired at -20C",fontsize='x-large')
            if y_plot == "width":
                plt.title(f"Width for irradiated sensors data \n Acquired at -20C")
            plt.legend([handles[i] for i in order], [labels[i] for i in order], title="Dose",fontsize='x-large',loc='best')
            plt.savefig(f'{os.getcwd()}/Plots_thesis/PostIrradiation/{y_plot}_{x_plot}_irr{'_grouped' if args.group_plot else ''}.png')
            #plt.show()
            plt.close()
        else:
            filtered_data = {fname: data for fname, data in file_data.items() if data["temperature"] > 0}
            plt.figure(figsize=(11,8))
            i = 0
            for file_name, data in filtered_data.items():
                if not args.group_plot:
                    plt.scatter(data[x_plot], data[y_plot], color=colors[i], label="light on" if "lighton" in file_name else "light off")
                else:
                    x_unique = np.unique(data[x_plot])
                    y_mean = []
                    y_std = []
                    for x in x_unique:
                        mask = np.array(data[x_plot]) == x
                        if isinstance(mask, np.ndarray) and mask.dtype != bool:
                            mask = mask.astype(bool)  # Force boolean type if needed
                        y_arr = np.array(data[y_plot])[mask]
                        if np.any(mask):
                            y_mean.append(np.mean(y_arr))
                            y_std.append(np.std(y_arr))
                        else:
                            y_mean.append(np.nan)
                            y_std.append(np.nan)
                    plt.errorbar(x_unique, y_mean, y_std, fmt='o', color=colors[i], label="light on" if "lighton" in file_name else "light off")
                    p0 = [1,0]
                    popt, pcov = curve_fit(linear,data[x_plot],data[y_plot],p0)
                    x_curve = np.linspace(np.min(data[x_plot])-1,np.max(data[x_plot])+1,500)
                    plt.plot(x_curve,linear(x_curve,popt[0],popt[1]),color = colors[i], linestyle = '--', label = "Fit light on" if "lighton" in file_name else "Fit light off")
                i += 1
                plt.xlabel(Title_x_axis,fontsize='x-large')
                plt.ylabel(Title_y_axis,fontsize='x-large')
            #handles, labels = plt.gca().get_legend_handles_labels()
            #order = [1,2,0,3]
            #plt.title(f"Current vs Charge for data acquired at -20C")
            #plt.legend([handles[i] for i in order], [labels[i] for i in order], title="Dose")
            if y_plot == "HM_left":
                plt.title(f"Signal baseline (HM left) for unirradiated sensors data \n Acquired at +22C",fontsize='x-large')
            if y_plot == "width":
                plt.title(f"Width for unirradiated sensors data \n Acquired at +22C",fontsize='x-large')
            plt.legend(title="Light status",fontsize='x-large',loc='best')
            plt.savefig(f'{os.getcwd()}/Plots_thesis/Unirradiated/{y_plot}_{x_plot}_unirr{'_grouped' if args.group_plot else ''}.png')
            #plt.show()
            plt.close()

    