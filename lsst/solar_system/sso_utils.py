from astropy.time import Time

UNIQUE_BANDS = ["u", "g", "r", "i", "z", "y"]
MARKERS = {
    "u": "o",
    "g": "<",
    "r": ">",
    "i": "s",
    "z": "*",
    "y": "p",
}

COLORS = {
    "u": "#15284f",
    "g": "#626d84",
    "r": "#afb2b9",
    "i": "#dbbeb2",
    "z": "#e89070",
    "y": "#f5622e",
}


def plot_lightcurve_allbands(time, flux, fluxErr, bands, ax, label=""):
    """Wrapper to plot all filter bands"""
    for band in UNIQUE_BANDS:
        mask = bands == band
        if mask.sum() == 0:
            continue
        ax.errorbar(
            Time(time[mask], format="mjd", scale="tai").datetime,
            flux[mask],
            fluxErr[mask],
            color=COLORS[band],
            marker=MARKERS[band],
            label=f"{band} band",
            ls="",
        )


def plot_lightcurve_singleband(
    time, flux, fluxErr, bands, ax, single_band, label="", color="C0", marker="o"
):
    """Wrapper to plot a single band"""
    mask = bands == single_band
    if mask.sum() == 0:
        print(f"No data for band {single_band}")
        return
    ax.errorbar(
        time[mask],
        flux[mask],
        fluxErr[mask],
        color=color,
        marker=marker,
        label=label,
        ls="",
    )
