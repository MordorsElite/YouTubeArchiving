import argparse
import json
import logging
import os
import re
import shutil
import sys
from datetime import datetime

import yt_dlp

import database
import downloader
import subtitles_embedding

# Load config
config_file_path = 'config/config.json'
with open(config_file_path, 'r') as config_file:
    config = json.load(config_file)



def _check_file_structure() -> None:
    """
    Ensures that the folder structure exists 
    as specified in the config.
    """
    # Check main directory
    if not os.path.exists(config["download_directory_main"]):
        os.mkdir(config["download_directory_main"])

    # Check in_progress directory
    download_directory_in_progress = os.path.join(
        config["download_directory_main"],
        config["download_directory_in_progress"])
    if not os.path.exists(download_directory_in_progress):
        os.mkdir(download_directory_in_progress)
    # Check in_progress subdirectories
    download_directory_in_progress_active = os.path.join(
        config["download_directory_main"],
        config["download_directory_in_progress"],
        config["download_directory_in_progress_active"])
    download_directory_in_progress_paused = os.path.join(
        config["download_directory_main"],
        config["download_directory_in_progress"],
        config["download_directory_in_progress_paused"])
    download_directory_in_progress_failed = os.path.join(
        config["download_directory_main"],
        config["download_directory_in_progress"],
        config["download_directory_in_progress_failed"])
    if not os.path.exists(download_directory_in_progress_active):
        os.mkdir(download_directory_in_progress_active)
    if not os.path.exists(download_directory_in_progress_paused):
        os.mkdir(download_directory_in_progress_paused)
    if not os.path.exists(download_directory_in_progress_failed):
        os.mkdir(download_directory_in_progress_failed)

    # Check directories for finished downloads
    download_directory_videos = os.path.join(
        config["download_directory_main"],
        config["download_directory_videos"])
    if not os.path.exists(download_directory_videos):
        os.mkdir(download_directory_videos)

    download_directory_subtitles = os.path.join(
        config["download_directory_main"],
        config["download_directory_subtitles"])
    if not os.path.exists(download_directory_subtitles):
        os.mkdir(download_directory_subtitles)

    # Check data directory
    download_directory_data = os.path.join(
        config["download_directory_main"],
        config["download_directory_data"])
    if not os.path.exists(download_directory_data):
        os.mkdir(download_directory_data)
    # Check data subdirectories
    download_directory_data_info_json = os.path.join(
        config["download_directory_main"],
        config["download_directory_data"],
        config["download_directory_data_info_json"])
    download_directory_data_logs = os.path.join(
        config["download_directory_main"],
        config["download_directory_data"],
        config["download_directory_data_logs"])
    if not os.path.exists(download_directory_data_info_json):
        os.mkdir(download_directory_data_info_json)
    if not os.path.exists(download_directory_data_logs):
        os.mkdir(download_directory_data_logs)

    # Check for relevant information files
    download_archive_file = os.path.join(
        config["download_directory_main"],
        config["download_directory_data"],
        config["download_archive_file"])
    download_failed_list = os.path.join(
        config["download_directory_main"],
        config["download_directory_data"],
        config["download_failed_list"])
    download_to_process_list = os.path.join(
        config["download_directory_main"],
        config["download_directory_data"],
        config["download_to_process_list"])
    if not os.path.exists(download_archive_file):
        with open(download_archive_file, 'w'):
            pass
    if not os.path.exists(download_failed_list):
        with open(download_failed_list, 'w'):
            pass
    if not os.path.exists(download_to_process_list):
        with open(download_to_process_list, 'w'):
            pass



def _setup_logger(print_to_console:bool=False) -> logging.Logger:
    """
    Create log-file and logger

    Parameters
    ----------
    print_to_console: bool
        If enabled, logs will both be written to the log
        file and printed into console

    Returns
    -------
    logging.Logger:
        Logger that allows logging to log file
    """
    # Create a timestamp for the filename
    timestamp = datetime.now().strftime("%Y.%m.%d_%H.%M.%S")
    log_filename = f"youtube_archiving_log_{timestamp}.txt"

    # Define log-file path
    log_file = os.path.join(
        config["download_directory_main"],
        config["download_directory_data"],
        config["download_directory_data_logs"],
        log_filename
    )

    # Define log-file handlers
    handlers = [logging.FileHandler(log_file)]      # Log to file
    if print_to_console:
        handlers.append(logging.StreamHandler())    # Optional: Log to console
    
    
    # Set up logging configuration
    logging.basicConfig(
        level=logging.DEBUG,                        # Log level can be changed as needed
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=handlers
    )
    
    # Create a logger object for other modules to use
    logger = logging.getLogger(__name__)
    logger.info(f'Logging started on {timestamp}')
    return logger



