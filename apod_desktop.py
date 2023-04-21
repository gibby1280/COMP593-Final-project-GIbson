""" 
COMP 593 - Final Project

Description: 
  Downloads NASA's Astronomy Picture of the Day (APOD) from a specified date
  and sets it as the desktop background image.

Usage:
  python apod_desktop.py [apod_date]

Parameters:
  apod_date = APOD date (format: YYYY-MM-DD)
"""
from datetime import date
import os
import image_lib
import inspect
import sys 
from datetime import datetime 
import sqlite3
from apod_api import get_apod_image_url
import apod_api
import re 
import hashlib
# Global variables
image_cache_dir = None  # Full path of image cache directory
image_cache_db = None   # Full path of image cache database

def main():
    ## DO NOT CHANGE THIS FUNCTION ##
    # Get the APOD date from the command line
    apod_date = get_apod_date()    

    # Get the path of the directory in which this script resides
    script_dir = get_script_dir()

    # Initialize the image cache
    init_apod_cache(script_dir)

    # Add the APOD for the specified date to the cache
    apod_id = add_apod_to_cache(apod_date)

    # Get the information for the APOD from the DB
    apod_info = get_apod_info(apod_id)

    # Set the APOD as the desktop background image
    if apod_id != 0:
        image_lib.set_desktop_background_image(apod_info['file_path'])

def get_apod_date():
    """Gets the APOD date
     
    The APOD date is taken from the first command line parameter.
    Validates that the command line parameter specifies a valid APOD date.
    Prints an error message and exits script if the date is invalid.
    Uses today's date if no date is provided on the command line.

    Returns:
        date: APOD date
    """
    # Sets the lowest date that the command line will accept 
    lowest_date = date(1995,6,16)

    if len(sys.argv) > 1:
        try:
            apod_date = date.fromisoformat(sys.argv[1])
        
        except ValueError:
          
            print(f'The date {sys.argv[1]} is invaild. Please make sure you use the correct date format: YYYY-MM-DD')
            sys.exit(1)
    else:
            apod_date = date.today()
            
            # If the date entered is further in the past then 1995-06-16, the script spits an error out.
            if apod_date < lowest_date:
                print(f'The date {apod_date.isoformat()} is to far in the past!')
                sys.exit(1)

            # If the date entered is in the future, the script spits an error out.
            if apod_date > date.today():
                print(f'The date {apod_date.isoformat()} is in the future!')
                sys.exit(1)

    return apod_date

def get_script_dir():
    """Determines the path of the directory in which this script resides

    Returns:
        str: Full path of the directory in which this script resides
    """
    ## DO NOT CHANGE THIS FUNCTION ##
    script_path = os.path.abspath(inspect.getframeinfo(inspect.currentframe()).filename)
    return os.path.dirname(script_path)

def init_apod_cache(parent_dir):
    """Initializes the image cache by:
    - Determining the paths of the image cache directory and database,
    - Creating the image cache directory if it does not already exist,
    - Creating the image cache database if it does not already exist.
    
    The image cache directory is a subdirectory of the specified parent directory.
    The image cache database is a sqlite database located in the image cache directory.

    Args:
        parent_dir (str): Full path of parent directory    
    """
    global image_cache_dir
    global image_cache_db
    # Determine the path of the image cache directory
    image_cache_dir = os.path.join(parent_dir, 'image_cache')

    # Create the image cache directory if it does not already exist
    if not os.path.exists(image_cache_dir):
        os.makedirs(image_cache_dir)
        print(f'Image cache dir: {image_cache_dir}')
        print('directory created.')
    else:
        print (f'Image cache dir: {image_cache_dir}')
        print('directory already created')
   
    # Determine the path of image cache DB
    image_cache_db = os.path.join(image_cache_dir, 'image_cache.db')

    # Creates the image_apod database exactly as outlined. 
    con = sqlite3.connect(image_cache_db)
    cur = con.cursor()
    APOD_query = """
        CREATE TABLE IF NOT EXISTS image_apod
        (
        id INTEGER PRIMARY KEY,
        title TEXT NOT NULL,
        explanation TEXT NOT NULL,
        file_path TEXT NOT NULL,
        sha256 TEXT NOT NULL
        );
        """
    # Run the APOD_query then commit it to the database and close the database connection. 
    cur.execute(APOD_query)
    con.commit()
    con.close()

