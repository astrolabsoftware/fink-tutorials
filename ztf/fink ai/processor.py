"""User defined script"""
import preprocessing as pp 
import pandas as pd
import numpy as np


def processor(pdf: pd.DataFrame, model=None):
    """Run inference on alert

    Notes
    -----
    This script is written by users

    Parameters
    ----------
    pdf: pd.DataFrame
        DataFrame with alerts

    Returns
    -------
    y: pd.Series
        Vector of probabilities
    """
    if model is None:
        raise ValueError("You must provide a model")

    pdf = pp.make_cut(pdf)
    if not pdf.empty:
        pdf = pp.raw2clean(pdf)

        pdf = pp.run_sherlock(pdf)

        X, meta = pp.make_X(pdf)

        y = model.predict_proba(X).T[1]
    else:
        y = pd.Series(np.zeros(len(pdf), dtype=float))

    return y