def _parse_arguments() -> argparse.ArgumentParser:
    """
    Parse commandline arguments for use in the script

    Returns
    -------
    argparse.ArgumentParser:
        Parsed commandline arguments. 
        Values are accessible using for example args.url
    """
    parser = argparse.ArgumentParser(description="Youtube Archiving")

    # Define arguments for downloading manually specified URL
    parser.add_argument(
        "--url", type=str, required=False, 
        help="URL to download"
    )

    parser.add_argument(
        "--playlist", action="store_true", required=False,
        help="FLAG: Download playlist at given URL"
    )
    parser.add_argument(
        "--channel", action="store_true", required=False,
        help="FLAG: Download channel at given URL"
    )

    # Define argument for downloading URLs from file
    parser.add_argument(
        "--file", type=str, required=False, 
        help="Text file containing URLs to download (one URL per line)"
    )

    # Define argument for specifying the video source
    parser.add_argument(
        "--video-source", type=str, required=False, 
        help="Manually specify the source for the given video. " +
             "Mainly useful when providing URLs via a file"
    )

    # Define arguments for overriding the config
    parser.add_argument(
        "--rate-limit", type=int, required=False, 
        help="Override the max download rate specified in the config (in MB)"
    )
    parser.add_argument(
        "--max-height", type=int, required=False, 
        help="Override the max video height specified in the config (in Pixels)"
    )

    paused_dir = config['download_directory_in_progress_paused']
    parser.add_argument(
        "--postpone-post-processing", action='store_true', required=False,
        help=f'Disables new subtitle generation etc. '+\
             f'Video will be moved to {paused_dir} instead of final directory'
    )

    parser.add_argument(
        "--verbose", action="store_true", required=False,
        help="FLAG: Makes the script print additional information to console"
    )

    # Parse and return arguments
    return parser.parse_args()



def _print_error(message:str) -> None:
    """
    Print error message to console in color red

    Parameters
    ----------
        message: str
        Error message
    """
    # ANSI escape code for red text
    RED = '\033[91m'
    RESET = '\033[0m'
    print(f'{RED}[ERROR] {message}{RESET}')

def _print_error_and_exit(
        message:str, 
        logger:logging.Logger) -> int:
    """
    Prints error to log-file and console, then returns 1

    Parameters
    ----------
    message: str
        Error message
    logger: logging.Logger
        For access to log file

    Returns
    -------
    1: int
        Error code "1"
    """
    logger.error(message)
    logger.error('Exiting...')
    _print_error(message)
    _print_error('Exiting...')
    return 1



def _move_files(
        source_directory:str,
        destination_directory:str) -> None:
    """
    Move all files from source directory into destination directory.
    Will raise an error if moving files fails.

    Parameters
    ----------
    source_directory: str
        Path to source directory
    destination_directory: str
        Path to destination directory
    """
    files_to_move = os.listdir(source_directory)
    for file in files_to_move:
        src = os.path.join(source_directory, file)
        dst = os.path.join(destination_directory, file)
        shutil.move(src, dst)



def _move_active_to_failed(
        download_number:int,
        logger:logging.Logger) -> None:
    """
    Move files from active download directory into directory for
    failed downloads

    Parameters
    ----------
    download_number: int
        Index of the download URL in the list of downloaded URLs
        for logging purposes
    logger: logging.Logger
        Where to log the info/error messages for file movement
    """
    failed_dir = config['download_directory_in_progress_failed']
    logger.info(f'Moving failed download {download_number+1}\'s '
                f'files to {failed_dir}')
    
    download_directory_in_progress_active = os.path.join(
        config["download_directory_main"],
        config["download_directory_in_progress"],
        config["download_directory_in_progress_active"])
    download_directory_in_progress_failed = os.path.join(
        config["download_directory_main"],
        config["download_directory_in_progress"],
        config["download_directory_in_progress_failed"])
    
    try:
        _move_files(
            download_directory_in_progress_active,
            download_directory_in_progress_failed)
    except Exception as err:
        return _print_error_and_exit(
            f'Error while moving files to {failed_dir} '
            f'for download {download_number+1}: {err}',
            logger)
    logger.info(f'Finished moving failed download '
                f'{download_number+1}\'s files to failed files')



