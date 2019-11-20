from genetic_calculator import GeneticCalculator, Model
from tensorflow import keras
import numpy as np

def normalize(array):
    return (array - array.min(0)) / array.ptp(0)

raw_data = np.load("combined_results.npy", allow_pickle=True)

# del datapoints with empty vectors
mask = np.ones(len(raw_data), dtype=bool)
data = np.zeros((len(raw_data), 13), dtype='O')

for i, dp in enumerate(raw_data):
    if (dp[3].size is 0 or dp[5].size is 0):
        mask[i] = False
    
    flattened = np.concatenate([[*dp[0], *dp[1], *dp[2]], dp[3], [dp[4]], dp[5]], axis=0).astype('float32')
    if flattened.shape[0] is data.shape[1]:
        data[i] = flattened
del raw_data

data = data[mask, ...]

# split into training and testing sets
mask = np.random.choice([True, False], len(data), p=[0.75, 0.25])

training_data = data[mask, ...][:, 2:]
training_labels = data[mask, ...][:, :2]

mask = ~mask

testing_data = data[mask, ...][:, 2:]
testing_labels = data[mask, ...][:, :2]

norm_training_data = normalize(training_data)
norm_testing_data = normalize(testing_data)

del data

def model_fitness(tpl):
    global training_data, training_labels, norm_training_data, norm_training_labels, testing_data, testing_labels

    model = keras.Sequential()
    model.add(keras.Input(shape=(11,), name='data'))

    for layer in tpl.layers:
        model.add(keras.layers.Dense(layer[0], activation=layer[1]))

    model.add(keras.layers.Dense(2, activation=tpl.out_ac, name='output'))

    model.compile(optimizer='adam', loss='mean_absolute_error')

    if tpl.norm:
        model.fit(norm_training_data, training_labels, epochs=tpl.epochs, verbose=0)
        return model.evaluate(norm_testing_data, testing_labels, verbose=0)
    else:
        model.fit(training_data, training_labels, epochs=tpl.epochs, verbose=0)
        return model.evaluate(testing_data, testing_labels, verbose=0)

# Initial population
pop = [
    Model(True, 'relu', 50, [[512, 'relu'], [128, 'relu'], [512, 'relu'], [253, 'relu'], [254, 'relu'], [22, 'linear'], [48, 'linear']]),
    Model(True, 'relu', 50, [[244, 'relu'], [514, 'linear'], [502, 'relu'], [256, 'relu'], [256, 'relu'], [48, 'linear'], [113, 'relu'], [30, 'linear']]),
    Model(True, 'relu', 50, [[16, 'relu'], [256, 'relu'], [256, 'relu'], [512, 'linear'], [64, 'relu']]),
    Model(True, 'relu', 45, [[244, 'relu'], [512, 'relu'], [514, 'relu'], [48, 'linear'], [31, 'linear'], [32, 'linear'], [32, 'relu'], [128, 'linear'], [128, 'linear']]),
    Model(True, 'linear', 60, [[269, 'relu'], [478, 'relu'], [500, 'relu'], [505, 'linear'], [547, 'relu'], [76, 'relu']]),
    Model(True, 'linear', 50, [[138, 'relu'], [48, 'linear'], [133, 'linear'], [256, 'relu'], [256, 'relu'], [22, 'linear'], [38, 'relu']]),
    Model(True, 'linear', 50, [[16, 'relu'], [128, 'linear'], [512, 'relu'], [256, 'relu'], [256, 'relu'], [22, 'linear'], [48, 'linear'], [512, 'relu']]),
    Model(True, 'linear', 50, [[510, 'linear'], [138, 'linear'], [48, 'relu'], [128, 'relu'], [30, 'linear'], [64, 'relu'], [43, 'relu']]),
    Model(True, 'linear', 50, [[48, 'linear'], [21, 'linear'], [512, 'relu'], [44, 'linear'], [266, 'relu'], [32, 'linear'], [11, 'relu'], [71, 'linear'], [256, 'relu']]),
    Model(True, 'relu', 53, [[27, 'linear'], [265, 'relu'], [500, 'relu'], [515, 'relu'], [37, 'linear'], [86, 'linear'], [57, 'linear'], [32, 'relu'], [73, 'relu']]),
    Model(True, 'linear', 54, [[512, 'relu'], [138, 'linear'], [512, 'relu'], [253, 'relu'], [256, 'relu'], [10, 'relu'], [60, 'relu']]),
    Model(True, 'linear', 56, [[512, 'relu'], [128, 'relu'], [512, 'relu'], [258, 'linear'], [254, 'relu'], [32, 'linear'], [27, 'relu']])
] + GeneticCalculator.random(19, min_layers=4, max_layers=9, layer_size_choice=[16, 32, 48, 64, 128, 256, 512],
                             layer_activation=['relu', 'linear'], norm_choice=[True], out_ac_choice=['relu', 'linear'],
                             epochs_choice=[40, 50, 60])

# Gen calc instance
gen_calc = GeneticCalculator(pop, model_fitness, mutation_probability=0.25, selection_amount=6, selection_probability=0.6, verbose=3)
gen_calc.start(2)

while True:
    c = input("Set finished.\nC - Continue  E - Edit  Q - Quit")
    if c is 'C':
        gen_calc.start(int(input("Number of generations > ")))
    elif c is 'E':
        gen_calc.reconfigure(int(input("Selection amount > ")), float(input("Mutation probability > ")), float(input("Selection probability > ")))
    else:
        break
