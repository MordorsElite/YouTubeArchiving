import yt_dlp
import os
import json
from datetime import datetime

# Load config
config_file_path = 'config/config.json'
with open(config_file_path, 'r') as config_file:
    config = json.load(config_file)



def get_ydl_opts(output_dir=None, subtitle_langs=['en', 'de'], rate_limit_in_mb=1000) -> dict:
    """
    Generates yt-dlp download preferences

    @param output_dir: Directory in which to put the downloaded files
    @param subtitle_langs: List of languages to download subtitles for
    @param rate_limit_in_mb: Limit download speed in MB

    @return: Dictionary of download preferences
    """
    output = 'YouTube ## %(uploader)s ## %(upload_date)s ## %(title)s ## %(id)s.%(ext)s'
    if output_dir is not None:
        output = os.path.join(output_dir, output)
    rate_limit = rate_limit_in_mb * 1000000

    # Define options based on your requirements
    ydl_opts = {
        # Custom format selection with prioritized fallbacks
        'format': (
            'bestvideo[height<=1080][vcodec~=avc1]+bestaudio[acodec~=mp4a]/'
            'bestvideo[height<=1080][vcodec!~=avc1]+bestaudio[acodec~=mp4a]/'
            'bestvideo[height<=1080]+bestaudio[acodec~=mp4a]/'
            'bestvideo[height<=1080]+bestaudio/'
            'best'
        ),

        'merge_output_format': 'mkv',                          # Merge output to MKV format
        'windowsfilenames': True,                              # Use Windows-compatible filenames
        'outtmpl': output,                                     # Filename format

        'ratelimit': rate_limit,                               # Limits download speed
        
        # Download and save metadata and subtitles
        'writeinfojson': True,                                 # Write metadata to .info.json file
        'writethumbnail': True,                                # Download thumbnail
        'writesubtitles': True,                                # Download subtitles
        'writeautomaticsub': True,                             # Download auto-generated subtitles
        'subtitleslangs': subtitle_langs,                      # Limit subtitles to English and German
        
        # Postprocessors to handle embedding options
        'postprocessors': [
            {
                'key': 'FFmpegMetadata',  # Embeds metadata tags
                'add_metadata': {
                    'title': '%(title)s',
                    'artist': '%(uploader)s',
                    'date': '%(upload_date)s',
                    'comment': f'Downloaded on {datetime.now().strftime("%Y-%m-%d")}',
                    'video-id': '%(id)s',
                    'uploader': '%(uploader)s',
                    'upload_date': '%(upload_date)s',
                    'download_date': datetime.now().strftime("%Y-%m-%d")
                }
            },
            {
                'key': 'EmbedThumbnail',                      # Embed thumbnail into the file
                'already_have_thumbnail': False
            }
        ]
    }

    return ydl_opts



def download_video_by_url(url:str, ydl_opts: dict) -> None:
    """
    Downloads video using yt-dlp.

    @param url: URL of the video to download (string)
    @param ydl_opts: Contains all download preferences (dict)

    @return
    """
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])



def download(url:str) -> None:
    """
    Main download function. Generates download preferences 
    from config and downloads video using yt-dlp.

    @param url: URL of the video to download (string)
    """
    ydl_opts = get_ydl_opts(
        config["temp_file_directory"],
        config["subtitle_languages"],
        config["download_rate_limit_in_mb"])

    download_video_by_url(url, ydl_opts)



if __name__ == '__main__':
    url = 'https://www.youtube.com/watch?v=wXcS9oD1_i8'
    download(url)
