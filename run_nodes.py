# Mac Users: run_nodes.py
import subprocess
import os
import random
import json
# import shutil
# no_of_sellers= input("No of sellers: ")
# no_of_transactions= input("No of transaction for each buyer peer ex. 0 10 100 or 20 10 100: ")

# Randomly select sellers and buyers
# sellers = random.sample(numbers,3) 
data={"boar":{"quantity":0, "price":0},"fish":{"quantity":0, "price":0},"salt":{"quantity":0, "price":0}}
types = ["Boars", "Salt", "Fish"]

with open("stock.json", "w") as file:
    json.dump(data, file, indent=4) 
# buyers = [i for i in numbers if i not in sellers]

base_directory = os.getcwd()
# print("Sellers: ", sellers)
# print("Buyers: ", buyers)

# # Create directories for each seller and buyer

# commands = []
# transactions=no_of_transactions.split()

# # transactions= [10,10,10]

# for i in range(len(sellers)):
#     seller_dir = os.path.join(base_directory, f"peer{i}")
#     os.makedirs(seller_dir, exist_ok=True) 

#     data={"type": types[i], "quantity": 4 }
#     path=f"seller_{sellers[i]}_stock.json"
#     with open(path, "w") as json_file:
#         json.dump(data, json_file, indent=4)
#     commands.append(["python", f"{base_directory}/seller.py", str(sellers[i])])
 
# for i in range(len(buyers)):
#     buyer_dir = os.path.join(base_directory, f"peer{buyers[i]}")
#     os.makedirs(buyer_dir, exist_ok=True) 
#     commands.append(["python", f"{base_directory}/buyer.py", str(buyers[i]), str(transactions[i])])


no_of_nodes= int(input("No of nodes: "))
numbers = [i for i in range(1, no_of_nodes+1)] 
with open("config_ts.json", "r") as file:
        data_sb = json.load(file)
#for consistency 

sellers = data_sb[str(no_of_nodes)]["sellers"]

commands=[["python", f"{base_directory}/peer.py", str(i), "seller" if i in sellers else "buyer", str(no_of_nodes)] for i in range(1,no_of_nodes+1)]
commands.append(["python", f"{base_directory}/warehouse.py", str(51)])
print(commands)

for cmd in commands:
    try:       
        # Construct the directory path for the role
        # role_dir = os.path.join(base_directory, f"peer{cmd[2]}")
        role_dir= os.path.join(base_directory, f"peer{cmd[2]}")
        
        # Construct the full command to execute in a new terminal
        full_command = (
            f"osascript -e 'tell app \"Terminal\" to do script "
            f"\" cd {role_dir} &&source {base_directory}/venv/bin/activate && {' '.join(cmd)}\"'"
        )
        # Execute the command in a new terminal
        subprocess.Popen(full_command, shell=True)
        
    except Exception as e:
        # Log failure to start the process
        print(f"Failed to start process: {' '.join(cmd)} - {e}")
