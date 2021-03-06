"""
Created on Wed Feb 14 22:22:09 2018

@author: Anet
print(__doc__)
"""
import mne
import numpy as np
from mne import io
import platform; print(platform.platform())
import sys; print("Python", sys.version)
import numpy; print("NumPy", numpy.__version__)
import scipy; print("SciPy", scipy.__version__)
import sklearn; print("Scikit-Learn", sklearn.__version__)
import feature as ft
import lda as lda
import epochs_methods as epoch_met
import input_test_data as load_file_names
from builtins import print
import mix_data_x_y as mix
import config
import neural_network as neural_network
import print_results
from numpy.random import seed
from keras.models import load_model


seed(1)


#turn off log
mne.set_log_level('ERROR')
# import os
# os.environ["TF_CPP_MIN_LOG_LEVEL"]="4"

# Set path to raw data folder 
DATA_FOLDER ='C:/Users/Anet/eclipse-workspace/Classification/raw_data/'


# Set EEG event list - instruction



##############################################
#
#             Data loading
#
##############################################

# mapu, ve ktere jsou ulozeny nazvy trenovacich souboru a jejich targetove/non-targetove znacky
files_training_map = load_file_names.load_training_data_names()

# mapu, ve ktere jsou ulozeny nazvy testovacich souboru a jejich targetove nazvy
files_testing_map = load_file_names.load_predicting_data_names()



data_training_count = len(files_training_map)
data_predicting_count = len(files_testing_map)

##############################################
#
#            Loading data to train
#
##############################################
raw = []
for i in range(data_training_count):
    path = DATA_FOLDER + (files_training_map[i][0])
    raw.append(io.read_raw_brainvision(vhdr_fname=path, preload=True))
    raw[i].filter(config.low_filter_frequency,config.high_filter_frequency)
#     print(raw[i]._events)

##############################################
#
#             Loading data to predict
#
##############################################
raw_to_predict = []
true_prediction = []
for i in range(data_predicting_count):
    path = DATA_FOLDER + (files_testing_map[i][0])
    true_prediction.append(files_testing_map[i][1])
    true_prediction[i] = true_prediction[i].strip()
    raw_to_predict.append(io.read_raw_brainvision(vhdr_fname=path, preload=True))
    raw_to_predict[i].filter(config.low_filter_frequency,config.high_filter_frequency)

    
##############################################
#
#             Epochs creating
#
##############################################
    
# Vytvori epochy pro klasifikaci
event_to_predict = []
epochs_to_predict = []
for i in range(data_predicting_count):
    event_to_predict.append(raw_to_predict[i]._events)
 
    if(i < config.instruction_files_to_pred):

        epochs_to_predict.append(mne.Epochs(raw_to_predict[i],event_to_predict[i], event_id=config.event_id_instruction, tmin=config.epoch_tmin, tmax=config.epoch_tmax,baseline=(config.baseline_min, config.baseline_max), preload=True))
    else:
        epochs_to_predict.append(mne.Epochs(raw_to_predict[i],event_to_predict[i], event_id=config.event_id_matrix, tmin=config.epoch_tmin, tmax=config.epoch_tmax,baseline=(config.baseline_min, config.baseline_max), preload=True))
    
    

# Plot raw data
# raw[0].plot(block=True, lowpass=40, n_channels=5)

# for i in range(data_count): 
#    raw[i].plot(block=True, lowpass=40, n_channels=6)

##############################################
#
#             
#
##############################################




# Set color of events
"""


for i in range(data_count):
    mne.viz.plot_events(events[i],raw[i].info['sfreq'], raw[i].first_samp, color=config.color)
    """

#extract epochs

events_train = []
epochs = []
epochs_targets = []
epochs_non_targets = []



# Vytvori epochy, z vytvorenych Epoch potom vybere ty targetove a ulozi je do epochs_target

