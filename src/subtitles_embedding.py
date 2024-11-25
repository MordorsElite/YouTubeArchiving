import json
import logging
import os
import sys

import ffmpeg

# Load config
config_file_path = 'config/config.json'
with open(config_file_path, 'r') as config_file:
    config = json.load(config_file)



def _get_subtitle_language(subtitle_file:str) -> str:
    """
    Reads out the 'language' from a subtitle file

    Example: 'name.en.dir_iter.vtt' would return 'en.dir_iter'
    Example: 'name.en.vtt' would return 'en'

    Parameters
    ----------
    subtitle_file: str
        Path to a subtitle file

    Returns
    -------
    str:
        'language' of the input subtitle file according to its title
    """
    split_sub_file = str.split(subtitle_file, '.')
    language = split_sub_file[-2]
    if language in config["subtitle_languages"]:
        return language
    else:
        return split_sub_file[-3] + '.' + language
    


def _order_subtitles(subtitle_files:list[str]) -> list[str]:
    """
    Orders subtitle files according to the priorities specified in the config.
    Priorities are grouped by language according to the order of occurance in
    the config entry 'subtitle_languages'. Per language the subtitles are further
    ordered by 'subtitle_priority'

    Parameters
    ----------
    subtitle_files: list[str]
        List of subtitle files to order

    Returns
    -------
    list[str]:
        Ordered list of the subtitle files from the input
    """
    # Find "language" of each subtitle file
    subtitle_languages = [_get_subtitle_language(sf) for sf in subtitle_files]

    # Assign each subtitle file a priority index
    pritority_idices = []
    for lang in config["subtitle_languages"]:
        for lang_prio in config["subtitle_priority"]:
            # Resolve language_to_check
            language_to_check = None
            if lang_prio == 'default':
                # Only uses main language abbreviation for default youtube subs
                language_to_check = lang
            else:
                language_to_check = f'{lang}.{lang_prio}'
            # Check if language is available
            try:
                index = subtitle_languages.index(language_to_check)
                pritority_idices.append(index)
            except:
                continue
    # Return ordered list of subtitle files
    return [subtitle_files[idx] for idx in pritority_idices]
        


def add_subtitle_streams(
        video_file:str, 
        subtitle_files:list[str],
        output_file:str=None) -> None:
    """
    Embeds all subtitles into the given video file. 

    Subtitles are ordered according to the priorities specified in the config.
    Priorities are grouped by language according to the order of occurance in
    the config entry 'subtitle_languages'. Per language the subtitles are further
    ordered by 'subtitle_priority'

    Parameters
    ----------
    video_file: str
        Video file to embed subtitles into
    subtitle_files: list[str]
        All subtitle files to embed
    output_file: str
        Path of output video file. If not given, 
        input file will be overwritten instead
    """
    # If no output file is defined, overwrite input file
    if output_file is None or output_file == video_file:
        output_file = video_file[:-4] + '.temp' + video_file[-4:]
    
    # Order subtitle files
    subtitle_files = _order_subtitles(subtitle_files)

    # Define ffmpeg input
    input_ffmpeg = ffmpeg.input(video_file)
    input_ffmpeg_subtitles = [ffmpeg.input(sub_file) for sub_file in subtitle_files]

    # Define ffmpeg output
    input_video = input_ffmpeg['v']
    input_audio = input_ffmpeg['a']
    input_subtitles = [subtitle['s'] for subtitle in input_ffmpeg_subtitles]

    # Define langauge metadata
    lang_metadata = {}
    for i, sub_file in enumerate(subtitle_files):
        language = _get_subtitle_language(sub_file)
        lang_metadata[f'metadata:s:s:{i}'] = f'language={language}'

    scodec_dict = {f'scodec:s:{i}': 'webvtt' 
                   for i in range(len(subtitle_files))}

    output_ffmpeg = ffmpeg.output(
        input_video, input_audio, 
        *input_subtitles,
        output_file, 
        vcodec='copy', acodec='copy',
        map='0:t',
        **lang_metadata,
        **scodec_dict)

    output_ffmpeg = ffmpeg.overwrite_output(output_ffmpeg)

    ffmpeg.run(output_ffmpeg)

    # Overwrite previous video file
    os.remove(video_file)
    os.rename(output_file, video_file)



if __name__ == '__main__':
    pass