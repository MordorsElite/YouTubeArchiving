import yt_dlp
import os
import json
from datetime import datetime

# Load config
config_file_path = 'config/config.json'
with open(config_file_path, 'r') as config_file:
    config = json.load(config_file)



def _get_ydl_opts(
        output_dir=None, 
        subtitle_langs=['en', 'de'],
        download_archive:str=None, 
        rate_limit:int=1000,
        max_height:int=1080
        ) -> dict:
    """
    Generates yt-dlp download preferences

    @param output_dir: Directory in which to put the downloaded files (str)
    @param subtitle_langs: List of languages to download subtitles for (list[str])
    @param rate_limit: Limit download speed in MB (int)
    @param max_heigh: Max Video Height in Pixels (int)
    @param download_archive: File containing IDs of already downloaded files (str)

    @return: Dictionary of download preferences
    """
    output = 'YouTube ## %(uploader)s ## %(upload_date)s ## %(title)s ## %(id)s.%(ext)s'
    if output_dir is not None:
        output = os.path.join(output_dir, output)
    rate_limit = rate_limit * 1000000

    # Define options based on your requirements
    ydl_opts = {
        # Custom format selection with prioritized fallbacks
        'format': (
            f'bestvideo[height<={max_height}][vcodec~=avc1]+bestaudio[acodec~=mp4a]/'
            f'bestvideo[height<={max_height}][vcodec!~=avc1]+bestaudio[acodec~=mp4a]/'
            f'bestvideo[height<={max_height}]+bestaudio[acodec~=mp4a]/'
            f'bestvideo[height<={max_height}]+bestaudio/'
            f'best'
        ),

        'merge_output_format': 'mkv',                           # Merge output to MKV format
        'windowsfilenames': True,                               # Use Windows-compatible filenames
        'outtmpl': output,                                      # Filename format
 
        'ratelimit': rate_limit,                                # Limits download speed

        # Download and save metadata and subtitles
        'writeinfojson': True,                                  # Write metadata to .info.json file
        'writethumbnail': True,                                 # Download thumbnail
        'writesubtitles': True,                                 # Download subtitles
        'writeautomaticsub': True,                              # Download auto-generated subtitles
        'subtitleslangs': subtitle_langs,                       # Limit subtitles to English and German
        
        # Postprocessors to handle embedding options
        'postprocessors': [
            {
                'key': 'EmbedThumbnail',                        # Embed thumbnail into the file
                'already_have_thumbnail': False
            }
        ]
    }

    if download_archive is not None:
        ydl_opts['download_archive'] = download_archive         # Add downloaded video ids to archive file
        ydl_opts['break_on_existing'] = True                    # Don't download videos with archived ids

    return ydl_opts



def _download_video_by_url(url:str, ydl_opts: dict) -> bool:
    """
    Downloads video using yt-dlp.

    @param url: URL of the video to download (string)
    @param ydl_opts: Contains all download preferences (dict)

    @return success: Was the download successful (bool)
    """
    success = False
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        success = ydl.download([url])
    return success



def get_video_urls_from_url(url:str) -> list[str]:
    """
    Get a list of Video URLs from a Playlist or Channel

    @param url: URL of a playlist or channel (str)

    @Return video_urls: List of video urls (list[str])
    """
    # Initialize the yt-dlp options
    ydl_opts = {
        'quiet': True,  # Suppress unnecessary output
        'extract_flat': True,  # Get URLs of videos without downloading
    }
    
    # Create a list to store the URLs
    video_urls = []

    # Use yt-dlp to extract information
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        # Extract video information from the provided URL (playlist or channel)
        result = ydl.extract_info(url, download=False)  # Don't download, just extract

        if 'entries' in result:
            # 'entries' contains the list of videos in the playlist or channel
            for entry in result['entries']:
                video_urls.append(entry['url'])  # Add the video URL to the list
    
    return video_urls



def download(
        url:str, 
        override_rate_limit:int=None, 
        override_max_height:int=None) -> bool:
    """
    Main download function. Generates download preferences 
    from config and downloads video using yt-dlp.

    @param url: URL of the video to download (string)
    @param override_rate_limit: Override for the config
        value of the download rate limit in MB (int)
    @param override_max_height: Override for the config
        value of the max video height in pixels (int)

    @Return Returns true if download was successful (bool)
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
        max_video_height = config["download_rate_limit_in_mb"]

    ydl_opts = _get_ydl_opts(
        active_download_directory,
        config["subtitle_languages"],
        download_archive_file,
        download_rate_limit,
        max_video_height
    )

    return _download_video_by_url(url, ydl_opts)



if __name__ == '__main__':
    url = 'https://www.youtube.com/watch?v=wXcS9oD1_i8'
    download(url)