def add_apod_to_cache(apod_date):
    """Adds the APOD image from a specified date to the image cache.
     
    The APOD information and image file is downloaded from the NASA API.
    If the APOD is not already in the DB, the image file is saved to the 
    image cache and the APOD information is added to the image cache DB.

    Args:
        apod_date (date): Date of the APOD image

    Returns:
        int: Record ID of the APOD in the image cache DB, if a new APOD is added to the
        cache successfully or if the APOD already exists in the cache. Zero, if unsuccessful.
    """
    print("APOD date:", apod_date.isoformat())
    apod_info = apod_api.get_apod_info(apod_date)

    image_exp = apod_info['explanation']
    image_title = apod_info['title']
    print(f'Image title: {image_title}')

    apod_url = get_apod_image_url(apod_info)
    print(f'Image URL: {apod_url}')

    image_download = image_lib.download_image(apod_url)

    sha_hash = hashlib.sha256(image_download).hexdigest()
    print(f'SHA-256: {sha_hash}')

    path_for_apod = determine_apod_file_path(image_title, apod_url)

    apod_id = add_apod_to_db(image_title, image_exp, path_for_apod, sha_hash)

    image = get_apod_id_from_db(sha_hash)

    image_saved = image_lib.save_image_file(image_download, path_for_apod)

    if image == 0:
        print(f'The APOD file path is: {path_for_apod}')
        return image_saved, apod_id
   
    if not image == 0:
        print('That image is already in the cache.')
        return image
    else:
        return 0

    
def add_apod_to_db(title, explanation, file_path, sha256):
    """Adds specified APOD information to the image cache DB.
     
    Args:
        title (str): Title of the APOD image
        explanation (str): Explanation of the APOD image
        file_path (str): Full path of the APOD image file
        sha256 (str): SHA-256 hash value of APOD image

    Returns:
        int: The ID of the newly inserted APOD record, if successful.  Zero, if unsuccessful       
    """
    # Connects to the image_cache database 
    con = sqlite3.connect(image_cache_db)
    cur = con.cursor()

    # Adds the title explanation file path and sha256 into the image_apod table 
    apod_query = """
        INSERT INTO image_apod
        (
        title,
        explanation,
        file_path,
        sha256
        )
        VALUES (?,?,?,?);
        """
    query_image = (title, explanation, file_path, sha256)

    id = get_apod_id_from_db(sha256)
    if not id == 0 :
        return id 
    
    # Commits the values from above into the database 
    cur.execute(apod_query, query_image)
    con.commit()
    con.close()
    
def get_apod_id_from_db(image_sha256):
    """Gets the record ID of the APOD in the cache having a specified SHA-256 hash value
    
    This function can be used to determine whether a specific image exists in the cache.

    Args:
        image_sha256 (str): SHA-256 hash value of APOD image

    Returns:
        int: Record ID of the APOD in the image cache DB, if it exists. Zero, if it does not.
    """
    con = sqlite3.connect(image_cache_db)
    cur = con.cursor()
    info_query = """
        SELECT id FROM image_apod
        WHERE sha256 = ?
        """
    cur.execute(info_query, (image_sha256,))
    info_q = cur.fetchone()
    if info_q == None:
        return 0
    if not info_q == None:
        return info_q[0]
    con.commit()
    con.close()

def determine_apod_file_path(image_title, image_url):
    """Determines the path at which a newly downloaded APOD image must be 
    saved in the image cache. 
    
    The image file name is constructed as follows:
    - The file extension is taken from the image URL
    - The file name is taken from the image title, where:
        - Leading and trailing spaces are removed
        - Inner spaces are replaced with underscores
        - Characters other than letters, numbers, and underscores are removed

    For example, suppose:
    - The image cache directory path is 'C:\\temp\\APOD'
    - The image URL is 'https://apod.nasa.gov/apod/image/2205/NGC3521LRGBHaAPOD-20.jpg'
    - The image title is ' NGC #3521: Galaxy in a Bubble '

    The image path will be 'C:\\temp\\APOD\\NGC_3521_Galaxy_in_a_Bubble.jpg'

    Args:
        image_title (str): APOD title
        image_url (str): APOD image URL
    
    Returns:
        str: Full path at which the APOD image file must be saved in the image cache directory
    """
    image_title = image_title.strip().replace('', '_')
    image_title = re.sub('[A-Za-z0-9_]+', '', image_title)

    file_exe = image_url.split('.')[-1]

    full_title = f'{image_title} {file_exe}'

    complete_path = os.path.join(image_cache_dir, full_title)
    
    return complete_path

def get_apod_info(image_id):
    """Gets the title, explanation, and full path of the APOD having a specified
    ID from the DB.

    Args:
        image_id (int): ID of APOD in the DB

    Returns:
        dict: Dictionary of APOD information
    """
    con = sqlite3.connect(image_cache_db)
    cur = con.cursor()

    sel_query = """
        SELECT title, explanation, file_path FROM image_apod
        WHERE id = ?
    """

    cur.execute(sel_query, (image_id,))
    queury_result = cur.fetchone()

    con.commit()
    con.close()

    apod_info = {
        'title': queury_result[0], 
        'explanation':queury_result[1] ,
        'file_path': queury_result[2],
    }

    if queury_result != 0:
        return apod_info
    else:
        return None
    
def get_all_apod_titles():
    """Gets a list of the titles of all APODs in the image cache

    Returns:
        list: Titles of all images in the cache
    """
    # TODO: Complete function body
    # NOTE: This function is only needed to support the APOD viewer GUI
    return

if __name__ == '__main__':
    main()