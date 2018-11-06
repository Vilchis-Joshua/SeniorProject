import os
import pandas as pd
import numpy as np
import tensorflow as tf


dir = 'train_data/easy'
files = os.listdir(dir)
d = []
count = 0
for f in files:
   data = os.path.join(dir, f)
   #data = list(data)
   print(pd.DataFrame(data=data[1:,1:],
                    index=data[1:,0],
                    columns=data[0,1:]))
   
   #for d in data:
   #   print(d)
   #   count += 1

      #for file in all_files[current:current+increment]:
      #   full_path = os.path.join(train_data_dir, file)
      #   data = np.load(full_path)
      #   data = list(data)
      #   for d in data:
      #         choice = np.argmax(d[0])
      #         if choice == 0:
      #            no_attacks.append([d[0], d[1]])
      #         elif choice == 1:
      #            attack_closest_to_nexus.append([d[0], d[1]])
      #         elif choice == 2:
      #            attack_enemy_structures.append([d[0], d[1]])
      #         elif choice == 3:
      #            attack_enemy_start.append([d[0], d[1]])
      #         elif choice == 4:
      #            harass_attack.append([d[0], d[1]])