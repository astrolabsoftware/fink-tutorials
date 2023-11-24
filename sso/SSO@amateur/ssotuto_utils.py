import matplotlib.pyplot as plt
import io
import json
import sbpy.data as sso_py
from astropy.time import Time
import astropy.units as u
import pandas as pd
import numpy as np
from astropy.coordinates import SkyCoord
import astropy.units as u
import requests


def plot_traj(pdf: pd.DataFrame, id: str):
    """
    Plot trajectories with ra,dec coordinates

    Parameters
    ----------
    pdf : pd.DataFrame
        dataframe containing the trajectories observations
    id : str
        the id of the trajectory to plot
    """
    ff_pdf = pdf[pdf["d:ssoCandId"] == id].sort_values("d:jd")
    fig = plt.figure()
    plt.scatter(ff_pdf["d:ra"], ff_pdf["d:dec"])
    plt.title(f"{id} sky trajectory")
    plt.xlabel("right ascension (degree)")
    plt.ylabel("declination (degree)")
    plt.show()


def plot_lc(pdf: pd.DataFrame, id: str):
    """
    Plot the lightcurve of the trajectory

    Parameters
    ----------
    pdf : pd.DataFrame
        dataframe containing the trajectories observations
    id : str
        the id of the trajectory to plot
    """
    ff_pdf = pdf[pdf["d:ssoCandId"] == id].sort_values("d:jd")
    fig = plt.figure()
    filt_label = {
        1: "g band",
        2: "r band"
    }
    for filt in ff_pdf["d:fid"].unique():
        filt_mask = ff_pdf["d:fid"] == filt
        plt.errorbar(
            Time(ff_pdf[filt_mask]["d:jd"], format="jd").to_datetime(), 
            ff_pdf[filt_mask]["d:magpsf"],
            yerr=ff_pdf[filt_mask]["d:sigmapsf"],
            linestyle="",
            marker="o",
            label=filt_label[filt]
        )
    plt.xticks(rotation=45, ha='right')
    plt.title(f"{id} lighcurve")
    plt.legend()
    plt.xlabel("time (days in julian date)")
    plt.ylabel("apparent magnitude")
    plt.show()

# ==== Ephemeries with Miriade
def write_target_json(orb_list: list) -> io.BytesIO:

    dict_param = dict()
    dict_param["type"] = "Asteroid"
    dict_param["name"] = "x"
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
    
    f = io.StringIO()
    json.dump(dict_param, f, indent=4)
    f.seek(0)
    return f

def write_target(orb_df):
    orb_select = orb_df[[
        "d:ref_epoch", 
        "d:a", "d:e", "d:i", 
        "d:long_node", 
        "d:arg_peric", 
        "d:mean_anomaly", 
        "d:ssoCandId"
    ]].values

    return [write_target_json(orb_elem) for orb_elem in orb_select]

def request_ephem(in_memory_json, ephem_date, tr_id, location):
    url = "https://ssp.imcce.fr/webservices/miriade/api/ephemcc.php"
    # url = "https://ssp.imcce.fr/webservices/miriade/miriade.php"
    
    params = {
        "-name": "",
        "-type": "Asteroid",
        "-tscale": "UTC",
        "-observer": location,
        "-theory": "INPOP",
        "-teph": 1,
        "-tcoor": 5,
        "-oscelem": "MPCORB",
        "-mime": "json",
        "-output": "--jd",
        "-from": "MiriadeDoc",
    }
    in_memory_json.seek(0)
    files = {
        "target": in_memory_json.read().encode(),
        "epochs": ("epochs", "\n".join(["%.6f" % epoch.jd for epoch in ephem_date])),
    }

    r = requests.post(url, params=params, files=files, timeout=2000)
    j = r.json()
    ephem = pd.DataFrame.from_dict(j["data"])

    coord = SkyCoord(ephem["RA"], ephem["DEC"], unit=(u.deg, u.deg))

    ephem["cRA"] = coord.ra.value * 15
    ephem["cDec"] = coord.dec.value
    ephem["trajectory_id"] = tr_id
    
    return ephem


def generate_ephem(pdf, start, stop, step, times, location="I41"):
    if times is not None and len(times) > 0:
        time_range = times
    else:
        time_range = Time(np.arange(Time(start).jd, Time(stop).jd, step), format="jd")

    in_memory_json = write_target(pdf)
    ephem = pd.concat(
        [
            request_ephem(mem_json, time_range, tr_id, location) 
            for mem_json, tr_id in zip(in_memory_json, pdf["d:ssoCandId"])
        ])
    ephem = ephem.rename({"trajectory_id": "targetname"}, axis=1)
    ephem["RA"] = ephem["cRA"]
    ephem["DEC"] = ephem["cDec"]
    ephem = ephem.drop(["cRA", "cDec"], axis=1)
    return ephem




