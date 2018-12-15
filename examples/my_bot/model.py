import keras
from keras.models import Sequential
from keras.layers import Dense, Dropout, Flatten, Conv2D, MaxPooling2D, Flatten, Activation
from keras.callbacks import TensorBoard
import os
import random
import numpy as np
import time
from tensorflow.keras.callbacks import TensorBoard


os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

#NAME = 'terran-ai-bot-{}'.format(int(time.time()))


#dense_layers = [0,1,2]
#layer_sizes = [32, 64, 128]
#conv_layers = [1, 2, 3]

#for dense_layer in dense_layers:
#   for layer_size in layer_sizes:
#      for conv_layer in conv_layers:
#         NAME = '{}-conv-{}-nodes-{}-dense-{}-time'.format(conv_layer_size, layer_size, dense_layer, int(time.time()))

#         model = Sequential()
#         model.add(Conv2D(32, (3,3), padding='same',
#                          input_shape=(184, 208, 3),
#                          activation='relu'))

#         model.add(Conv2D(32, (3,3), padding='same',
#                          input_shape=(184, 208, 3),
#                          activation='relu'))
#         model.add(Conv2D(32, (3, 3), activation='relu'))
#         model.add(MaxPooling2D(pool_size=(2, 2)))
#         model.add(Dropout(0.2))

#         model.add(Conv2D(64, (3, 3), padding='same',
#                          activation='relu'))
#         model.add(Conv2D(32, (3, 3), activation='relu'))
#         model.add(MaxPooling2D(pool_size=(2, 2)))
#         model.add(Dropout(0.2))

#         model.add(Conv2D(64, (3, 3), padding='same',
#                          activation='relu'))
#         model.add(Conv2D(128, (3, 3), activation='relu'))
#         model.add(MaxPooling2D(pool_size=(2, 2)))
#         model.add(Dropout(0.2))

#         model.add(Flatten())
#         model.add(Dense(128, activation='relu'))
#         model.add(Dropout(0.5))
#         model.add(Dense(6, activation='softmax'))
#         learning_rate = 0.001
#         opt = keras.optimizers.adam(lr=learning_rate, decay = 1e-6)
#         model.compile(loss='categorical_crossentropy',
#                       optimizer=opt,
#                       metrics=['accuracy'])
#tensorboard = TensorBoard(log_dir='logs/{}'.format(NAME))


#model = Sequential()
#model.add(Conv2D(32, (3,3), padding='same',
#                 input_shape=(184, 208, 3),
#                 activation='relu'))

#model.add(Conv2D(32, (3,3), padding='same',
#                 input_shape=(184, 208, 3),
#                 activation='relu'))
#model.add(Conv2D(32, (3, 3), activation='relu'))
#model.add(MaxPooling2D(pool_size=(2, 2)))
#model.add(Dropout(0.2))

#model.add(Conv2D(64, (3, 3), padding='same',
#                 activation='relu'))
#model.add(Conv2D(32, (3, 3), activation='relu'))
#model.add(MaxPooling2D(pool_size=(2, 2)))
#model.add(Dropout(0.2))

#model.add(Conv2D(64, (3, 3), padding='same',
#                 activation='relu'))
#model.add(Conv2D(128, (3, 3), activation='relu'))
#model.add(MaxPooling2D(pool_size=(2, 2)))
#model.add(Dropout(0.2))

#model.add(Flatten())
#model.add(Dense(128, activation='relu'))
#model.add(Dropout(0.5))
#model.add(Dense(6, activation='softmax'))
#learning_rate = 0.001
#opt = keras.optimizers.adam(lr=learning_rate, decay = 1e-6)
#model.compile(loss='categorical_crossentropy',
#              optimizer=opt,
#              metrics=['accuracy'])
#tensorboard = TensorBoard(log_dir='logs/stage1')


model = Sequential()
model.add(Conv2D(32, (7, 7), padding='same',
                 input_shape=(184, 208, 3),
                 activation='relu'))
model.add(Conv2D(32, (3, 3), activation='relu'))
model.add(MaxPooling2D(pool_size=(2, 2)))
model.add(Dropout(0.2))

model.add(Conv2D(64, (3, 3), padding='same',
                 activation='relu'))
model.add(Conv2D(64, (3, 3), activation='relu'))
model.add(MaxPooling2D(pool_size=(2, 2)))
model.add(Dropout(0.2))

model.add(Conv2D(128, (3, 3), padding='same',
                 activation='relu'))
model.add(Conv2D(128, (3, 3), activation='relu'))
model.add(MaxPooling2D(pool_size=(2, 2)))
model.add(Dropout(0.2))

