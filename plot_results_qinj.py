import os
import re
import ROOT
#import mplhep as hep

LOW_TEMP = False
ALL = True

# Dose extraction from filename
def extract_dose(input_string):
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

    import matplotlib.pyplot as plt
    plt.figure()
    y_plot = "width" #"width" #"HM_left"
    x_plot = "current"  #"current"
    
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
        Title_y_axis = "Current uA"
    
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
        plt.legend(title="Dose - Temperature - Light")
        plt.show()

    else:
        if LOW_TEMP:
            filtered_data = {fname: data for fname, data in file_data.items() if data["temperature"] < 0}

            plt.figure()
            i = 0
            for file_name, data in filtered_data.items():
                i += 1
                plt.scatter(data[x_plot], data[y_plot], label=fr"{extract_dose(file_name)}e14 $n_{{eq}}/cm^2$")
                plt.xlabel(Title_x_axis)
                plt.ylabel(Title_y_axis)
            handles, labels = plt.gca().get_legend_handles_labels()
            order = [1,2,0,3]
            if y_plot == "HM_left":
                plt.title(f"Signal Vth position (HM left) for irradiated sensors data \n Acquired at -20C")
            if y_plot == "width":
                plt.title(f"Width for irradiated sensors data \n Acquired at -20C")
            plt.legend([handles[i] for i in order], [labels[i] for i in order], title="Dose")
            plt.show()
        else:
            filtered_data = {fname: data for fname, data in file_data.items() if data["temperature"] > 0}
            plt.figure()
            i = 0
            for file_name, data in filtered_data.items():
                i += 1
                plt.scatter(data[x_plot], data[y_plot], label="light on" if "lighton" in file_name else "light off")
                plt.xlabel(Title_x_axis)
                plt.ylabel(Title_y_axis)
            #handles, labels = plt.gca().get_legend_handles_labels()
            #order = [1,2,0,3]
            #plt.title(f"Current vs Charge for data acquired at -20C")
            #plt.legend([handles[i] for i in order], [labels[i] for i in order], title="Dose")
            if y_plot == "HM_left":
                plt.title(f"Signal Vth position (HM left) for unirradiated sensors data \n Acquired at -22C")
            if y_plot == "width":
                plt.title(f"Width for unirradiated sensors data \n Acquired at +22C")
            plt.legend(title="Light status")
            plt.show()
    