from tensorflow import keras, device
import numpy as np
import random

NORMALIZATION = [False]
NUM_HIDDEN_LAYERS = [4]
NUM_UNITS = [16, 32, 64]
ACTIVATION = ['relu']
OUTPUT_LAYER_ACTIVATION = ['linear']
NUM_EPOCHS = [40, 10, 10]
AUTOSAVE_EVERY = 150

def normalize(array):
    return (array - array.min(0)) / array.ptp(0)

def printtest():
    for i in range(15):
        index = random.randint(0, 500)
        td = testing_data[index:index+1]

        print('\nModel returns:', model.predict(td))
        print('Expected:', testing_labels[index])

def all_hl_cfg(depth=1, _arr=[]):
    if not _arr:
        for num_units in NUM_UNITS:
            for ac in ACTIVATION:
                _arr.append([(num_units, ac)])
    if depth > 1:
        ret = []
        for el in _arr:
            for num_units in NUM_UNITS:
                for ac in ACTIVATION:
                    ret.append(el + [(num_units, ac)])
        return all_hl_cfg(depth - 1, ret)
    elif depth == 1:
        return _arr
    else:
        raise ValueError('depth must always be equal to, or higher than 1')

# Format:
# [point, left_eye_midpoint, right_eye_midpoint, gaze_vector, face_size, head_pose]

raw_data = np.load("capresults.npy", allow_pickle=True)

# del datapoints with empty vectors
mask = np.ones(len(raw_data), dtype=bool)
data = np.zeros((len(raw_data), 13), dtype='O')

for i, dp in enumerate(raw_data):
    if (dp[3].size == 0 or dp[5].size == 0):
        mask[i] = False
    
    flattened = np.concatenate([[*dp[0], *dp[1], *dp[2]], dp[3], [dp[4]], dp[5]], axis=0).astype('float32')
    if flattened.shape[0] == data.shape[1]:
        data[i] = flattened
del raw_data

# Format:
# [point.x, point.y, left_eye_midpoint, right_eye_midpoint, face_size, gaze_vector.x, gaze_vector.y, gaze_vector.z, head_pose.x, head_pose.y, head_pose.z,]

data = data[mask, ...]

# split into training and testing sets
mask = np.random.choice([True, False], len(data), p=[0.75, 0.25])

training_data = data[mask, ...][:, 2:]
training_labels = data[mask, ...][:, :2]

mask = ~mask

testing_data = data[mask, ...][:, 2:]
testing_labels = data[mask, ...][:, :2]

norm_training_data = normalize(training_data)
norm_training_labels = normalize(training_labels)

del data

random.seed(1984)

configurations = []
per_layer_configutaions = len(NUM_UNITS) * len(ACTIVATION)
total_tests = 0
for n in NUM_HIDDEN_LAYERS:
    total_tests = total_tests + per_layer_configutaions ** n
total_tests = str(total_tests * len(NORMALIZATION) * len(NUM_EPOCHS) * len(OUTPUT_LAYER_ACTIVATION))

current_test = 0

with device('/GPU:0'):
    for num_hl in NUM_HIDDEN_LAYERS:
        for hl_cfg in all_hl_cfg(num_hl):
            for out_ac in OUTPUT_LAYER_ACTIVATION:
                if current_test % AUTOSAVE_EVERY == 0:
                    np.save("cfg_autosave", configurations)
                    keras.backend.clear_session()

                model = keras.Sequential()
                model.add(keras.Input(shape=(11,), name='data'))
                model.add(keras.layers.Dense(128, activation='relu'))
                for layer in hl_cfg:
                    model.add(keras.layers.Dense(layer[0], activation=layer[1]))
                
                model.add(keras.layers.Dense(2, activation=out_ac, name='output'))

                model.compile(optimizer='adam', loss='mean_squared_error', 
                            metrics=['mean_squared_error'])

                total_epochs = 0
                for norm in NORMALIZATION:
                    for epochs in NUM_EPOCHS:
                        current_test = current_test + 1
                        # train the model
                        if norm:
                            model.fit(norm_training_data, norm_training_labels, epochs=epochs, initial_epoch=total_epochs)
                        else:
                            model.fit(training_data, training_labels, epochs=epochs, initial_epoch=total_epochs)
                        total_epochs = total_epochs + epochs

                        # test the model
                        test_loss, test_mse = model.evaluate(testing_data, testing_labels, verbose=0)
                        print('\nTest (' + str(current_test) + '/' + total_tests + ') MSE:', test_mse)

                        configurations.append([norm, hl_cfg, out_ac, total_epochs, test_loss])

np.save("configurations_zjst_l5", configurations)

configurations.sort(key=lambda x: x[-1])

print("#  | loss             | norm  | out_ac       | epochs | hidden layers")
print("--------------------------------------------------")
for i, result in enumerate(configurations):
    print("{0:2d} | {1:6.10f} | {2} | {3:12s} | {4:6d} | {5}".format(i, result[4], result[0], result[2], result[3], result[1]))

# convert to openvino-mo-understandable format
# printtest()
