import os
import requests
import pandas as pd
import matplotlib.pyplot as plt
from panoptes_client import (
    Panoptes,
    Project,
    SubjectSet,
    Subject,
    User,
    ProjectPreferences,
)

""" This is a template to query Fink API and send candidates to Zooniverse.org

    It uses:
    - Fink API https://fink-portal.org/api
    - Zooniverse client https://github.com/zooniverse/panoptes-python-client

    Beware!
    - It does not include project and subject creation
    - It is not at all optimized (e.g. single query, saves local files)
    - It only sends thumbnails to Zooniverse

    Questions? amoller@swin.edu.au
"""


def get_candidate_info(class_to_query="QSO_Candidate", n=5):
    """Get candidates from Fink API

    Args:
        class_to_query (str): queried Fink substream
        n (int): number of candidates queried (limited by API)

    Returns:
        idxs (list of string): lit of unique ObjectIds from this query
    """
    # Get latests candidates for a given class
    r = requests.post(
        "http://134.158.75.151:24000/api/v1/latests",
        json={"class": class_to_query, "n": n},
    )
    pdf = pd.read_json(r.content)
    idxs = pdf["i:objectId"].unique()

    return idxs


def get_thumbnails(objId):
    """ Fetch cutout data from Fink API

    Currently it saves these cutouts before sending them
    this should be optimized

    Args:
        objId (str): ObjetId to query
    Returns:
        fname_thumbnails (str): path to cutouts
    """
    r = requests.post(
        "http://134.158.75.151:24000/api/v1/objects",
        json={"objectId": objId, "withcutouts": "True"},
    )
    pdf = pd.read_json(r.content)
    fig, axes = plt.subplots(1, 3, figsize=(15, 6))

    columns = [
        "b:cutoutScience_stampData",
        "b:cutoutTemplate_stampData",
        "b:cutoutDifference_stampData",
    ]
    for index, col in enumerate(columns):
        # 2D array
        data = pdf[col].values[0]

        # You could optimize the color range to highlight the galaxy
        axes[index].imshow(data)
        axes[index].set_title(col)

    path_thumbnails = "./thumbnails_test"
    os.makedirs(path_thumbnails, exist_ok=True)
    fname_thumbnails = f"{path_thumbnails}/{objId}_thumbnails.jpeg"
    plt.savefig(fname_thumbnails)

    return fname_thumbnails


def fetch_data(objId):
    """ Fetch thumbnails and metadata from a given event

    Args:
        objId (str): ObjetId to query
    Returns:
        data (dict): dictionary with thumbnail path + metadata
    """
    metadata = {"objectId": objId}

    fname_thumbnails = get_thumbnails(objId)

    data = {}
    data["location_ps"] = fname_thumbnails
    data["metadata"] = metadata

    return data


def send_data_to_project(data, project_id, subject_set_id):
    """Send retrieved data to Zooniverse project

    Args:
        data (dict): dictionary with thumbnail path + metadata
        project_id (int): number of Zooniverse project
        subject_set_id (int): number of Zooniverse subject

    """

    # get the project object
    project = Project.find(project_id)
    subject_set = SubjectSet().find(subject_set_id)
    existing_subject_set_name = subject_set.display_name  # get its name
    subject_set_name = existing_subject_set_name

    # Create a list of the existing subject metadata
    meta_list = []
    print("existing subjects:")
    for subject in subject_set.subjects:
        print(subject.id, subject.metadata)
        meta_list.append(subject.metadata)

    # When making list of subjects to add, check to see if the metadata of the subject you want to add is already in the set
    print("new subjects:")
    new_subjects = []
    for dat in data:

        # TO DO: add check to avoid double upload
        subject = Subject()

        subject.links.project = project
        subject.add_location(dat["location_ps"])

        subject.metadata.update(dat["metadata"])

        subject.save()
        new_subjects.append(subject)
        print("{}, new subject add to list".format(dat["metadata"]))

    print("new subjects to add: {}".format(new_subjects))

    # add the new subject list (data and metadata) to the already defined project subject set
    subject_set.add(new_subjects)

    return


if __name__ == "__main__":
    """Retrieve candidates from Fink and send them to Zooniverse
    """

    # Select your Fink substream
    # here we use as example SIMBAD QSO_Candidate
    # we only query for 5 alerts (n=5)
    idxs = get_candidate_info(class_to_query="QSO_Candidate", n=5)

    list_data = []
    for idx in idxs:
        data = fetch_data(idx)
        list_data.append(data)

    # Add YOUR Project and Subject ID
    project_id = 1234
    subject_set_id = 98111

    # Add YOUR Username and Password
    # a good practice is to use a key
    username = myusername
    xxxx = mypassword
    Panoptes.connect(username=username, password=xxxx)

    # Send your candidates to Zooniverse
    send_data_to_project(list_data, project_id, subject_set_id)

