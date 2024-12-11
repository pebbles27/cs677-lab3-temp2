import subprocess
import os
import random
import json

data = {"boar": {"quantity": 0, "price": 0}, "fish": {"quantity": 0, "price": 0}, "salt": {"quantity": 0, "price": 0}}
types = ["Boars", "Salt", "Fish"]

# Write initial stock data to file
with open("stock.json", "w") as file:
    json.dump(data, file, indent=4)

base_directory = os.getcwd()

# Get the number of nodes
no_of_nodes = int(input("No of nodes: "))
numbers = [i for i in range(1, no_of_nodes + 1)]

# Load seller-buyer configuration
with open("config_ts.json", "r") as file:
    data_sb = json.load(file)

sellers = data_sb[str(no_of_nodes)]["sellers"]

# Generate commands for nodes
commands = [
    ["python", f"{base_directory}\\peer.py", str(i), "seller" if i in sellers else "buyer", str(no_of_nodes)]
    for i in range(1, no_of_nodes + 1)
]
commands.append(["python", f"{base_directory}\\warehouse.py", str(51)])
print(commands)

# Start processes in new cmd windows
for cmd in commands:
    try:
        role_dir = os.path.join(base_directory, f"peer{cmd[2]}")
        os.makedirs(role_dir, exist_ok=True)

        # Full command for Windows cmd.exe
        full_command = (
            f"start cmd /k \"cd /d {role_dir} && {' '.join(cmd)}\""
        )
        
        print(f"Executing: {full_command}")  # Debugging output
        subprocess.Popen(full_command, shell=True)
    except Exception as e:
        print(f"Failed to start process: {' '.join(cmd)} - {e}")
