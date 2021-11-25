# Fink broker tutorials

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/astrolabsoftware/fink-notebook-template/blob/main)

This repository contains materials (notebooks & presentation) to explore the [Fink broker](https://fink-broker.org) alert data. As of November 2021, Fink has collected more than 120 million alerts from the ZTF public stream, and processed more than 40 millions (after quality cuts). Among these, you will find extragalatic sources (supernovae, AGN, ...), galactic sources (many classes of transients incl. variables stars from our galaxy or gravitational microlensing events, ...) and moving objects from our Solar System (asteroids, comets, and made-man objects like space-debris!). Some sources are already confirmed, many are candidates!

## Materials

The repository contains a number of notebooks focusing on the use of the Fink REST API. We shortly present different science cases:

- Extragalactic science: AGN & supernovae ([see notebook](extragalactic/extragalactic.ipynb))
- Galactic science: variable stars & microlensing ([see notebook](galactic/galactic.ipynb))
- Solar system science: asteroids, comets & space debris ([see notebook](sso/sso.ipynb))
- Multi-messenger astronomy: searching for kilonovae ([see notebook](MMA/MMA.ipynb))
- Multi-messenger astronomy: correlating with gravitational waves sky maps ([see notebook](MMA/gravitational_waves.ipynb))
- Broker interfaces: presentation on the livestream service, the Science Portal and its API, and the Fink TOM module ([see the presentation](interfaces/README.md))

These sciences are not exhaustive and we welcome new collaborations to expand them! In addition, there are notebooks focusing on other specific aspects:

- How to tune the output rate of a Fink filter? Example for the Early SN Ia candidate filter ([see notebook](extragalactic/tuning_snia_output_rate.ipynb))

You can try the notebooks using Google Colab (follow the link above). You can also clone the repo, and try it locally (very little external libraries are required).

We also provide a Singularity script to work in a contained environment (thanks @bregeon):

- Build with `singularity build --fakeroot fink.sif Singularity`
- Run with `singularity run fink.sif`
- Open the link in your browser (from the host)


## How to contribute

How to contribute:

- Clone (or fork) this repo, and open a new branch.
- Create a new folder with a meaningful name (e.g. `supernovae`, `grb`, ...)
- Read and copy an existing notebook to get an idea of the structure of a tutorial.
- Once your notebook is finished, open a Pull Request such that we review the tutorial and merge it!
