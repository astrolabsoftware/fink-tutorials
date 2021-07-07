Bootstrap: docker

From: rockylinux/rockylinux

%post    
    dnf -y update
    dnf -y install wget && dnf -y groupinstall "Development Tools"     
    wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda.sh
    bash ~/miniconda.sh -b -p /opt/miniconda
    #/opt/miniconda/bin/conda init bash
    source /opt/miniconda/etc/profile.d/conda.sh
    conda config --add channels conda-forge    
    # fast deps resolution
    conda install mamba -n base
    # fink env
    conda create --name fink-nb python=3.7    
    conda activate fink-nb
    # install enough packages here so they are not installed via pip later
    mamba install pyerfa cython astropy bokeh numba emcee scipy\
                  numpy pandas matplotlib gatspy seaborn jupyter requests
    # these are the 2 specific ones
    pip install fink-science pyLIMA
    # clone notebooks
    cd /opt
    git clone https://github.com/astrolabsoftware/fink-notebook-template.git
    conda deactivate
    
%runscript
    source /opt/miniconda/etc/profile.d/conda.sh 
    conda activate fink-nb
    cd /opt/fink-notebook-template
    jupyter notebook
    

