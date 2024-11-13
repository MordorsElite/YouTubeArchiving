import os
import json
import logging
from datetime import datetime

# Load config
config_file_path = 'config/config.json'
with open(config_file_path, 'r') as config_file:
    config = json.load(config_file)


def setup_logger():
    """
    Create log-file and logger
    """
    # Create a timestamp for the filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"youtube_archiving_log_{timestamp}.txt"

    # Define log-file path
    log_file = os.path.join(
        config["download_directory_main"],
        config["download_directory_data"],
        config["download_directory_data_logs"],
        log_filename
    )
    
    # Set up logging configuration
    logging.basicConfig(
        level=logging.DEBUG,  # Log level can be changed as needed
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),  # Log to file
            logging.StreamHandler()             # Optional: Log to console
        ]
    )
    
    # Create a logger object for other modules to use
    logger = logging.getLogger(__name__)
    logger.info(f'Logging started on {timestamp}')
    return logger



def check_file_structure() -> None:
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

    raise Exception("Oh no, something went wrong!")


def main():
    # Interpret console commands
    

    
    
    

    # Create environment
    try:
        check_file_structure()
    except Exception as err:
        def print_error(message):
            # ANSI escape code for red text
            RED = '\033[91m'
            RESET = '\033[0m'
            print(f'{RED}[ERROR] {message}{RESET}')
        
        print_error('File structure not correct!')
        print_error(err)
        print_error('Exiting...')
        return 1

    # Initialize the logger for this script
    logger = setup_logger()
        
    logger.info(f'File structure checked/created successfully.')

    # Download video


    # Modify/generate subtitles for downloaded Video


    # Move finalized product to final directories

if __name__ == '__main__':
    main()