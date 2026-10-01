# Fink Solar System tutorials

These tutorials have been given during the [LSST@EUROPE 8](https://lsst-europe8.hu/index.php) conference on 2026/10/01. Slides can be found [online](https://docs.google.com/presentation/d/1ZXTh_gdrZ6j1hKZou-27jggY74BlEmugOSdWhifgzUk/edit?usp=sharing).

- [0_lsst_sso_statistics.ipynb](0_lsst_sso_statistics.ipynb): play with stream statistics
- [1_ssobject.ipynb](1_ssobject.ipynb): how to query object data
- [2_ssoft.ipynb](2_ssoft.ipynb): how to query SSO Fink Table (SSOFT)
- [3_fast_rotator.ipynb](3_fast_rotator.ipynb): Characterizing a Super-fast Rotating Asteroid in Rubin Observatory First Alerts with Fink tools.

## Running the notebooks

Clone this repository using a shallow clone to reduce the volume of data to transfer:

```bash
git clone --depth 1 --single-branch --branch=main git@github.com:astrolabsoftware/fink-tutorials.git
```

Or you can only clone the relevant folder:

```bash
git clone --no-checkout --depth=1 --filter=tree:0 https://github.com/astrolabsoftware/fink-tutorials.git
cd fink-tutorials
git sparse-checkout set --no-cone /lsst/solar_system
git checkout
cd lsst/solar_system
```

Python 3.10 to 3.13 is recommended to run the notebooks. We suggest to use `jupyter-lab` in a Python virtual environment:

```bash
# Assuming you are on Linux
python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt
jupyter-lab
```
