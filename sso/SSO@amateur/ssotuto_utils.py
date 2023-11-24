import matplotlib.pyplot as plt
import os
import json
import sbpy.data as sso_py
from astropy.time import Time
import astropy.units as u
import pandas as pd
import numpy as np


def plot_traj(pdf, id):
    ff_pdf = pdf[pdf["d:ssoCandId"] == id]
    fig = plt.figure()
    plt.scatter(ff_pdf["d:ra"], ff_pdf["d:dec"])
    plt.title(f"{id} sky trajectory")
    plt.xlabel("right ascension (degree)")
    plt.ylabel("declination (degree)")
    plt.show()


def plot_lc(pdf, id):
    ff_pdf = pdf[pdf["d:ssoCandId"] == id]
    fig = plt.figure()
    filt_label = {
        1: "g band",
        2: "r band"
    }
    for filt in ff_pdf["d:fid"].unique():
        filt_mask = ff_pdf["d:fid"] == filt
        plt.errorbar(
            ff_pdf[filt_mask]["d:jd"], 
            ff_pdf[filt_mask]["d:magpsf"],
            yerr=ff_pdf[filt_mask]["d:sigmapsf"],
            linestyle="",
            marker="o",
            label=filt_label[filt]
        )
    plt.title(f"{id} lighcurve")
    plt.legend()
    plt.xlabel("right ascension (degree)")
    plt.ylabel("declination (degree)")
    plt.show()


def write_target_json(orb_list):

    dict_param = dict()
    dict_param["type"] = "Asteroid"
    dynamical_parameters = dict()
    
    dynamical_parameters["ref_epoch"] = orb_list[0]
    dynamical_parameters["semi_major_axis"] = orb_list[1]
    dynamical_parameters["eccentricity"] = orb_list[2]
    dynamical_parameters["inclination"] = orb_list[3]

    # dynamical_parameters["node_longitude"] = rows["Node"]
    # dynamical_parameters["perihelion_argument"] = rows["Peri"]
    # dynamical_parameters["mean_anomaly"] = rows["M"]

    dynamical_parameters["node_longitude"] = orb_list[4]
    dynamical_parameters["perihelion_argument"] = orb_list[5]
    dynamical_parameters["mean_anomaly"] = orb_list[6]

    dict_param["dynamical_parameters"] = dynamical_parameters

    with open(
        os.path.join("@aster_{}.json".format(int(orb_list[7]))), "w"
    ) as outfile:
        json.dump(dict_param, outfile, indent=4)

def write_target(orb_df):
    orb_select = orb_df[["ref_epoch", "a", "e", "i", "long. node", "arg. peric", "mean anomaly", "trajectory_id"]].values
    
    for orb_elem in orb_select:
        write_target_json(orb_elem)

def df_to_orb(df_orb: pd.DataFrame) -> sso_py.Orbit:
    with pd.option_context("mode.chained_assignment", None):
        df_orb["targetname"] = df_orb["d:ssoCandId"]
        df_orb["orbtype"] = "KEP"

        df_orb["H"] = 14.45
        df_orb["G"] = 0.15

    orb_dict = df_orb.to_dict(orient="list")

    orb_dict["a"] = orb_dict["d:a"] * u.au
    orb_dict["i"] = orb_dict["d:i"] * u.deg
    orb_dict["e"] = orb_dict["d:e"]
    orb_dict["node"] = orb_dict["d:long_node"] * u.deg
    orb_dict["argper"] = orb_dict["d:arg_peric"] * u.deg
    orb_dict["M"] = orb_dict["d:mean_anomaly"] * u.deg
    orb_dict["epoch"] = Time(orb_dict["d:ref_epoch"], format="jd")
    orb_dict["H"] = orb_dict["H"] * u.mag

    ast_orb_db = sso_py.Orbit.from_dict(orb_dict)
    return ast_orb_db


def compute_ephem(
    orbits: pd.DataFrame, epochs: list, location: str = "I41"
) -> pd.DataFrame:
    orb_table = df_to_orb(orbits)

    return sso_py.Ephem.from_oo(
        orb_table, epochs=Time(epochs, format="jd"), location="I41", scope="basic"
    ).table.to_pandas()


def plot_perf_ephem(pdf_orb, pdf_lc, ff_id):
    
    tmp_orb = pdf_orb[pdf_orb["d:ssoCandId"] == ff_id]
    tmp_lc = pdf_lc[pdf_lc["d:ssoCandId"] == ff_id].reset_index()
    
    ephem = compute_ephem(tmp_orb, tmp_lc["d:jd"].values).reset_index()
    
    # Compute ephemeris error
    deltaRAcosDEC = (tmp_lc["d:ra"] - ephem["RA"]) * np.cos(np.radians(tmp_lc["d:dec"])) * 3600
    deltaDEC = (tmp_lc["d:dec"] - ephem["DEC"]) * 3600

    colors = ["#15284F", "#F5622E"]

    fig, ax = plt.subplots(sharex=True,)

    plt.title("Trajectory with the corresponding ephemeris")

    ax.scatter(
        tmp_lc["d:ra"],
        tmp_lc["d:dec"],
        label="ZTF",
        alpha=0.2,
        color=colors[1],
    )

    ax.plot(
        ephem["RA"],
        ephem["DEC"],
        ls="",
        color="black",
        marker="x",
        alpha=0.2,
        label="Ephemerides",
    )
    ax.legend(loc="best")
    ax.set_xlabel("RA ($^o$)")
    ax.set_ylabel("DEC ($^o$)")

    axins = ax.inset_axes([0.2, 0.2, 0.45, 0.45])

    axins.plot(deltaRAcosDEC, deltaDEC, ls="", color=colors[0], marker="x")
    axins.errorbar(
        np.mean(deltaRAcosDEC),
        np.mean(deltaDEC),
        xerr=np.std(deltaRAcosDEC),
        yerr=np.std(deltaDEC),
    )
    axins.axhline(0, ls="--", color="black")
    axins.axvline(0, ls="--", color="black")
    axins.set_xlabel(r"$\Delta$RA ($^{\prime\prime}$)")
    axins.set_ylabel(r"$\Delta$DEC ($^{\prime\prime}$)")

    plt.show()



if __name__ == "__main__":
    import requests
    import io
    from rich.console import Console
    from rich.markdown import Markdown
    import sys


    r_lc = requests.post(
    'https://fink-portal.org/api/v1/ssocand',
    json={
        'kind': "orbParams", # Mandatory, `orbParams` or `lightcurves`
        # 'ssoCandId': int, # optional, if you know a trajectory ID. Otherwise returns all.
        # 'start_date': str, # optional. Only for lightcurves. Default is 2019-11-01
        # 'stop_date': str, # optional. Only for lightcurves. Default is today.
        # 'output-format': str
        'maxnumber': 15000
    }
    )
    # Format output in a DataFrame
    pdf_orb = pd.read_json(io.BytesIO(r_lc.content)).sort_values(["d:ssoCandId", "d:ref_epoch"])
    pdf_orb

    console = Console()
    console.print(Markdown(compute_ephem(pdf_orb.iloc[:3], [Time("2023-11-23").jd, Time("2023-11-24").jd]).to_markdown()))