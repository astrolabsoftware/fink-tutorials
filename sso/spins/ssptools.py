import pandas as pd
import requests
from astropy.io.votable import parse

def ephemsys(des, ep, nbd=None, step=None, gensol=None, tscale=None, user=None):
    '''Gets ephemerides of binary systems from IMCCE Miriade

    :des: str - SSO designation (number or name)
    :ep: float, str, list - Epoch of computation
    :returns: pd.DataFrame - The ephemerides
              False - If query failed somehow
    '''
    
    # Global variables
    url = 'https://ssp.imcce.fr/webservices/miriade/api/ephemsys.php?'
    file_name = "ephemsys.xml"

    
    # Define parameters
    params = { '-name': f'{des}' }
    if gensol!=None: 
        params['-gensol'] = gensol 
    if tscale!=None: 
        params['-tscale'] = tscale 
    if user!=None: 
        params['-from'] = user 


    # Single epoch of computation
    if type(ep)!=list:
        # Set parameters
        params['-ep'] = ep
        if nbd!=None: 
            params['-nbd'] = nbd
        if step!=None: 
            params['-step'] = step

        # Execute query
        try:
            r = requests.post(url, params=params, timeout=80)
        except requests.exceptions.ReadTimeout:
            return False


    # Multiple epochs of computation
    else:
        # Epochs of computation
        files = {'epochs': ('epochs', '\n'.join(['%.6f' % epoch
                                                 for epoch in ep]))}

        # Execute query
        try:
            r = requests.post(url, params=params, files=files, timeout=50)
        except requests.exceptions.ReadTimeout:
            return False


    # Write the result to disk
    file = open(file_name, "w")
    file.write(r.text)
    file.close()

    # Parse the VOTable
    tab = parse(file_name).get_table_by_index(1).to_table().to_pandas()

    return tab



# Define a simple ephemerides query
def ephemcc(ident, ep, nbd=None, step=None, observer='500', rplane='1', tcoor=5):
    '''Gets asteroid ephemerides from IMCCE Miriade for a suite of JD for a single SSO
    Original function by M. Mahlke

    :ident: int, float, str - asteroid identifier
    :ep: float, str, list - Epoch of computation
    :observer: str - IAU Obs code - default to geocenter: https://minorplanetcenter.net//iau/lists/ObsCodesF.html
    :returns: pd.DataFrame - Input dataframe with ephemerides columns appended
              False - If query failed somehow

    '''
    
    # ------
    # Miriade URL 
    url = 'https://ssp.imcce.fr/webservices/miriade/api/ephemcc.php'
    
    if rplane=='2':
        tcoor='1'
        
    # Query parameters
    params = {
        '-name': f'{ident}',
        '-mime': 'json',
        '-rplane': rplane,
        '-tcoor': tcoor,
        '-output': '--jd',
        '-observer': observer, 
        '-tscale': 'UTC'
    }
    

    # Single epoch of computation
    if type(ep)!=list:
        # Set parameters
        params['-ep'] = ep
        if nbd!=None: 
            params['-nbd'] = nbd
        if step!=None: 
            params['-step'] = step

        # Execute query
        try:
            r = requests.post(url, params=params, timeout=80)
        except requests.exceptions.ReadTimeout:
            return False


    # Multiple epochs of computation
    else:
        # Epochs of computation
        files = {'epochs': ('epochs', '\n'.join(['%.6f' % epoch
                                                 for epoch in ep]))}

        # Execute query
        try:
            r = requests.post(url, params=params, files=files, timeout=50)
        except requests.exceptions.ReadTimeout:
            return False


#    # Pass sorted list of epochs to speed up query
#    files = {'epochs': ('epochs', '\n'.join(['%.6f' % epoch
#                                             for epoch in jd]))}
#    # Execute query
#    try:
#        r = requests.post(url, params=params, files=files, timeout=2000)
#    except requests.exceptions.ReadTimeout:
#        return False

    j = r.json()

    # Read JSON response
    try:
        ephem = pd.DataFrame.from_dict(j['data'])
    except KeyError:
        return False

    return ephem
