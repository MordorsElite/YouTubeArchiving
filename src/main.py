import os
import json
import logging
from datetime import datetime
import argparse
import sys
import shutil

import downloader
import subtitles_convert_existing as sub_convert

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


def _setup_logger(print_to_console:bool=False):
    """
    Create log-file and logger
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



def _parse_arguments():
    """
    Parse commandline arguments for use in the script
    """
    parser = argparse.ArgumentParser(description="Youtube Archiving")

    # Define arguments for downloading manually specified URL
    parser.add_argument(
        "--playlist", action="store_true", required=False,
        help="FLAG: Download playlist at given URL"
    )
    parser.add_argument(
        "--channel", action="store_true", required=False,
        help="FLAG: Download channel at given URL"
    )
    parser.add_argument(
        "--url", type=str, required=False, 
        help="URL to download"
    )

    # Define argument for downloading URLs from file
    parser.add_argument(
        "--file", type=str, required=False, 
        help="Text file containing URLs to download (one URL per line)"
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

    # Parse and return arguments
    return parser.parse_args()



def _print_error(message):
    # ANSI escape code for red text
    RED = '\033[91m'
    RESET = '\033[0m'
    print(f'{RED}[ERROR] {message}{RESET}')

def _print_error_and_exit(
        message:str, 
        logger:logging.Logger) -> int:
    """
    Prints error to log-file and console, then returns 1

    @param message: Error message (str)

    @Returns 1
    """
    logger.error(message)
    logger.error('Exiting...')
    _print_error(message)
    _print_error('Exiting...')
    return 1



def main():
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

    # Interpret console commands
    video_urls = []

    if len(sys.argv) == 1:
        print("No arguments provided. Use --help for assistance.")
        sys.argv.append("--help")
    args = _parse_arguments()
    logger.info('Input parameters:')
    logger.info(args)
    
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
                'Neither URL nor URL-file provided!')
        
        if args.playlist or args.channel:
            video_urls = downloader.get_video_urls_from_url(args.url)
            if video_urls in [None, []]:
                return _print_error_and_exit(logger,
                    f'No URLs found for '
                    f'{"playlist" if args.playlist else "channel"}!')
        else:
            video_urls = [args.url]

    logger.info(f'Video URLs to download ({len(video_urls)} total):')
    logger.info(video_urls)

    # Loop over all videos to download:
    for i, url in enumerate(video_urls):
        # Download video
        logger.info(f'Download {i+1}: {url} with aditional parameters '
                    f'rate_limit={args.rate_limit} '
                    f'and max_height={args.max_height}')
        failure = downloader.download(url, args.rate_limit, args.max_height)

        # Check if download was successful
        if not failure:
            logger.info(f'Download {i+1} finished successfully! ({url})')
        else:
            # If download unsucessful
            # Logging
            logger.error(f'Download {i+1} unsuccessful! ({url})')
            download_failed_list = os.path.join(
                config["download_directory_main"],
                config["download_directory_data"],
                config["download_failed_list"])
            with open(download_failed_list, 'a') as failed_list_file:
                failed_list_file.write(f'{url}\n')
            logger.info(f'Failed download {i+1}\'s URL added to failed list')

            # Move Files from faild download into the designated directory
            logger.info(f'Moving failed download {i+1}\'s '
                        f'files to failed files')
            download_directory_in_progress_active = os.path.join(
                config["download_directory_main"],
                config["download_directory_in_progress"],
                config["download_directory_in_progress_active"])
            download_directory_in_progress_failed = os.path.join(
                config["download_directory_main"],
                config["download_directory_in_progress"],
                config["download_directory_in_progress_failed"])
            failed_files = os.listdir(download_directory_in_progress_active)
            for file in failed_files:
                src = os.path.join(download_directory_in_progress_active, file)
                dst = os.path.join(download_directory_in_progress_failed, file)
                shutil.move(src, dst)
            logger.info(f'Finished moving failed download {i+1}\'s '
                        f'files to failed files')
        
        # Modify/generate subtitles for downloaded Video

        # Check whether download contained autogenerated, 
        # manual or no subtitles

        # Get info.json
        download_directory_in_progress_active = os.path.join(
        config["download_directory_main"],
        config["download_directory_in_progress"],
        config["download_directory_in_progress_active"])
        info_json = None
        for item in os.listdir(download_directory_in_progress_active):
            if str.endswith(item, '.json'):
                info_json = item
                break
        if info_json is None:
            logger.error(f'Download {i+1}: info.json not found!')
            # !!!!!!!!!!!!!! Error handling necessary!!!!!!!!!
            pass

        info_json = os.path.join(
            download_directory_in_progress_active,
            info_json
        )
        with open(info_json, 'r', encoding='utf-8') as info_file:
            info_data = json.load(info_file)

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
            pass





        # Move finalized product to final directories

if __name__ == '__main__':
    main()