# ==== Ephemeries with sbpy
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
    orbits: pd.DataFrame,start: str, stop:str, step: float, times: list, location: str = "I41"
) -> pd.DataFrame:
    
    if times is not None and len(times) > 0:
        time_range = times
    else:
        time_range = Time(np.arange(Time(start).jd, Time(stop).jd, step), format="jd")

    orb_table = df_to_orb(orbits)

    pdf_ephem = sso_py.Ephem.from_oo(
        orb_table, epochs=Time(time_range, format="jd"), location=location, scope="basic"
    ).table.to_pandas()
    pdf_ephem["Date"] = Time(pdf_ephem["epoch"]).jd
    return pdf_ephem


def ephemeries(pdf_orb, start=None, stop=None, step=None, times:list=None, location="I41", method="miriade"):
    if method == "miriade":
        return generate_ephem(pdf_orb, start, stop, step, times, location)
    elif method == "sbpy":
        return compute_ephem(pdf_orb, start, stop, step, times, location)
    else:
        raise NotImplemented("ephemeries generation method = {} not exists !")


def plot_perf_ephem(pdf_orb: pd.DataFrame, pdf_lc: pd.DataFrame, ff_id: str, method: str):

    tmp_orb = pdf_orb[pdf_orb["d:ssoCandId"] == ff_id]
    tmp_lc = pdf_lc[pdf_lc["d:ssoCandId"] == ff_id].sort_values("d:jd").reset_index()

    ephem_fit = ephemeries(
        tmp_orb, 
        Time(tmp_lc["d:jd"].values[0], format="jd").iso, 
        Time(tmp_lc["d:jd"].values[-1], format="jd").iso,
        1/24,
        method=method
    ).reset_index().sort_values("Date")

    ephem_residuals = ephemeries(
        tmp_orb, 
        times=Time(tmp_lc["d:jd"].values + 15/3600/24, format="jd"),
        method=method
    ).reset_index().sort_values("Date")

    # Compute ephemeris error
    deltaRAcosDEC = (tmp_lc["d:ra"] - ephem_residuals["RA"]) * np.cos(np.radians(tmp_lc["d:dec"])) * 3600
    deltaDEC = (tmp_lc["d:dec"] - ephem_residuals["DEC"]) * 3600

    colors = ["#15284F", "#F5622E"]

    fig, ax = plt.subplots(sharex=True,)

    plt.title("Trajectory with the corresponding ephemeris")

    ax.plot(
        ephem_fit["RA"],
        ephem_fit["DEC"],
        ls="--",
        lw=1,
        color="black",
        alpha=0.2,
        label="Ephemerides",
    )
    ax.scatter(
        tmp_lc["d:ra"],
        tmp_lc["d:dec"],
        label="ZTF",
        alpha=0.5,
        s=50,
        color=colors[1],
    )

    ax.legend(loc="best")
    ax.set_xlabel("RA ($^o$)")
    ax.set_ylabel("DEC ($^o$)")

    axins = ax.inset_axes([0.2, 0.2, 0.45, 0.45])

    axins.scatter(deltaRAcosDEC, deltaDEC, c=tmp_lc["d:jd"].values, marker="x")
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

def prep_traj_for_orbfit(pdf_traj: pd.DataFrame)-> pd.DataFrame:
    with pd.option_context("mode.chained_assignment", None):
        pdf_traj = pdf_traj.rename({
                "d:magpsf": "dcmag", 
                "d:ra": "ra", 
                "d:dec": "dec", 
                "d:fid": "fid", 
                "d:jd": "jd"
            },
            axis=1
        )
        sso_id = pdf_traj["d:ssoCandId"].unique()
        map_id = {sso_cand_id: traj_id for sso_cand_id, traj_id in zip(sso_id, np.arange(len(sso_id)))}
        pdf_traj["trajectory_id"] = pdf_traj["d:ssoCandId"].map(map_id)
        return pdf_traj

def add_fake_point_to_traj(traj_pdf, fake_point):
    with pd.option_context("mode.chained_assignment", None):
        tmp = fake_point[["RA", "DEC", "Date"]]
        tmp["d:ssoCandId"] = traj_pdf["d:ssoCandId"].values[0]
        tmp["fid"] = 1
        tmp["dcmag"] = 17
        tmp["trajectory_id"] = 0
        tmp = tmp.rename({"RA": "ra", "DEC": "dec", "Date": "jd"}, axis=1)
        return pd.concat([traj_pdf, tmp])


def format_orbit(orb, ff_id):
    orb["d:ssoCandId"] = ff_id
    orb = orb.rename({
        "a": "d:a",
        "e": "d:e",
        "i": "d:i",
        "long. node": "d:long_node",
        "arg. peric": "d:arg_peric",
        "mean anomaly": "d:mean_anomaly",
        "ref_epoch": "d:ref_epoch"
    }, axis=1)
    return orb

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