model.add(Dense(256, activation='relu'))
model.add(Dropout(0.5))

model.add(Flatten())
model.add(Dense(1024, activation='relu'))
model.add(Dropout(0.5))
model.add(Dense(11, activation='softmax'))

learning_rate = 0.0001
opt = keras.optimizers.adam(lr=learning_rate)#, decay=1e-6)

model.compile(loss='categorical_crossentropy',
              optimizer=opt,
              metrics=['accuracy'])
#model = Sequential()
#model.add(Conv2D(32, (3, 3), padding='same',
#                 input_shape=(184, 208, 3),
#                 activation='relu'))


#model.add(Conv2D(8, (3, 3), activation='relu'))
#model.add(Conv2D(32, (3, 3), activation='relu'))
#model.add(MaxPooling2D(pool_size=(3, 3)))
#model.add(Dropout(0.5))

#model.add(Conv2D(32, (3, 3), activation='relu'))
#model.add(Conv2D(64, (3, 3), activation='relu'))
#model.add(MaxPooling2D(pool_size=(2,2)))
#model.add(Dropout(0.2))



#model.add(Conv2D(256, (3, 3), activation='relu'))
#model.add(MaxPooling2D(pool_size=(3, 3)))
#model.add(Dropout(0.7))

#model.add(Flatten())
#model.add(Dense(1024, activation='relu'))
#model.add(Dropout(0.5))
#model.add(Dense(11, activation='softmax'))
#learning_rate = 0.0001
#opt = keras.optimizers.adam(lr=learning_rate, decay = 1e-6)
#model.compile(loss='categorical_crossentropy',
#              optimizer=opt,
#              metrics=['accuracy'])
tensorboard = TensorBoard(log_dir='logs/stage6')

def check_data(choices):
    total_data = 0

    lengths = []
    for choice in choices:
        print("Length of {} is: {}".format(choice, len(choices[choice])))
        total_data += len(choices[choice])
        lengths.append(len(choices[choice]))

    print("Total data length now is:", total_data)
    return lengths

train_data_dir = 'train_data/data'
#train_data_dir = 'train_data'
hm_epochs = 5

for i in range(hm_epochs):
   current = 0
   increment = 5
   not_maximum = True
   all_files = os.listdir(train_data_dir)
   maximum = len(all_files)
   random.shuffle(all_files)

   while not_maximum:
      print("WORKING ON {}:{}, EPOCH:{}".format(current, current+increment, i))
      #no_attacks = []
      #attack_closest_to_nexus = []
      #attack_enemy_structures = []
      #attack_enemy_start = []
      #harass_attack = []
      choices = {0: [],
                 1: [],
                 2: [],
                 3: [],
                 4: [],
                 5: [],
                 6: [],
                 7: [],
                 8: [],
                 9: [],
                 10: []
                 }


      for file in all_files[current:current+increment]:
         full_path = os.path.join(train_data_dir, file)
         data = np.load(full_path)
         data = list(data)
         #for d in data:
         #      choice = np.argmax(d[0])
         #      if choice == 0:
         #         no_attacks.append(d)
         #      elif choice == 1:
         #         attack_closest_to_nexus.append(d)
         #      elif choice == 2:
         #         attack_enemy_structures.append(d)
         #      elif choice == 3:
         #         attack_enemy_start.append(d)
         #      elif choice == 4:
         #         harass_attack.append(d)         
         for d in data:
            choice = np.argmax(d[0])
            choices[choice].append([d[0], d[1]])

      lengths = check_data(choices)
      lowest_data = min(lengths)
      print('lengths: {}'.format(lengths))
      print('lowest data: {}'.format(lowest_data))

      for choice in choices:
         random.shuffle(choices[choice])
         choices[choice] = choices[choice][:lowest_data]

      check_data(choices)

      #train_data = no_attacks + attack_closest_to_nexus + attack_enemy_structures + attack_enemy_start + harass_attack
      train_data = []
      for choice in choices:
         for d in choices[choice]:
            train_data.append(d)

      random.shuffle(train_data)
      print(len(train_data))

      #test_size = 30
      #batch_size = 60
      test_size = 10
      batch_size = 20

      x_train = np.array([i[1] for i in train_data[:-test_size]]).reshape(-1, 184, 208, 3)
      y_train = np.array([i[0] for i in train_data[:-test_size]])

      x_test = np.array([i[1] for i in train_data[-test_size:]]).reshape(-1, 184, 208, 3)
      y_test = np.array([i[0] for i in train_data[-test_size:]])     


      model.fit(x_train, y_train,
               batch_size=batch_size,
               validation_data=(x_test, y_test),
               shuffle=True,
               verbose=1,
               epochs=hm_epochs,
              callbacks=[tensorboard])

      model.save("models/december-12-2018/BasicCNN-{}-epochs-{}-LR-STAGE2".format(hm_epochs, learning_rate))
      current += increment
      if current > maximum:
         not_maximum = False






 










