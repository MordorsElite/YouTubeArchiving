import os
import warnings
from datetime import timedelta
from time import time
import json

import torch
import whisper
from moviepy.editor import VideoFileClip


def _extract_audio_file(video_file:str, output_audio_file:str) -> None:
    """
    Extract audio file for a video file

    Parameters
    ----------
    video_file: str
        Video file to extract audio from
    output_audio_file: str
        Path and name where the output audio file should be saved to

    Returns
    -------
    None
    """
    # Load the video file
    video = VideoFileClip(video_file)

    # Write audio to a file in m4a format
    video.audio.write_audiofile(output_audio_file, codec='aac')



def _load_model(model_size:str='base') -> whisper.Whisper:
    """
    Load the Whisper model (base model works well for general purposes)
    You can use "small", "medium", "large" models for more accuracy

    Parameters
    ----------
    model_size: str 
        Selects the model version to use for the audio transcription

    Returns
    -------
    whisper.Whisper:
        The model to use for audio transcription
    """
    # Load the Whisper model (base model works well for general purposes)
    # You can use "small", "medium", "large" models for more accuracy
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = whisper.load_model(model_size).to(device)
    return model



def _get_word_by_word_timestamps(model:whisper.Whisper, audio_file:str
        ) -> dict[str, str | list]:
    """
    Use the whisper model to transcribe the audio file.

    Parameters
    ----------
    model: whisper.Whisper
        The model to use for audio transcription
    audio_file: str
        Path to the audio file to transcribe
    
    Returns
    -------
    dict[str, str | list]:
        Transcription information including sentence segments 
        and their timestamps. 
        They can be found at results['segments']
    """
    warnings.filterwarnings("ignore", category=UserWarning)
    # Transcribe the audio with word-level timestamps
    result = model.transcribe(audio_file, word_timestamps=True)
    return result



def _format_timestamp(seconds:float) -> str:
    """
    Convert times to WebVTT format (HH:MM:SS.mmm)

    Parameters
    ----------
    seconds: float
        Input times in seconds with decimal points

    Returns
    -------
    str:
        Timestamp in WebVTT format
    """
    td = timedelta(seconds=seconds)
    hours, remainder = divmod(td.total_seconds(), 3600)
    minutes, seconds = divmod(remainder, 60)
    milliseconds = int((seconds - int(seconds)) * 1000)
    return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}.{milliseconds:03}"



def _generate_vtt(
        word_by_word_timestamps:dict[str, str | list], 
        output_subtitle_file:str) -> None:
    """
    Generate the actual .vtt file (WebVTT) from the timestamped 
    audio transcription.

    Parameters
    ----------
    word_by_word_timestamps: dict[str, str | list]
        Timestamps provided by the Whisper Models Transcription
    output_subtitle_file: str
        Path for where to save the output subtitle file
    """
    # Initialize the content for the VTT file with the WebVTT header
    vtt_content = "WEBVTT\n\n\n\n"

    # Generate VTT entries with word-by-word timestamps
    for i, segment in enumerate(word_by_word_timestamps["segments"]):
        start_time = segment["start"]
        end_time = segment["end"]
        text = segment["text"][1:]

        # Convert start and end times to WebVTT format (HH:MM:SS.mmm)
        start_vtt = _format_timestamp(start_time)
        end_vtt = _format_timestamp(end_time)
            
        # Add the entry to the VTT content
        vtt_content += f"{start_vtt} --> {end_vtt}\n"
        vtt_content += f"{text}\n\n\n"
        
        start_time = end_time  # Update start time for the next word

    # Save to a .vtt file
    with open(output_subtitle_file, "w", encoding='utf-8') as file:
        file.write(vtt_content)



def _delete_file(file_path:str) -> None:
    """
    Deletes the specified file
    
    Parameters
    ----------
    file_path: str
        Path to the file to be deleted
    """
    try:
        # Check if the file exists
        if os.path.isfile(file_path):
            os.remove(file_path)  # Delete the file
            #print(f"File '{file_path}' has been deleted.")
        else:
            #print(f"File '{file_path}' does not exist.")
            raise FileNotFoundError(f'{file_path} does not Exist!')
    except Exception as e:
        print(f"An error occurred while trying to delete the file: {e}")



def generate_new_subtitles(
        video_file:str, 
        output_subtitle_file:str=None) -> dict[str, str]:
    """
    Generate a new subtitle file from scratch by extracting the 
    audio from the input video file and using a Whisper-Model
    to transcribe it. The output file will be in WebVTT format.

    Parameters
    ----------
    video_file: str
        The video file to generate subtitles for
    output_subtitle_file: str
        Path and name of the resulting subtitle file. 
        If not given, the filename of video_file will be used
        with an appended '.en.new'

    Returns
    -------
    dict[str, str]:
        A dict with debug information about the generated subtitle file
    """
    debug_info = {}

    try:
        # Extract audio file
        temp_audio_file = f'{video_file}.temp.m4a'
        _extract_audio_file(video_file, temp_audio_file)
        debug_info['audio_file_extraction'] = \
            f'Audio file {temp_audio_file} successfully extracted'
    except Exception as err:
        debug_info['audio_file_extraction'] = 'Error: ' +\
            f'Audio file {temp_audio_file} failed to extract {err}'
        
    # Generate Transcription
    print('Transcribing...') 
    
    try:
        model = _load_model()
        result = _get_word_by_word_timestamps(model, temp_audio_file)
        debug_info['transcription_model'] = \
            f'Transcription model successfully applied.'
    except Exception as err:
        debug_info['transcription_model'] = 'Error: ' +\
            f'Transcription model failed: {err}.'

    # Generate Subtitle file from Transcriptions
    try:
        if output_subtitle_file is None:
            output_subtitle_file = video_file[:-4] + '.en.new.vtt'
        _generate_vtt(result, output_subtitle_file)
        debug_info['generate_vtt'] = \
            f'VTT subtitles generated successfully.'
    except Exception as err:
        debug_info['transcription_model'] = 'Error: ' +\
            f'VTT subtitle generation failed: {err}.'
    

    # Delete temporary audio file
    try:
        _delete_file(temp_audio_file)
        debug_info['deleted_temp_audio'] = \
            f'Temporary audio file removed.'
    except Exception as err:
        debug_info['deleted_temp_audio'] = 'Error: ' +\
            f'Temporary audio file could not be removed: {err}.'
    
    return debug_info



if __name__ == '__main__':
    pass