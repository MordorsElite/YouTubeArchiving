import warnings
from datetime import timedelta
from time import time
import os
from moviepy.editor import VideoFileClip
import torch
import whisper

def extract_audio_file(video_file:str, output_audio_file:str) -> None:
    # Load the video file
    video = VideoFileClip(video_file)

    # Write audio to a file in m4a format
    video.audio.write_audiofile(output_audio_file, codec='aac')

def load_model():
    # Load the Whisper model (base model works well for general purposes)
    # You can use "small", "medium", "large" models for more accuracy
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = whisper.load_model("base").to(device)
    return model

def get_word_by_word_timestamps(model, audio_file:str):
    warnings.filterwarnings("ignore", category=UserWarning)
    # Transcribe the audio with word-level timestamps
    result = model.transcribe(audio_file, word_timestamps=True)
    return result

def format_timestamp(seconds):
    # Convert times to WebVTT format (HH:MM:SS.mmm)
    td = timedelta(seconds=seconds)
    hours, remainder = divmod(td.total_seconds(), 3600)
    minutes, seconds = divmod(remainder, 60)
    milliseconds = int((seconds - int(seconds)) * 1000)
    return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}.{milliseconds:03}"

def generate_vtt(word_by_word_timestamps, output_subtitle_file:str):
    # Initialize the content for the VTT file with the WebVTT header
    vtt_content = "WEBVTT\n\n\n\n"

    # Generate VTT entries with word-by-word timestamps
    for i, segment in enumerate(word_by_word_timestamps["segments"]):
        start_time = segment["start"]
        end_time = segment["end"]
        text = segment["text"][1:]

        # Convert start and end times to WebVTT format (HH:MM:SS.mmm)
        start_vtt = format_timestamp(start_time)
        end_vtt = format_timestamp(end_time)
            
        # Add the entry to the VTT content
        vtt_content += f"{start_vtt} --> {end_vtt}\n"
        vtt_content += f"{text}\n\n\n"
        
        start_time = end_time  # Update start time for the next word

    # Save to a .vtt file
    with open(output_subtitle_file, "w") as file:
        file.write(vtt_content)

def delete_file(file_path):
    """Deletes the specified file."""
    try:
        # Check if the file exists
        if os.path.isfile(file_path):
            os.remove(file_path)  # Delete the file
            print(f"File '{file_path}' has been deleted.")
        else:
            print(f"File '{file_path}' does not exist.")
    except Exception as e:
        print(f"An error occurred while trying to delete the file: {e}")

def generate_new_subtitles(video_file:str, output_subtitle_file:str) -> None:
    # Extract audio file
    temp_audio_file = os.path.join('TempFiles', f'{video_file}.m4a')
    extract_audio_file(temp_audio_file)

    # Generate Transcription
    model = load_model()
    result = get_word_by_word_timestamps(model, temp_audio_file)

    # Generate Subtitle file from Transcriptions
    generate_vtt(result, output_subtitle_file)

    # Delete temporary audio file
    delete_file(temp_audio_file)



if __name__ == '__main__':
    audio_file = r'TempFiles\WordByWordTranscritptions.py'

    start_time_model = time()
    model = load_model()
    end_time_model = time()

    start_time_transcription = time()
    result = get_word_by_word_timestamps(model, audio_file)
    end_time_transcription = time()

    start_time_vtt = time()
    generate_vtt(result)
    end_time_vtt = time()

    print(f'Time to load model: {end_time_model - start_time_model:0.3f}s')
    print(f'Time to transcribe: {end_time_transcription - start_time_transcription:0.3f}s')
    print(f'Time to generate VTT: {end_time_vtt - start_time_vtt:0.3f}s')