def _move_active_to_final(
        download_number:int, 
        logger:logging.Logger) -> None:
    """
    Move files from active download directory into the final
    directories (different depending on file type)

    Parameters
    ----------
    download_number: int
        Index of the download URL in the list of downloaded URLs
        for logging purposes
    logger: logging.Logger
        Where to log the info/error messages for file movement
    """
    logger.info(f'Download {download_number+1}: '
                f'Moving files to final directory!')
        
    download_directory_in_progress_active = os.path.join(
        config["download_directory_main"],
        config["download_directory_in_progress"],
        config["download_directory_in_progress_active"])
    download_directory_videos = os.path.join(
        config["download_directory_main"],
        config["download_directory_videos"])
    download_directory_subtitles = os.path.join(
        config["download_directory_main"],
        config["download_directory_subtitles"])
    download_directory_data_info_json = os.path.join(
        config["download_directory_main"],
        config["download_directory_data"],
        config["download_directory_data_info_json"])
    
    try:
        source_dir = download_directory_in_progress_active
        files_to_move = os.listdir(source_dir)
        for file in files_to_move:
            # Determine files final directory
            target_dir = None
            file_extension = str.split(file, '.')[-1]
            if file_extension in ['mkv', 'mp4', 'webm']:
                target_dir = download_directory_videos
            elif file_extension in ['srt', 'vtt', 'ass']:
                target_dir = download_directory_subtitles
            elif str.endswith(file, '.json'):
                target_dir = download_directory_data_info_json
            # Move file
            src = os.path.join(source_dir, file)
            dst = os.path.join(target_dir, file)
            shutil.move(src, dst)
    except Exception as err:
        return _print_error_and_exit(
            f'Download {download_number+1}: '
            f'Error while moving files to '
            f'final directories: {err}',
            logger)
    logger.info(f'Download {download_number+1}: Finished moving '
                f'files to their final directories.')



def _get_id_from_url(url:str) -> str:
    """
    Returns video id from a url

    Parameters
    ----------
    url:str
        URL to extract ID from

    Returns
    -------
    id:str
        ID of the video at the input URL

    Errors
    ------
    ValueError:
        If ID could not be found in URL
    """
    youtube_url_options = [
        'https://youtu.be/',
        'https://www.youtube.com/watch?v='
    ]
    for option in youtube_url_options:
        if option not in url:
            continue
        url_without_domain = url[len(option):]
        split_url_without_domain = re.split(r'[&?]', url_without_domain)
        return split_url_without_domain[0]
    
    raise ValueError(f'Could not find ID in URL: {url}')



