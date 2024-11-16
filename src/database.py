import os
import json
import csv
import datetime

# Load config
config_file_path = 'config/config.json'
with open(config_file_path, 'r') as config_file:
    config = json.load(config_file)

def _sanitize_value(value):
    """
    Sanitizes a value to ensure it doesn't interfere with CSV formatting.
    - Lists and dictionaries are converted to JSON strings.
    - Strings are encoded to handle special characters safely.
    """
    if isinstance(value, (list, dict)):
        return json.dumps(value)  # Serialize lists/dicts into JSON
    elif isinstance(value, str):
        return value.replace('\0', '')  # Remove null bytes (if any)
    else:
        return value

def _write_to_csv(data:dict):
    """
    Writes data to a CSV file specified in config.

    Handles lists and dictionaries by serializing them into JSON strings.
    Ensures all values are safe for CSV formatting and creates a header 
    if the file is new or empty.

    @param data: Key:Value datapoints to be stored in CSV (dict)
    """
    # Path to the CSV file
    csv_file = os.path.join(
        config['download_directory_main'],
        config['download_directory_data'],
        config['download_database'])
    
    # Extract header and sanitized row data
    header = list(data.keys())
    row = [_sanitize_value(value) for value in data.values()]
    
    # Check if the file exists and is non-empty
    file_exists = os.path.exists(csv_file)
    file_is_empty = file_exists and os.path.getsize(csv_file) == 0
    
    # Open the file in append mode or create it
    with open(csv_file, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        
        # Write the header if the file is being created or is empty
        if not file_exists or file_is_empty:
            writer.writerow(header)
        
        # Write the row data
        writer.writerow(row)



def update_database(
        video_id:str, 
        video_source:str,
        info_json:str,
        subtitle_files:list[str]):
    """
    Loads a value from a specific row in a CSV file, checks it, and updates it based on the result.
    
    !!!!!!!! WORK IN PROGRESS, NOT READY YET !!!!!!!!!

    Args:
        video_id (str): Video ID
        video_source (str): What source the video download came from 
            (ie. a playlist, channel or direct link)
        info_json (str): The info.json file associated with the video id
        subtitle_files (list[str]): Additional subtitle files
    """
    csv_file = os.path.join(
        config['download_directory_main'],
        config['download_directory_data'],
        config['download_database'])

    # Check if the file exists
    if not os.path.exists(csv_file):
        raise FileNotFoundError(f"The file {csv_file} does not exist.")
    
    # Read the CSV file into memory
    with open(csv_file, mode='r', newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        rows = list(reader)  # Load all rows into a list
        fieldnames = reader.fieldnames  # Save the header
    
    column_name = 'example_datapoint'

    # Find the row and check the value
    row_found = False
    for row in rows:
        if row[fieldnames[0]] == video_id:  # Match the first column with row_id
            row_found = True
            current_value = row[column_name]
            # Check the current value
            if current_value == 'X':
                # Update the value based on the update function
                row[column_name] = 'Y'
            break
    
    if not row_found:
        raise ValueError(f"Row with ID '{video_id}' not found.")
    
    # Write the updated data back to the CSV file
    with open(csv_file, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()  # Write the header
        writer.writerows(rows)  # Write the updated rows



def add_to_database(
        info_json_file:str,
        video_file:str,
        subtitle_files:list[str], 
        video_source:str) -> None:
    """
    Save data to CSV file
    """
    with open(info_json_file, 'r', encoding='utf-8') as infile:
        info_json = json.load(info_json)

    csv_data = {}

    csv_data['video_id'] = info_json['id']
    csv_data['video_title'] = {
        datetime.datetime.now().strftime("%Y.%m.%d_%H.%M.%S"): 
        info_json['fulltitle']}
    csv_data['video_language'] = info_json['language']
    csv_data['video_length'] = info_json['duration']

    csv_data['video_file'] = video_file
    csv_data['video_file_size'] = info_json['filesize_approx']

    csv_data['channel_id'] = info_json['channel_id']
    csv_data['channel_name'] = info_json['channel']
    csv_data['uploader_id'] = info_json['uploader_id']
    csv_data['uploader_name'] = info_json['uploader']

    csv_data['upload_date'] = info_json['upload_date']
    csv_data['download_date'] = datetime.date().strftime()
    csv_data['video_source'] = [video_source]

    subtitle_languages = []
    subtitle_formats = []
    for file in subtitle_files:
        sub_file_split = str.split(file, '.')
        if sub_file_split[-2] in config['subtitle_languages']:
            subtitle_formats.append(sub_file_split[-2])
            subtitle_languages.append(sub_file_split[-2])
        else:
            subtitle_formats.append(
                sub_file_split[-3] + '.' + sub_file_split[-2])
            subtitle_languages.append(sub_file_split[-3])
    csv_data['subtitle_languages'] = subtitle_languages
    csv_data['subtitle_formats'] = subtitle_formats

    csv_data['video_description'] = {
        datetime.datetime.now().strftime("%Y.%m.%d_%H.%M.%S"):
        info_json['description']}

    video_captions_full = None
    # No subtitles found to provide video text
    if subtitle_formats == None:
        video_captions_full = f'Subtitles not found'
    # Get text from self generated subtitles
    elif (len(subtitle_files) == 1 
          and str.endswith(subtitle_formats[0], 'new')):
        with open(subtitle_files[0], 'r', encoding='utf-8') as infile:
                video_captions_full = infile.read()
    # Get text from youtube official subtitles
    else:
        autogen_sub_file = None
        highest_prio_sub = config['subtitle_priority'][0]
        for lang in config['subtitle_languages']:
            for file in subtitle_files:
                sub_file_split = str.split(file, '.')
                if f'{sub_file_split[-3]}.{sub_file_split[-2]}' == \
                        f'{lang}.{highest_prio_sub}':
                    autogen_sub_file = file
                    break
                elif sub_file_split[-2] == lang:
                    autogen_sub_file = file
            if autogen_sub_file is not None:
                break
        if autogen_sub_file is not None:
            with open(autogen_sub_file, 'r', encoding='utf-8') as infile:
                video_captions_full = infile.read()
        else:
            video_captions_full = f'Subtitles not found'
    csv_data['video_captions_full'] = video_captions_full

    ### Write to CSV
    _write_to_csv(csv_data)



