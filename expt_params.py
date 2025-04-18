
params = dict(
# ---- Data dirs
logfiles_dir = '/Users/kamronsoldozy/Documents/PhD/ANALYSIS/SEEG_PREPROCESSING/LOGS',
channels_info_dir = '/Users/kamronsoldozy/Documents/PhD/ANALYSIS/DATA/MNI_FILES/', #This is where the out_EMUXXX.xlsx files are.


    
# output dirs
outdir_edfs = '/Users/kamronsoldozy/Documents/PhD/ANALYSIS/DATA/EDFs/',
outdir_epochs = '/Users/kamronsoldozy/Documents/PhD/ANALYSIS/SEEG_PREPROCESSING/EPOCHS',
outdir_logging = '/Users/kamronsoldozy/Documents/PhD/ANALYSIS/SEEG_PREPROCESSING/LOGS',
    
electrode_space = "MNI",
subjects_dir = '/Applications/freesurfer/7.4.1/subjects',



# downsampling
resample_fs = 1000, # in Hz, if not required: None

# filters settings
high_pass_cutoff = 0.1,
notch_freqs = (60, 120, 180, 240),


# epochs params
epochs_tmin = -0.1,
epochs_tmax = 0.8,
epochs_baseline = (-0.1, 0),
epochs_decim = 1
)

# photodiode_delay = None