def main():
    """
    The main script of this project.
    Takes the commandline arguments listed in README.md
    """
    # Create environment
    try:
        _check_file_structure()
    except Exception as err:
        _print_error('File structure not correct!')
        _print_error(err)
        _print_error('Exiting...')
        return 1

    # Initialize the logger for this script
    logger = _setup_logger()
    logger.info(f'File structure checked/created successfully.')

    ### Interpret console commands
    video_urls = []
    video_source = None
    url_info = None

    if len(sys.argv) == 1:
        print("No arguments provided. Use --help for assistance.")
        sys.argv.append("--help")
    args = _parse_arguments()
    logger.info('Input parameters:')
    logger.info(args)
    
    # Get video URLs
    if args.file is not None:
        with open(args.file, 'r', 'utf-8') as url_file:
            for url in url_file.readlines():
                video_urls.append(url)
        if video_urls in [None, []]:
            return _print_error_and_exit(logger,
                f'No URLs found in file {args.file}')
    else: 
        if args.url is None:
            return _print_error_and_exit(logger,
                'Neither URL or URL-file provided!')
        
        if args.playlist or args.channel:
            video_urls, url_info = downloader.get_video_urls_from_url(args.url)
            if video_urls in [None, []]:
                return _print_error_and_exit(logger,
                    f'No URLs found for '
                    f'{"playlist" if args.playlist else "channel"}!')
        else:
            video_urls = [args.url]
    
    logger.info(f'Video URLs to download ({len(video_urls)} total):')
    logger.info(video_urls)

    # Determine video source
    if args.video_source is not None:
        video_source = args.video_source
    else:
        if url_info is not None:
            video_source_type = 'Playlist' if args.playlist else 'Channel'
            id = url_info['id']
            title = url_info['title']
            channel = url_info['channel']
            video_source = (
                f'{video_source_type}:'
                f'title={title}&id={id}&channel={channel}')
        else:
            video_source = 'direct'

    verbose = False
    if args.verbose:
        verbose = True

    

    # Loading this here as it's used all over
    download_directory_in_progress_active = os.path.join(
        config["download_directory_main"],
        config["download_directory_in_progress"],
        config["download_directory_in_progress_active"])
    download_directory_in_progress_paused = os.path.join(
        config["download_directory_main"],
        config["download_directory_in_progress"],
        config["download_directory_in_progress_paused"])
    
    ### Loop over all videos to download:
    for i, url in enumerate(video_urls):
        video_file = None
        ### Download video
        logger.info(f'Download {i+1}: {url} with aditional parameters '
                    f'rate_limit={args.rate_limit} '
                    f'and max_height={args.max_height}')
        try:
            ret_code = downloader.download(url, args.rate_limit, args.max_height)
        
        # If video has already been downloaded
        except yt_dlp.utils.ExistingVideoReached as err:
            logger.warning(f'Download {i+1}: ({url}) Video already downloaded!')
            logger.warning(f'Download {i+1}: {err}')
            logger.info(
                f'Download {i+1}: '
                f'Checking for additional content to download')
            # Download additional subtitles if they were not 
            # already downloaded before. Also download a new version 
            # of info.json to compare title and description

            # Compare downloaded subtitle languages
            video_id = _get_id_from_url(url)
            try:
                csv_subtitle_languages = json.loads(
                    database.get_field_value_by_video_id(
                        video_id,
                        'subtitle_languages'))
            except Exception as err:
                logger.error(f'Download {i+1}: '
                             f'Download of additional content failed')
                _move_active_to_failed(i, logger)
                continue
            remaining_langauges = []
            for language in config['subtitle_languages']:
                if language not in csv_subtitle_languages:
                    remaining_langauges.append(language)
            logger.info(f'Download {i+1}: Additional subtitle languages '
                        f'{remaining_langauges} still needed. Downloading...')
            # Download additional languages and new info.json
            ret_code = downloader.download_additional_content(
                url,
                download_directory_in_progress_active,
                remaining_langauges if remaining_langauges != [] else None)
            if ret_code == 0:
                logger.info(f'Download {i+1}: Download of additional '
                            f'content successfull')
                # Rename new info.json by appending current date to name
                new_downloaded_files = \
                    os.listdir(download_directory_in_progress_active)
                for file_name in new_downloaded_files:
                    if str.endswith(file_name, '.json'):
                        new_info_json = os.path.join(
                            download_directory_in_progress_active,
                            file_name)
                        break
                renamed_info_json = (new_info_json[:-5] +
                    ' ## ' +
                    datetime.now().strftime("%Y.%m.%d_%H.%M.%S") +
                    new_info_json[-5:])
                os.rename(new_info_json, renamed_info_json)

                # Collect subtitle files
                subtitle_files = []
                for file_name in new_downloaded_files:
                    file_extension = str.split(file_name, '.')[-1]
                    if file_extension in ['srt', 'vtt', 'ass']:
                        subtitle_files.append(file_name)

                # Update database with new content/info
                logger.info(f'Download {i+1}: Updating database...')
                database.update_database(
                    video_id,
                    video_source,
                    renamed_info_json,
                    subtitle_files)
                logger.info(f'Download {i+1}: Database updated!')
                
                # Move files to final directories
                _move_active_to_final(i, logger)
                continue
            else:
                logger.error(f'Download {i+1}: Error while downloading '
                             f'additional content')
                _move_active_to_failed(i, logger)
                continue

        # Check if download was successful
        if ret_code == 0:
            logger.info(f'Download {i+1}: Finished successfully! ({url})')
            print(f'Download {i+1}: Finished successfully! ({url})')
        else:
            # If download unsucessful
            # Logging
            logger.error(f'Download {i+1}: Unsuccessful! ({url})')
            download_failed_list = os.path.join(
                config["download_directory_main"],
                config["download_directory_data"],
                config["download_failed_list"])
            with open(download_failed_list, 'a') as failed_list_file:
                failed_list_file.write(f'{url}\n')
            logger.info(f'Failed download {i+1}\'s URL added to failed list')

            # Move Files from faild download into the designated directory
            _move_active_to_failed(i, logger)
            continue
            
        ### If Post-processing is set to "postponted", skip rest of the loop
        if args.postpone_post_processing:
            paused_dir = config['download_directory_in_progress_paused']
            logger.info(f'Download {i+1}: ({url}) Post-processing postponed. '
                        f'Moving files to {paused_dir}.')
            try:
                _move_files(
                    download_directory_in_progress_active,
                    download_directory_in_progress_paused)
            except Exception as err:
                return _print_error_and_exit(
                    f'Error while moving files to {paused_dir} '
                    f'for download {i+1}: ({url}) {err}',
                    logger)
            logger.info(f'Download {i+1}: ({url}) '
                        f'Finished moving files to {paused_dir}.')
            download_paused_list = os.path.join(
                config["download_directory_main"],
                config["download_directory_data"],
                config["download_to_process_list"])
            with open(download_paused_list, 'a') as paused_list_file:
                paused_list_file.write(f'{url}\n')
            logger.info(f'Download {i+1}\'s URL added '
                        f'to {download_paused_list}')
            # Skip rest of loop, as it's all post processing
            continue

        
        ### Modify/generate subtitles for downloaded Video

        # Check whether download contained autogenerated, 
        # manual or no subtitles

        # Get info.json
        info_json = None
        for item in os.listdir(download_directory_in_progress_active):
            if str.endswith(item, '.json'):
                info_json = item
                break
        if info_json is None:
            logger.error(f'Download {i+1}: info.json not found!')
            _move_files(
                download_directory_in_progress_active,
                download_directory_in_progress_paused)
            logger.info(
                f'Download {i+1}: Moved files into '
                f'{download_directory_in_progress_paused} '
                f'due to missing video file')
            
            download_paused_list = os.path.join(
                config["download_directory_main"],
                config["download_directory_data"],
                config["download_to_process_list"])
            with open(download_paused_list, 'a') as paused_list_file:
                paused_list_file.write(f'{url}\n')
            logger.info(f'Download {i+1}\'s URL added '
                        f'to {download_paused_list}')
            continue
        
        # Load info.json
        info_json = os.path.join(
            download_directory_in_progress_active,
            info_json)
        with open(info_json, 'r', encoding='utf-8') as info_file:
            info_data = json.load(info_file)

        # Preprocessing for caption analysis
        subtitle_langs = config['subtitle_languages']
        subtitle_langs_covered = list.copy(subtitle_langs)
        next_step_required = True

        # Downloaded video has Manual subtitles
        if info_data['subtitles'] != {}:
            # Check that downloaded video has all required
            # languages as manual subtitles
            for sub_id, sub_info in info_data['subtitles'].items():
                for lang_idx, language in enumerate(subtitle_langs):
                    if str.startswith(sub_id, language):
                        subtitle_langs_covered[lang_idx] = None
                        break
            subtitle_langs_covered = [lang for lang in subtitle_langs_covered 
                                           if lang is not None]
            # All required langauges available as manual captions
            if subtitle_langs_covered == []:
                next_step_required = False
        
        # Downloaded video has Automatic captions and downloaded 
        # video did not have all required languages as manual subtitles
        if next_step_required and info_data['automatic_captions'] != {}:
            # Check that downloaded video has all required/remaining
            # languages as manual subtitles
            auto_captions_found = []
            subtitle_langs = subtitle_langs_covered
            for sub_id, sub_info in info_data['automatic_captions'].items():
                for lang_idx, language in enumerate(subtitle_langs):
                    if sub_id == language:
                        subtitle_langs_covered[lang_idx] = None
                        auto_captions_found.append(language)
                        break
            subtitle_langs_covered = [lang for lang in subtitle_langs_covered 
                                           if lang is not None]
            # All required langauges available as automatic captions
            if subtitle_langs_covered == []:
                next_step_required = False

            file_list = os.listdir(download_directory_in_progress_active)


            # Generate converted captions for automatic captions
            for language in auto_captions_found:
                # Check that subtitle file is actually available for langauge
                subtitle_file = None
                for file in file_list:
                    if str.endswith(file[:-4], language):
                        subtitle_file = file
                        break
                if subtitle_file is None:
                    continue
                # Convert subtitle file into its derivatives

                # Importing here to prevent unneccessary slowdown
                # if the import is unused
                print(f'Download {i+1}: Converting Subtitles ({language})...')
                import subtitles_convert_existing as sub_convert
                subtitle_file = os.path.join(
                    download_directory_in_progress_active,
                    subtitle_file)
                                
                if language == 'en':
                    debug_info = sub_convert.generate_converted_subtitles(
                        subtitle_file)
                else:
                    # If language en reformatting ML-model doesn't apply
                    debug_info = sub_convert.generate_converted_subtitles(
                        subtitle_file, True, False, False)
                for key, message in debug_info.items():
                    if str.startswith(message, 'Error'):
                        logger.error(f'{key}: {message}')
                    else:
                        logger.info(f'{key}: {message}')

        # Downloaded video does NOT have automatic or manual captions
        # If this is the case and the missing langauge is English,
        # Generate new caption using ML-model.
        # This script does not have multiple models for different Languages
        if next_step_required and 'en' in subtitle_langs_covered:
            # Find video file
            file_list = os.listdir(download_directory_in_progress_active)
            video_file = None
            found = False
            for video_file_format in ['mkv', 'mp4', 'webm']:
                for file in file_list:
                    if str.endswith(file, video_file_format):
                        video_file = file
                        break
                if found:
                    break
            # If video file found, generate new Subtitles
            video_file_path = os.path.join(
                download_directory_in_progress_active,
                video_file)
            if video_file_path is not None and os.path.exists(video_file_path):
                # Importing here to prevent unneccessary slowdown
                # if the import is unused
                print(f'Download {i+1}: Generating new Subtitles...')
                import subtitles_generate_new as sub_generate
                debug_info = sub_generate.generate_new_subtitles(
                    video_file_path)
                for key, message in debug_info.items():
                    if str.startswith(message, 'Error'):
                        logger.error(f'{key}: {message}')
                    else:
                        logger.info(f'{key}: {message}')

        ### Subtitle embedding 
        # Embed subtitle files into video file
        
        # Retrieve video and subtitle files
        video_file = None
        subtitle_files = []
        downloaded_files = os.listdir(
            download_directory_in_progress_active)
        for file in downloaded_files:
            file_extension = str.split(file, '.')[-1]
            if file_extension in ['mkv', 'mp4', 'webm']:
                video_file = file
            elif file_extension in ['srt', 'vtt', 'ass']:
                subtitle_files.append(file)

        # Check video and subtitles are available
        if video_file is None:
            logger.error(
                f'Download {i+1}: No video file found to embed subs')
            _move_files(
                download_directory_in_progress_active,
                download_directory_in_progress_paused)
            logger.info(
                f'Download {i+1}: Moved files into '
                f'{download_directory_in_progress_paused} '
                f'due to missing video file')
            
            download_paused_list = os.path.join(
                config["download_directory_main"],
                config["download_directory_data"],
                config["download_to_process_list"])
            with open(download_paused_list, 'a') as paused_list_file:
                paused_list_file.write(f'{url}\n')
            logger.info(f'Download {i+1}\'s URL added '
                        f'to {download_paused_list}')
            continue
        if subtitle_files == []:
            logger.error(
                f'Download {i+1}: No subtitle files found to embed subs')
            _move_files(
                download_directory_in_progress_active,
                download_directory_in_progress_paused)
            logger.info(
                f'Download {i+1}: Moved files into '
                f'{download_directory_in_progress_paused} '
                f'due to missing subtitle files')
            
            download_paused_list = os.path.join(
                config["download_directory_main"],
                config["download_directory_data"],
                config["download_to_process_list"])
            with open(download_paused_list, 'a') as paused_list_file:
                paused_list_file.write(f'{url}\n')
            logger.info(f'Download {i+1}\'s URL added '
                        f'to {download_paused_list}')
            continue
        
        # Embed subtitles into video (overwriting the original video)
        video_file_path = os.path.join(
            download_directory_in_progress_active,
            video_file)
        subtitle_file_paths = []
        for subtitle_file_name in subtitle_files:
            subtitle_file_paths.append(os.path.join(
                download_directory_in_progress_active,
                subtitle_file_name))

        subtitles_embedding.add_subtitle_streams(
            video_file_path,
            subtitle_file_paths,
            None)

        ### Save information to central database
        database.add_to_database(
            info_json,
            video_file,
            subtitle_file_paths,
            video_source)

        ### Move finalized product to final directories
        logger.info(f'Download {i+1}: ({url}) Post processing finished!')
        _move_active_to_final(i, logger)
        print(f'Download {i+1}: Finished!')

if __name__ == '__main__':
    main()