for i in range(data_training_count):
    events_train.append(raw[i]._events)
    
    if(i < config.instruction_files_count):
        epochs.append(mne.Epochs(raw[i],events_train[i], event_id=config.event_id_instruction, tmin=config.epoch_tmin, tmax=config.epoch_tmax,baseline=(config.baseline_min, config.baseline_max), preload=True))
        instruction = 1
    else:
        epochs.append(mne.Epochs(raw[i],events_train[i], event_id=config.event_id_matrix, tmin=config.epoch_tmin, tmax=config.epoch_tmax,baseline=(config.baseline_min, config.baseline_max), preload=True))
        instruction = 0
        
    epochs_targets.append(epoch_met.filter_epochs_target(epochs[i], events_train[i], files_training_map[i][1], instruction))  
    epochs_non_targets.append(epoch_met.filter_epochs_target(epochs[i], events_train[i], files_training_map[i][2], instruction))  
    


"""
for i in range(data_count):
    mne.viz.plot_epochs(epochs[i])
"""

# epochs.plot(title="Events epochs", n_epochs=(len(epochs.events)),event_colors=color)
# mne.viz.plot_epochs(epochs, title="Events epochs", n_epochs=15,event_colors=color)



# Create evoked structure

evoked_dict = [[]]
# jen pro instruction
for i in range(config.instruction_files_count):
    evoked_dict.append('')
    evoked_dict[i] = dict()
    for condition in config.conditions:
        evoked_dict[i][condition] = epochs[i][condition].average()
       

# Plot chart 

"""
for i in range(data_count):
    mne.viz.plot_compare_evokeds(evoked_dict[i], title="ERP chart", colors=config.colors, linestyles=config.linestyles, gfp=False)
"""

"""

Extrakce priznaku

"""
labels = epochs[0].events[:, -1]

#feature extraction
    
target_features = []
non_target_features = []
x = []


test_sample_count = 5


y = []


# Prepare data to training 
target_nontarget_epochs = epochs_targets + epochs_non_targets


for i in range(len(target_nontarget_epochs)):
    #count of target epochs     
    for j in range(len(target_nontarget_epochs[i])):
    
        pick_epochs = target_nontarget_epochs[i][j].pick_channels(config.chan)
        x.append(ft.feature_vector(pick_epochs))
        if(i < epochs_targets.__len__()):
            y.append(1)
        else:
            y.append(0)


# Prepare data to predict 
x_pred = []

y = np.array(y)

for i in range(data_predicting_count):
    x_pred.append([])
    for j in range(len(epochs_to_predict[i])):
        pick_epoch_to_predict = epochs_to_predict[i][j].pick_channels(config.chan)
        x_pred[i].append(ft.feature_vector(pick_epoch_to_predict))




mix.mix_data(x, y)

# X = np.reshape(X,(-1, 100))

##############################################
#
#             Predicting
#
##############################################

# plotting means of training data
# plt.plot(np.mean(X[y==1], axis=0))
# plt.plot(np.mean(X[y==0], axis=0))
# plt.show()


# plotting tests epochs
# for i in range(len(X_pred)):
#     name = str(i)+'.png'
#     plt.plot(X_pred[i])
#     plt.savefig(name)



x_event_lda = []
x_event_neural = []

print()
print("If you want to load model from file: 1")
print("If you want to train new model     : 0")
print()
model_load = input("Load model? 1/0: ")
if(model_load == '1'):
    config.model = load_model('save_models/mymodel_5.h5') 
else:
    if(model_load == '0'):
        neural_network.train(x, y)
    else:
        print("Invalid option")


for i in range(data_predicting_count):
    x_event_lda.append(lda.solve(x,y,x_pred[i]))
    x_event_neural.append(neural_network.solve(x_pred[i]))


for i in range(data_predicting_count):
    print()
    print("##########################################")
    print()
  
    
    if(i < config.instruction_files_to_pred):
        
        print(i+1,".) Expected solve: ",true_prediction[i])
        print()
        
        instruction = 1
        print("LDA: ")
        print_results.print_guess(x_event_lda[i], epochs_to_predict[i], true_prediction[i],instruction)
        print("Neural network: ")
        print_results.print_guess(x_event_neural[i], epochs_to_predict[i], true_prediction[i],instruction)
        
    else:
        if(i%2==1):
            print(i+1,".) Expected solve: ",true_prediction[i],true_prediction[i+1])
            
            print()
        
            instruction = 0
            print("LDA: ")
            print_results.print_guess(x_event_lda[i], epochs_to_predict[i], true_prediction[i],instruction)
            print("Neural network: ")
            print_results.print_guess(x_event_neural[i], epochs_to_predict[i], true_prediction[i],instruction)
        
    print()




