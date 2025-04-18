from matplotlib import pyplot as plt
import pandas as pd
import numpy as np
import ast, mne

#Function to return montage in correct space with fiducials loadedv
def get_montage_from_bs(electrode_data: pd.DataFrame, electrode_space: str, subjects_dir):
    #Conversion between brainstorm and MNE naming systems for coordinate systems 
    bs_mne_lookup = {
        "MNI": "mni_tal",
        "SCS": "head", 
        "World": "mri"
    }
    
    #Format data appropriately
    montage_channels = list(electrode_data["Channel"])
    montage_positions = np.array([ast.literal_eval(coord) for coord in electrode_data[electrode_space]]) / 1000

    if electrode_space == "MNI":
        #In MNI, just used fsaverage fiducials 
        fsav_fids = mne.coreg.get_mni_fiducials('fsaverage', subjects_dir=subjects_dir)
        nasion=np.array(fsav_fids[1]['r'])
        lpa=np.array(fsav_fids[0]['r'])
        rpa=np.array(fsav_fids[2]['r'])
    elif electrode_space == "World":
        
        nasion=[1.266342575278442e+02,2.254817422002587e+02,1.150572758809693e+02]
        lpa= [49.933001177278450,1.278225305569983e+02,1.069552155676635e+02]
        rpa= [2.052676423521206e+02,1.263183766548090e+02,1.108142123239688e+02]
    elif electrode_space == "SCS":
        pass
    else:
        raise ValueError(f"{electrode_space} coordinate system was not found in brainstorm output")
    
    montage = mne.channels.make_dig_montage(
        ch_pos=dict(zip(montage_channels, montage_positions)),
        nasion=nasion,
        lpa=lpa,
        rpa=rpa,
        coord_frame=bs_mne_lookup[electrode_space]
    )

    return(montage)


def apply_standard_filters(edf, HIGH_PASS_CUTOFF, NOTCH_FREQS):
    #High pass and bandpass filter
    raw_highpass = edf.copy().filter(l_freq=HIGH_PASS_CUTOFF, h_freq=None)
    raw_allfilter = raw_highpass.copy().notch_filter(freqs=NOTCH_FREQS)

    return raw_allfilter

def print_epochs_rejection_info(epochs, epochs_rej):
    percent_rej = (len(epochs) - len(epochs_rej)) / len(epochs)*100
    num_rej = len(epochs)-len(epochs_rej)
    num_clean = len(epochs_rej)
    print('Percent rej =', percent_rej)
    print('Num rej =', num_rej)
    print('Num clean =', num_clean)
    return num_rej, percent_rej


def plot_epochs_rejcount_by_channel(epochs_rej, method='zscore', threshold=2, plot=True):
    """
    Plots the rejection count per channel with an indication for outliers.
    This can be useful to check if a lot of epochs were rejected due to one noisy
    channel, it might be more data-economical to drop the channel instead
    
    Parameters:
        epochs_rej : mne.Epochs object after threshold rejection has been applied
        method (str): Method to detect outliers ('zscore' or 'iqr'). Default is 'zscore'.
        threshold (float): Threshold for detecting outliers. Default is 2 (for Z-score).

    returns
    ---------
    fig :  matplotlib figure
    """
    # epochs_rej.drop_log is a tuple of tuples that has the length of epochs before rejection
    # here first flattening epochs_rej.drop_log to count unique values
    rej_log_flat = np.array([item for subtuple in epochs_rej.drop_log for item in subtuple]) 
    channels, counts = np.unique(rej_log_flat, return_counts=True)

    # Detect outliers
    if method == 'zscore':
        # Z-score method
        mean = np.mean(counts)
        std = np.std(counts)
        z_scores = (counts - mean) / std
        outlier_indices = np.where(np.abs(z_scores) > threshold)[0]
    elif method == 'iqr':
        # IQR method
        q1 = np.percentile(counts, 25)
        q3 = np.percentile(counts, 75)
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        outlier_indices = np.where((counts < lower_bound) | (counts > upper_bound))[0]
    else:
        raise ValueError("Method must be 'zscore' or 'iqr'.")

    # Plot the rejection count per channel
    if plot:
        fig = plt.figure()
        plt.bar(channels, counts, color='skyblue', label='Rejection Counts')
        plt.xlabel('Channels')
        plt.ylabel('Rejection Counts')
        plt.title('Rejection Count per Channel\n* = outliers')
        plt.xticks(rotation=90)
    
        # Mark the outliers with a star
        for index in outlier_indices:
            plt.text(index, counts[index] + 1, '*', ha='center', va='bottom', color='red', fontsize=16)
    
        plt.tight_layout()
        plt.legend()
        plt.show()

    return fig


def drop_channel_then_print_new_epoch_rejcount(epochs, bad_channels, rejection_threshold):
    '''
    handy function that allows to quickly iterate over some channels to see if dropping thenm
    reduces the number of epochs rejected based on rejection_threshold
    '''
    _epochs_rej = epochs.copy()
    _epochs_rej.drop_channels(bad_channels)
    _epochs_rej.drop_bad(reject=rejection_threshold, verbose='warning')

    print_epochs_rejection_info(epochs, _epochs_rej)
    plot_epochs_rejcount_by_channel(_epochs_rej, method='zscore', threshold=2)


#Function to plot SEEG contacts over MNI fsaverage brain
def plot_seeg_freesurfer(data, subjects_dir, subject_ID='fsaverage',
                         views=['lat', 'med', 'axial'],
                         electrode_cmap='tab20'):

    '''
    data : mne object such as raw, epochs
    '''
    
    data = data.copy()

    montage = data.get_montage()
    head_mri_t = mne.coreg.estimate_head_mri_t(subject_ID, subjects_dir)
    montage.apply_trans(head_mri_t)
    data.set_montage(montage)

    trans = mne.channels.compute_native_head_t(montage)
    brain = mne.viz.Brain(
        subject=subject_ID,
        subjects_dir=subjects_dir,
        cortex="low_contrast",
        alpha=0.25,
        background="white",
        views=views,
    )

    # Build a color map here so it's one color per electrode shaft:
    plot_channels = [ch for ch in montage.get_positions()['ch_pos'].keys() if ch not in data.info['bads']]
    first_letter = set([ch[0] for ch in plot_channels])
    cmap = plt.get_cmap(electrode_cmap)  # Choose a colormap. 'tab20' is good for distinct colors.
    colors = [cmap(i / len(first_letter)) for i in range(len(first_letter))]
    cmap_dict = dict(zip(first_letter, colors))
    color_dict = {ch: cmap_dict[ch[0]] for ch in plot_channels}

    #Add sensors
    brain.add_sensors(data.info, trans=trans, sensor_colors=color_dict.values(), verbose=True)

    #Add channel names -> not working
    # for ch_name, ch_coord in montage.get_positions()['ch_pos'].items():
    #     if ch_name.endswith("'1"):
    #         print(f"{ch_name}: {ch_coord}")
    #         brain._renderer.text3d(x=ch_coord[0], y=ch_coord[1], z=ch_coord[2], 
    #                     text=ch_name, scale=50, color='black')

    # # Add volume labels from freesurfer
    # labels = ["ctx-lh-caudalmiddlefrontal", "ctx-lh-precentral", "ctx-lh-superiorfrontal", "Left-Putamen"]
    # brain.add_volume_labels(aseg="aparc+aseg", labels=labels)

    #Show
    brain.show_view()

    return brain