#model = Sequential()
#model.add(Conv2D(32, (7, 7), padding='same',
#                 input_shape=(176, 200, 1),
#                 activation='relu'))
#model.add(Conv2D(32, (3, 3), activation='relu'))
#model.add(MaxPooling2D(pool_size=(2, 2)))
#model.add(Dropout(0.2))

#model.add(Conv2D(64, (3, 3), padding='same',
#                 activation='relu'))
#model.add(Conv2D(64, (3, 3), activation='relu'))
#model.add(MaxPooling2D(pool_size=(2, 2)))
#model.add(Dropout(0.2))

#model.add(Conv2D(128, (3, 3), padding='same',
#                 activation='relu'))
#model.add(Conv2D(128, (3, 3), activation='relu'))
#model.add(MaxPooling2D(pool_size=(2, 2)))
#model.add(Dropout(0.2))

#model.add(Flatten())
#model.add(Dense(1024, activation='relu'))
#model.add(Dropout(0.5))
#model.add(Dense(11, activation='softmax'))

#learning_rate = 0.001
#opt = keras.optimizers.adam(lr=learning_rate)#, decay=1e-6)

#model.compile(loss='categorical_crossentropy',
#              optimizer=opt,
#              metrics=['accuracy'])

#tensorboard = TensorBoard(log_dir="logs/STAGE2-{}-{}".format(int(time.time()), learning_rate))

#train_data_dir = "train_data/data"

##model = keras.models.load_model('BasicCNN-5000-epochs-0.001-LR-STAGE2')


#def check_data(choices):
#    total_data = 0

#    lengths = []
#    for choice in choices:
#        print("Length of {} is: {}".format(choice, len(choices[choice])))
#        total_data += len(choices[choice])
#        lengths.append(len(choices[choice]))

#    print("Total data length now is:", total_data)
#    return lengths


#hm_epochs = 5000

#for i in range(hm_epochs):
#    current = 0
#    increment = 50
#    not_maximum = True
#    all_files = os.listdir(train_data_dir)
#    maximum = len(all_files)
#    random.shuffle(all_files)

#    while not_maximum:
#        try:
#            print("WORKING ON {}:{}, EPOCH:{}".format(current, current+increment, i))

#            choices = {0: [],
#                       1: [],
#                       2: [],
#                       3: [],
#                       4: [],
#                       5: [],
#                       6: [],
#                       7: [],
#                       8: [],
#                       9: [],
#                       10: [],
#                       }

#            for file in all_files[current:current+increment]:
#                try:
#                    full_path = os.path.join(train_data_dir, file)
#                    data = np.load(full_path)
#                    data = list(data)
#                    for d in data:
#                        choice = np.argmax(d[0])
#                        choices[choice].append([d[0], d[1]])
#                except Exception as e:
#                    print(str(e))

#            lengths = check_data(choices)

#            lowest_data = min(lengths)

#            for choice in choices:
#                random.shuffle(choices[choice])
#                choices[choice] = choices[choice][:lowest_data]

#            check_data(choices)

#            train_data = []

#            for choice in choices:
#                for d in choices[choice]:
#                    train_data.append(d)

#            random.shuffle(train_data)
#            print(len(train_data))

#            test_size = 100
#            batch_size = 128  # 128 best so far.

#            x_train = np.array([i[1] for i in train_data[:-test_size]]).reshape(-1, 184, 208, 3)
#            y_train = np.array([i[0] for i in train_data[:-test_size]])

#            x_test = np.array([i[1] for i in train_data[-test_size:]]).reshape(-1, 184, 208, 3)
#            y_test = np.array([i[0] for i in train_data[-test_size:]])

#            model.fit(x_train, y_train,
#                      batch_size=batch_size,
#                      validation_data=(x_test, y_test),
#                      shuffle=True,
#                      epochs=1,
#                      verbose=1, callbacks=[tensorboard])

#            model.save("BasicCNN-5000-epochs-0.001-LR-STAGE2")
#        except Exception as e:
#            print(str(e))
#        current += increment
#        if current > maximum:
#            not_maximum = False