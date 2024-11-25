import json
import os
from datetime import datetime

import yt_dlp

# Load config
config_file_path = 'config/config.json'
with open(config_file_path, 'r') as config_file:
    config = json.load(config_file)



def _get_ydl_opts(
        output_dir=None, 
        subtitle_langs=['en', 'de'],
        download_archive:str=None, 
        rate_limit:int=None,
        max_height:int=None,
        verbose:bool=False) -> dict:
    """
    Generates yt-dlp download preferences

    Parameters
    ----------
    output_dir: str
        Directory in which to put the downloaded files
    subtitle_langs: list[str]
        List of languages to download subtitles for
    download_archive: str
        File containing IDs of already downloaded files
    rate_limit: int
        Limit download speed in MB, default in config
    max_heigh: int
        Max Video Height in Pixels, defautt in config
    verbose: bool
        If set to false, yt-dlp will not print to console

    Returns
    -------
    dict:
        Dictionary of download preferences
    """
    output = 'YouTube ## %(uploader)s ## %(upload_date)s ## %(title)s ## %(id)s.%(ext)s'
    if output_dir is not None:
        output = os.path.join(output_dir, output)
    
    if rate_limit is None:
        rate_limit = config['download_rate_limit_in_mb']
    rate_limit = rate_limit * 1000000

    if max_height is None:
        max_height = config['download_max_video_height']

    # Define options based on your requirements
    ydl_opts = {
        # Custom format selection with prioritized fallbacks
        'format': ('('
            f'bestvideo[height<={max_height}][vcodec~=av01]/'
            f'bestvideo[height<={max_height}][vcodec~=vp09]/'
            f'bestvideo[height<={max_height}]) + ('
            f'bestaudio[acodec~=mp4a]/'
            f'bestaudio)'
        ),

        'merge_output_format': 'mkv',                   # Merge output to MKV format
        'windowsfilenames': True,                       # Use Windows-compatible filenames
        'outtmpl': output,                              # Filename format
 
        'ratelimit': rate_limit,                        # Limits download speed
        'quiet': (not verbose),

        # Download and save metadata and subtitles
        'writeinfojson': True,                          # Write metadata to .info.json file
        'writethumbnail': True,                         # Download thumbnail
        'writesubtitles': True,                         # Download subtitles
        'writeautomaticsub': True,                      # Download auto-generated subtitles
        'subtitleslangs': subtitle_langs,               # Limit subtitles to English and German
        'subtitlesformat': 'vtt/best',                  # Prefer VTT subtitle format

        # Postprocessors to handle embedding options
        'postprocessors': [
            {
                'key': 'FFmpegMetadata',                # Embed metadata
            },
            {
                'key': 'EmbedThumbnail',                # Embed thumbnail into the file
                'already_have_thumbnail': False
            }
        ]
    }

    if download_archive is not None:
        ydl_opts['download_archive'] = download_archive # Add downloaded video ids to archive file
        ydl_opts['break_on_existing'] = True            # Don't download videos with archived ids

    return ydl_opts



def _download_video_by_url(url:str, ydl_opts: dict) -> bool:
    """
    Downloads video using yt-dlp.

    Parameters
    ----------
    url: str
        URL of the video to download
    ydl_opts: dict
        Contains all download preferences

    Returns
    -------
    0: If download was successful
    1: If error occured during download
    """
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        return ydl.download([url])



def get_video_urls_from_url(url:str) -> tuple[list[str], dict[str:str]]:
    """
    Get a list of Video URLs from a Playlist or Channel

    Parameters
    ----------
    url: str
        URL of a playlist or channel

    Returns
    -------
    video_urls: list[str]
        List of video urls 
    url_info: dict[str:str]
        Information about the url provided: id, channel, title
    """
    # Initialize the yt-dlp options
    ydl_opts = {
        'quiet': True,  # Suppress unnecessary output
        'extract_flat': True,  # Get URLs of videos without downloading
    }
    
    # Create a list to store the URLs
    video_urls = []
    url_info = {}

    # Use yt-dlp to extract information
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        # Extract video information from the provided URL (playlist or channel)
        result = ydl.extract_info(url, download=False)  # Don't download, just extract

        if 'entries' in result:
            # 'entries' contains the list of videos in the playlist or channel
            for entry in result['entries']:
                video_urls.append(entry['url'])  # Add the video URL to the list
        
        url_info['id'] = result['id']
        url_info['title'] = result['title']
        url_info['channel'] = result['channel']

    return (video_urls, url_info)


def download_additional_content(
        url:str,
        output_dir:str=None, 
        subtitle_langs:list[str]=None
    ) -> bool:
    """
    Downloaded an updated info.json as well as additional subtitle files for
    a previously completed download.

    Parameters
    ----------
    url: str
        URL of a playlist or channel
    output_dir: str
        Target directory for downloaded files
    subtitle_langs: list[str]
        List of languages to download subtitles in

    Returns
    -------
    0: If download was successful
    1: If error occured during download
    """
    output = 'YouTube ## %(uploader)s ## %(upload_date)s ## %(title)s ## %(id)s.%(ext)s'
    if output_dir is not None:
        output = os.path.join(output_dir, output)

    ydl_opts = {
        'writeinfojson': True,                          # Write metadata info to a .info.json file
        'outtmpl': output,                              # Output template for naming files
        'skip_download': True,                          # Do not download the actual video
    }

    if subtitle_langs is not None and subtitle_opts != []:
        subtitle_opts = {
            'writesubtitles': True,                         # Download subtitles
            'writeautomaticsub': True,                      # Download auto-generated subtitles
            'subtitleslangs': subtitle_langs,               # Specify subtitle languages
            'subtitlesformat': 'vtt/best',                  # Subtitle file format
        }
        ydl_opts.update(subtitle_opts)

    return _download_video_by_url(url, ydl_opts)

def download(
        url:str, 
        override_rate_limit:int=None, 
        override_max_height:int=None,
        verbose:bool=False) -> bool:
    """
    Main download function. Generates download preferences 
    from config and downloads video using yt-dlp.

    Parameters
    ----------
    url: str 
        URL of the video to download
    override_rate_limit: int
        Override for the config value of the download rate limit in MB 
    override_max_height: int
        Override for the config value of the max video height in pixels
    verbose: bool
        If set to false, yt-dlp will not print to console

    Returns
    -------
    0: int
        If download was successful
    1: int
        If error occured during download
    """
    # Config value for download directory
    active_download_directory = os.path.join(
        config["download_directory_main"],
        config["download_directory_in_progress"],
        config["download_directory_in_progress_active"])
    
    # Config value for download_archive file
    download_archive_file = os.path.join(
        config["download_directory_main"],
        config["download_directory_data"],
        config["download_archive_file"])
    
    if override_rate_limit is not None:
        download_rate_limit = override_rate_limit
    else:
        download_rate_limit = config["download_rate_limit_in_mb"]

    if override_max_height is not None:
        max_video_height = override_max_height
    else:
        max_video_height = config["download_max_video_height"]

    ydl_opts = _get_ydl_opts(
        active_download_directory,
        config["subtitle_languages"],
        download_archive_file,
        download_rate_limit,
        max_video_height
    )

    return _download_video_by_url(url, ydl_opts)



if __name__ == '__main__':
    pass
