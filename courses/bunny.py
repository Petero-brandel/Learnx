import requests
import os
from django.conf import settings

BUNNY_API_KEY = os.environ.get('BUNNY_API_KEY')
LIBRARY_ID = os.environ.get('BUNNY_LIBRARY_ID')
PULL_ZONE = os.environ.get('BUNNY_PULL_ZONE')

def create_video_object(title):
    """
    Creates a video object in Bunny Stream and returns the GUID.
    The frontend will use this GUID to directly upload the video file via TUS.
    """
    url = f"https://video.bunnycdn.com/library/{LIBRARY_ID}/videos"
    
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "AccessKey": BUNNY_API_KEY
    }
    
    payload = {"title": title}
    
    response = requests.post(url, json=payload, headers=headers)
    
    if response.status_code == 200:
        return response.json().get('guid')
    return None

def get_playback_url(guid):
    """
    Returns the secure iframe URL for the video.
    In the future, we can add token authentication here for DRM.
    """
    return f"https://iframe.mediadelivery.net/embed/{LIBRARY_ID}/{guid}"
