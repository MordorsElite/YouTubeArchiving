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

    Parameters
    ----------
    value: list | dict | str | any
        Value to sanatize
    """
    if isinstance(value, (list, dict)):
        return json.dumps(value)            # Serialize lists/dicts into JSON
    elif isinstance(value, str):
        value = value.replace('\n', ' ')    # Remove all newlines
        return value.replace('\0', '')      # Remove null bytes (if any)
    else:
        return value

def _write_to_csv(data:dict):
    """
    Writes data to a CSV file specified in config.

    Handles lists and dictionaries by serializing them into JSON strings.
    Ensures all values are safe for CSV formatting and creates a header 
    if the file is new or empty.

    Parameters
    ----------
    data: dict
        Key:Value datapoints to be stored in CSV (dict)
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



def get_field_value_by_video_id(
        video_id:str,
        field:str) -> str:
    """
    Get a specific value for a specific video ID

    Parameters
    ----------
    video_id: str
        ID of the video 
    field: str
        Name of the field to be returned

    Returns
    -------
    str: 
        The value for video_id and field as a String. It is not converted
        to the correct type as that is dependent on the field

    Errors
    ------
    FileNotFoundError:
        If csv file not found
    ValueError:
        If video id not found in CSV file
    KeyError
        If field not found for video_id
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

    # Find value
    for row in rows:
        if row[fieldnames[0]] == video_id:  # Match the first column with row_id
            return row[field]
    
    # Raise error if video_id not found in CSV
    raise ValueError(f"Row with ID '{video_id}' not found.")


def update_database(
        video_id:str, 
        video_source:str,
        info_json_file:str,
        subtitle_files:list[str]) -> None:
    """
    Loads a value from a specific row in a CSV file, 
    checks it and updates it based on the result.
    
    Parameters
    ----------
    video_id: str
        Video ID
    video_source: str
        What source the video download came from (ie. a playlist, channel or direct link)
    info_json_file: str
        The info.json file associated with the video id
    subtitle_files: list[str]
        Additional subtitle files

    Errors
    ------
    FileNotFoundError:
        If csv file not found
    ValueError:
        If video id not found in CSV file
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

    # Collect relevant information for CSV update from info.json
    with open(info_json_file, 'r', encoding='utf-8') as infile:
        info_json = json.load(infile)
    new_video_title = info_json['fulltitle']
    new_video_description = info_json['video_description']

    # Collect relevant information for CSV update from input
    new_video_source = video_source

    if subtitle_files is not None:
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
        new_subtitle_languages = subtitle_languages
        new_subtitle_formats = subtitle_formats

    # Find the row and check the value
    row_found = False
    for row in rows:
        if row[fieldnames[0]] == video_id:  # Match the first column with row_id
            row_found = True
            
            # Update title dict
            csv_video_title_dict = json.loads(row['video_title'])
            if new_video_title not in list(csv_video_title_dict.values()):
                csv_video_title_dict[
                    datetime.datetime.now().strftime("%Y.%m.%d_%H.%M.%S")] = \
                    _sanitize_value(new_video_title)
                row['video_title'] = json.dumps(csv_video_title_dict)
                
            # Update description dict
            csv_video_description_dict = json.loads(row['video_description'])
            if new_video_description not in list(csv_video_description_dict.values()):
                csv_video_description_dict[
                    datetime.datetime.now().strftime("%Y.%m.%d_%H.%M.%S")] = \
                    _sanitize_value(new_video_description)
                row['video_description'] = json.dumps(csv_video_description_dict)
            
            # Update video source list
            csv_video_source_list = json.loads(row['video_source'])
            if new_video_source not in csv_video_source_list:
                csv_video_source_list += new_video_source
                row['video_source'] = json.dumps(csv_video_source_list)

            if subtitle_files is not None:
                # Update Subtitle Languages
                csv_subtitle_language_list = json.loads(row['subtitle_languages'])
                csv_subtitle_language_list += (new_subtitle_languages)
                csv_csv_subtitle_language_list = list(set(csv_subtitle_language_list))
                row['subtitle_languages'] = json.dumps(csv_subtitle_language_list)

                # Update Subtitle Formats
                csv_subtitle_format_list = json.loads(row['subtitle_formats'])
                csv_subtitle_format_list += new_subtitle_formats
                csv_subtitle_format_list = list(set(csv_subtitle_format_list))
                row['subtitle_languages'] = json.dumps(csv_subtitle_format_list)

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

    Parameters
    ----------
    info_json_file: str
        The info.json file associated with the video id. 
        This is used to get most of the metadata for the video database.
    video_file: str
        Name of the video file
    subtitle_files: list[str] 
        Additional subtitle files
    video_source: str
        What source the video download came from (ie. a playlist, channel or direct link)
    """
    with open(info_json_file, 'r', encoding='utf-8') as infile:
        info_json = json.load(infile)

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
    csv_data['download_date'] = \
        datetime.datetime.now().strftime("%Y.%m.%d_%H.%M.%S")
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
    csv_data['subtitle_languages'] = list(set(subtitle_languages))
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

if __name__ == '__main__':
    possible_fields = [
        'video_id',
        'video_title',
        'video_language',
        'video_length',
        'video_file',
        'video_file_size',
        'channel_id',
        'channel_name',
        'uploader_id',
        'uploader_name',
        'upload_date',
        'download_date',
        'video_source',
        'subtitle_languages',
        'subtitle_formats',
        'video_description',
        'video_captions_full'
    ]
    for field in possible_fields:
        value = get_field_value_by_video_id(
            'wXcS9oD1_i8',
            field)
        print(f'{field} : {value}')
