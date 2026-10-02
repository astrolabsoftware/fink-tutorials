"""Data processing and feature engineering functions to go from raw alert stream to X and metadata

These utilities are DELIBERATELY not modularised into separate sub modules such that 
we can include this file as an artifact in our MLFlow logging allowing for complete
reproducibility with just this file alone. 

To help readability, additional comments and sectioning is used. 
"""
import pandas as pd
import logging
import numpy as np
import os
from fink_client.visualisation import extract_field
import lasair

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, 
                    format="%(asctime)s [%(levelname)s] %(name)s.%(funcName)s: %(message)s")

# #################################
# Make cuts on Alert df
# #################################
def make_cut(alerts_df: pd.DataFrame):
    """User-defined cuts on alerts - THESE ARE MINE ADD YOUR OWN"""
    # Include new taxonomy
    f1 = alerts_df["cdsxmatch"] == "Unknown"
    f2 = alerts_df["roid"] != 3
    f3 = alerts_df["candidate"].apply(lambda x: x["magpsf"]) > 19.5
    f4 = alerts_df["candidate"].apply(lambda x: x["drb"]) > 0.5
    return alerts_df[f1 & f2 & f3 & f4]

# #################################
# Alert df to Clean data 
# #################################

def raw2clean(alerts_df: pd.DataFrame) -> pd.DataFrame:
    """Process alerts into a clean DataFrame with relevant columns.
    
    Parameters:
        alerts_df (pd.DataFrame): DataFrame containing raw alerts with nested structures.
        It is extracted with pd.from_records(alerts) where alerts is obtained from 
        mlflink.polling.poll_n_alerts function. The pd.from_records is the only 
        aspect of preprocessing not done in this module.
    """

    logger.info("Extracting columns of interest from alerts.")

    alerts_df['mag'] = alerts_df.apply(lambda alert: extract_field(alert, 'magpsf'), axis=1)
    alerts_df['maglim'] = alerts_df.apply(lambda alert: extract_field(alert, 'diffmaglim'), axis=1)
    alerts_df['mjd'] = alerts_df.apply(lambda alert: extract_field(alert, 'jd'), axis=1) - 2400000.5
    alerts_df['fid'] = alerts_df.apply(lambda alert: extract_field(alert, 'fid'), axis=1)
    alerts_df['isdiffpos'] = alerts_df.apply(lambda alert: extract_field(alert, 'isdiffpos'), axis=1)
    alerts_df['ra'] = alerts_df.apply(lambda row: row['candidate']['ra'], axis=1)
    alerts_df['dec'] = alerts_df.apply(lambda row: row['candidate']['dec'], axis=1)
    alerts_df['drb'] = alerts_df.apply(lambda row: row['candidate']['drb'], axis=1)


    logger.info("Alerts processed into dataframe: %d", len(alerts_df))

    return alerts_df[[
        'candid', 'objectId', 'ra', 'dec', 'drb',
        'mjd', 'mag', 'maglim', 'fid', 'isdiffpos',
        'lc_features_g', 'lc_features_r'
    ]]


# ###############################################
# Clean data to curated data 
# ###############################################

def run_sherlock(alert_data:pd.DataFrame):
    # TODO: add description of what run_sherlock does for me. 
    """Run Sherlock on the alert data processed by process_data."""

    if "LASAIR_TOKEN" not in os.environ:
        alert_data['sherl_class'] = np.nan
        alert_data['sep_arcsec'] = np.nan
        return alert_data
    
    logger.info("Running Sherlock classification on alerts.")
    # the lasair client will be used for fetching Sherlock data
    L = lasair.lasair_client(os.environ.get('LASAIR_TOKEN'), 
                             endpoint='https://lasair-ztf.lsst.ac.uk/api')
    
    sherl_class = []
    sherl_separcsec = []

    for i in range(alert_data.shape[0]):
        _sherl = L.sherlock_position(alert_data.iloc[i]['ra'], alert_data.iloc[i]['dec'], lite=False)
        sherl_class.append(_sherl['classifications']['transient_00000'][0])
        try:
            sherl_separcsec.append(_sherl['crossmatches'][0]['separationArcsec'])
        except IndexError:
            # If orphan will get no match 
            sherl_separcsec.append(np.nan)

    logger.info("Successfully retrieved Sherlock classifications for %d alerts.", len(sherl_class))
    data_w_sherl = alert_data.join(pd.DataFrame(np.atleast_2d([sherl_class, sherl_separcsec]).T, 
                                                columns=['sherl_class', 'sep_arcsec']))
    
    # remove AGNs and Variable Stars
    mask = (data_w_sherl['sherl_class'] == 'AGN') | (data_w_sherl['sherl_class'] == 'VS')
    clean_data = data_w_sherl[~mask]
    logger.info("After removing AGNs and Variable Stars, %d alerts remain.", clean_data.shape[0])
    return clean_data


