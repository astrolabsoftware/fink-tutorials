# Fink broker tutorials

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/astrolabsoftware/fink-notebook-template/blob/main)

This repository contains materials (notebooks & presentation) to explore the [Fink broker](https://fink-broker.org) alert data from Vera C. Rubin Legacy Survey of Space and Time (LSST).

## Materials

The repository contains a number of notebooks focusing on the use of the Fink LSST REST API. 

You can try the notebooks using Google Colab (follow the link above). You can also clone the repo, and try it locally. Most notebooks will work with any Python verson higher than 3.5. We advise to work on a virtual environment:

```
python -m venv myenv
source myenv/bin/activate

pip install -r requirements.txt
# ... wait a bit

jupyter-notebook
# play with notebooks
```

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
