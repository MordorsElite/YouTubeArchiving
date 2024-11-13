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
        rate_limit=1000,
        max_height=1080,
        download_archive=None
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

        'download_archive': download_archive,                   # Add downloaded video ids to archive file
        'break_on_existing': True,                              # Don't download videos with archived ids
        
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



def download(url:str) -> bool:
    """
    Main download function. Generates download preferences 
    from config and downloads video using yt-dlp.

    @param url: URL of the video to download (string)

    @return success: Was the download successful (bool)
    """
    active_download_directory = os.path.join(
        config["download_directory_main"],
        config["download_directory_in_progress"],
        config["download_directory_in_progress_active"]
    )

    ydl_opts = _get_ydl_opts(
        config["temp_file_directory"],
        config["subtitle_languages"],
        config["download_rate_limit_in_mb"])

    return _download_video_by_url(url, ydl_opts)



if __name__ == '__main__':
    url = 'https://www.youtube.com/watch?v=wXcS9oD1_i8'
    download(url)
