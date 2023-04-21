'''
Library for interacting with NASA's Astronomy Picture of the Day API.
'''
import requests
from datetime import date 

# Sets the api key and the url of the api itself.
NASA_API_KEY = '8dczCmVwdmzq9UCgOZAS6SAP6UK7sTh3x4TdP94o'
NASA_APOD_URL = 'https://api.nasa.gov/planetary/apod'

def main():
    apod_info = get_apod_info('2004-08-08')
    print(apod_info)
    image_url = get_apod_image_url(apod_info)
    print('Image URL:', image_url)

    return None 
    
   
def get_apod_info(apod_date):
    """Gets information from the NASA API for the Astronomy 
    Picture of the Day (APOD) from a specified date.

    Args:
        apod_date (date): APOD date (Can also be a string formatted as YYYY-MM-DD)

    Returns:
        dict: Dictionary of APOD info, if successful. None if unsuccessful
    """
    
    # Uses the requests pacakge to get information about the API.
    get_params = {
       
        'api_key' : NASA_API_KEY,
        'date' : apod_date
    }
    
    resp_msg = requests.get(NASA_APOD_URL, params= get_params)

    # Checks to make sure the request was succesful. 
    if resp_msg.status_code == 200:
        print('Request successful!')
       
        return resp_msg.json()
    else:
        print('Request failed')
        
        return None


def get_apod_image_url(apod_info_dict):
    """Gets the URL of the APOD image from the dictionary of APOD information.

    If the APOD is an image, gets the URL of the high definition image.
    If the APOD is a video, gets the URL of the video thumbnail.

    Args:
        apod_info_dict (dict): Dictionary of APOD info from API

    Returns:
        str: APOD image URL
    """
    # Checks the media type and acts based on if the the media is an image or video.
    media_type = apod_info_dict['media_type']
    
    if media_type == 'image':
        # If the apod is an image, return the url of the high defintion image.
        return apod_info_dict['hdurl']
    
    elif media_type == 'video':
        # If the apod is a video, return the url of the video thumbnail.
        return apod_info_dict['url']

    else:  # If the media type entered is not either a video or image, give an error.
        raise ValueError('The media you have entered is invaild.')

if __name__ == '__main__':
    main()