# coding: utf-8

from pathlib import Path
import argparse
from argparse import RawTextHelpFormatter
from matplotlib import image
# Scientific modules imports
import numpy as np
import pandas as pd

# AxonDeepSeg imports
from AxonDeepSeg.morphometrics.compute_morphometrics import *
import AxonDeepSeg.ads_utils as ads


def launch_morphometrics_computation(path_img, path_prediction, axon_shape="cicle"):
    """
    This function is equivalent to the morphometrics_extraction notebook of AxonDeepSeg.
    It automatically performs all steps (computations, savings, displays,...) of the
    morphometrics extraction of a given sample.
    :param path_img: path of the input image (microscopy sample)
    :param path_prediction: path of the segmented image (output of AxonDeepSeg)
    :param axon_shape: str: shape of the axon, can either be either be circle or an ellipse


    :return: none.
    """
    
    # If string, convert to Path objects
    path_img = convert_path(path_img)
    path_prediction = convert_path(path_prediction)

    try:
        # Read image
        img = ads.imread(path_img)

        # Read prediction
        pred = ads.imread(path_prediction)
    except (IOError, OSError) as e:
        print(("launch_morphometrics_computation: " + str(e)))
        raise
    else:

        # Get axon and myelin masks
        pred_axon = pred > 200
        pred_myelin = np.logical_and(pred >= 50, pred <= 200)

        # Get folder path
        path_folder = path_img.parent

        # Compute and save axon morphometrics
        stats_array = get_axon_morphometrics(pred_axon, path_folder, axon_shape=axon_shape)
        save_axon_morphometrics(path_folder, stats_array)

        # Generate and save displays of axon morphometrics
        fig = draw_axon_diameter(img, path_prediction, pred_axon, pred_myelin, axon_shape=axon_shape)
        save_map_of_axon_diameters(path_folder, fig)

        # Compute and save aggregate morphometrics
        aggregate_metrics = get_aggregate_morphometrics(
            pred_axon, pred_myelin, path_folder, axon_shape=axon_shape
        )
        write_aggregate_morphometrics(path_folder, aggregate_metrics)

def main(argv=None):
    ap = argparse.ArgumentParser(formatter_class=RawTextHelpFormatter)

    
    # Setting the arguments of the saving the morphometrics in excel file
    ap.add_argument('-s', '--sizepixel', required=False, help='Pixel size of the image(s) to segment, in micrometers. \n'+
                                                              'If no pixel size is specified, a pixel_size_in_micrometer.txt \n'+
                                                              'file needs to be added to the image folder path. The pixel size \n'+
                                                              'in that file will be used for the segmentation.',
                                                              default=None)


    ap.add_argument('-i', '--imgpath', required=True, help='Path to the image to be segmented ')

    
    ap.add_argument('-f', '--filename', required=False, nargs='+', help='Name of the excel file in which the morphometrics file will be  stored',
                                                              default = "morphometrics"  )

    

    # Processing the arguments
    args = vars(ap.parse_args(argv))
    image_path = Path(args["imgpath"])
    print("Image path is ", image_path)
    filename = str(args["filename"])


    print("Stem of image path is ", image_path.stem)

    #load the axon image 
    if (Path(image_path.stem + "_seg-axon.png")).exists():
        pred_axon = image.imread(image_path.stem + "_seg-axon.png")
        print(pred_axon.shape)
    else: 
        print("ERROR: Segmented axon mask is not present in the image folder  ",
                            "Please check that the axon mask is located in the image folder ",
                            "If it is not present, perform segmentation of the image first using ADS."
            )
        sys.exit(3)

    #load myelin image    
    if (Path(image_path.stem + "_seg-myelin.png")).exists():
        pred_myelin = image.imread(image_path.stem + "_seg-myelin.png")
        print(pred_myelin.shape)
    else: 
        print("ERROR: Segmented myelin mask is not present in the image folder  ",
                            "Please check that the myelin mask is located in the image folder ",
                            "If it is not present, perform segmentation of the image first using ADS."
            )
        sys.exit(3)



    if args["sizepixel"] is not None:
        psm = float(args["sizepixel"])
    else: # Handle cases if no resolution is provided on the CLI

        # Check if a pixel size file exists, if so read it.
        if (image_path.parent / 'pixel_size_in_micrometer.txt').exists():

            resolution_file = open(image_path.parent / 'pixel_size_in_micrometer.txt', 'r')

            psm = float(resolution_file.read())
        else:

            print("ERROR: No pixel size is provided, and there is no pixel_size_in_micrometer.txt file in image folder. ",
                            "Please provide a pixel size (using argument -s), or add a pixel_size_in_micrometer.txt file ",
                            "containing the pixel size value."
            )
            sys.exit(3)

   
    


    x = np.array([], dtype=[
                                ('x0', 'f4'),
                                ('y0', 'f4'),
                                ('gratio','f4'),
                                ('axon_area','f4'),
                                ('myelin_area','f4'),
                                ('axon_diam','f4'),
                                ('myelin_thickness','f4'),
                                ('axonmyelin_area','f4'),
                                ('solidity','f4'),
                                ('eccentricity','f4'),
                                ('orientation','f4')
                            ]
                    )
    
    # Compute statistics
    stats_array = get_axon_morphometrics(im_axon=pred_axon, im_myelin=pred_myelin, pixel_size=psm)

    for stats in stats_array:

        x = np.append(x,
            np.array(
                [(
                stats['x0'],
                stats['y0'],
                stats['gratio'],
                stats['axon_area'],
                stats['myelin_area'],
                stats['axon_diam'],
                stats['myelin_thickness'],
                stats['axonmyelin_area'],
                stats['solidity'],
                stats['eccentricity'],
                stats['orientation']
                )],
                dtype=x.dtype)
            )



    # save the current contents in the file
    if not (filename.lower().endswith((".xlsx", ".csv"))):  # If the user didn't add the extension, add it here
        filename = filename + ".xlsx"
    try:
        # Export to excel
        pd.DataFrame(x).to_excel(filename)

    except IOError:
        print("Cannot save morphometrics  data in file '%s'." % file)