# ###############################################
# Curated data to features and metadata
# ###############################################

# Lc features from fink I've decided to keep for now
fink_lc_features_to_keep = ['amplitude', 
                       'linear_fit_reduced_chi2', 
                       'linear_fit_slope', 
                       'linear_fit_slope_sigma', 
                       'median', 
                       'median_absolute_deviation']


def vra_lc_features(row):
    """Function to compute light curve features on each row of a dataframe.
    To be applied to data saved by the poll_n_alerts function in consumer.py.
    """

    # need to make sure I ignore the negative diffs
    
    pos_diffs = (row.isdiffpos == 't')

    # NUMBER OF DETECTIONS
    try:    
        ndets = sum(pos_diffs)
    except TypeError:
        if pos_diffs is True:

            ndets = 1
        else:
            # it's a positive diff or if it's None (to detection) we set ndets to 0 
            ndets = 0

    # NUMBER OF NON-DETECTIONS
    nnondets = sum(pd.isna(row['mag']))


    if ndets == 0:
        return 0, nnondets, np.nan, np.nan
    
    dets_median = np.nanmedian(row['mag'][pos_diffs])
    dets_std = np.nanstd(row['mag'][pos_diffs])

    return ndets, nnondets, dets_median, dets_std


def make_X(clean_data: pd.DataFrame, 
                  fink_lc_features: list = fink_lc_features_to_keep
                  ) -> pd.DataFrame:
    """Make features from the clean data DataFrame. 
    The clean data is created by the consumer module and saved as parquet files. 
    They should be loaded into dataframes first before being given to this function.
    
    Parameters:
        clean_data (pd.DataFrame): DataFrame with columns 'candid', 'objectId', 'ra', 'dec', 'drb',
                                   'mjd', 'mag', 'maglim', 'fid', 'sep_arcsec' and light curve features.
        fink_lc_features (list): List of light curve features to keep from Fink.
    """
    if fink_lc_features is None:
        raise ValueError("fink_lc_features must be provided and not None.")
    
    # Create the VRA light curve features
    vra_feat_df = clean_data.apply(lambda row: vra_lc_features(row), axis=1, result_type='expand')
    vra_feat_df.columns = ['ndets', 'nnondets', 'dets_median', 'dets_std']
    clean_data_copy = clean_data.join(vra_feat_df) # add them to the clean data

    # Our clean data has cells that contains scalars, lists and dictionaries
    # here we clean this up to have a neat features data frame X where each row
    # corresponds to a sample (alert)

    # this is where we store the fink light curve features we want to keep
    lc_features_g_series = []
    lc_features_r_series = []
    vra_features = [] # ra, dec, drb, 'ndets', 'nnondets', 'dets_median', 'dets_std'
    # We iterate over each row of the clean data (each row is an alert)
    for i in range(clean_data_copy.shape[0]):
        # first we grab the "VRA" features, some are basic context from ZTF or sherlock,
        # others are the lightcurve features we computed above
        vra_features.append(clean_data_copy.iloc[i][['candid',
                                          'objectId',
                                          'ra', 
                                          'dec', 
                                          'drb', 
                                          'ndets', 
                                          'nnondets', 
                                          'dets_median', 
                                          'dets_std', 
                                          'sep_arcsec',
                                          ]])
        # Now we grab the Fink lightcurve features for g and r bands
        lc_features_g_series.append(pd.Series(clean_data_copy.iloc[i]['lc_features_g'
                                                                      ])[fink_lc_features])
        lc_features_r_series.append(pd.Series(clean_data_copy.iloc[i]['lc_features_r'
                                                                      ])[fink_lc_features])

    # Now we create a DataFrame X that contains all the features
    X = pd.DataFrame(vra_features).join(pd.DataFrame(lc_features_g_series)
                                        ).join(pd.DataFrame(lc_features_g_series), 
                                               rsuffix='r_')
    # We use candid as a in index because it is UNIQUE
    X.set_index('candid', inplace=True)

    # Then we separate the features and the object names
    meta = X[['objectId']]
    X = X.drop(['objectId'], axis=1)

    return X, meta


# ###############################################
# Entry point expected by fink ai 
# ###############################################

def pre_processing(data: dict) -> dict:
    """Preprocess a single raw alert into ML-ready features.

    This is the entry point looked up by mlflow-preprocessing-runner's
    runner.py when this file is logged to MLflow and built into a Docker
    image: it must be named exactly `pre_processing` and take/return a
    single record (dict), not a DataFrame.

    `data` is expected to already be past the make_cut() filtering stage
    (done upstream, at the Fink topic level).
    """
    alerts_df = pd.DataFrame([data])
    clean_df = raw2clean(alerts_df)
    curated_df = run_sherlock(clean_df)
    X, meta = make_X(curated_df)

    result = X.iloc[0].to_dict()
    result['candid'] = X.index[0]
    result['objectId'] = meta.iloc[0]['objectId']
    return result