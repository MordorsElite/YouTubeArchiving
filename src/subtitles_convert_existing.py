import re
import warnings
from deepmultilingualpunctuation import PunctuationModel



class TimedToken():
    def __init__(self, start:str, end:str, token='') -> None:
        self.start = re.sub(r'[<>]', '', start)
        self.end = re.sub(r'[<>]', '', end)
        self.token = token

    def add_token(self, token):
        self.token = token

    def __eq__(self, other):
        if isinstance(other, TimedToken):
            return (
                self.token == other.token and
                self.start == other.start and
                self.end == other.end
            )
        return False
    
    def __str__(self):
        return f'TimedToken(start={self.start}, end={self.end}, token={self.token})'



class Block():
    def __init__(self, timed_tokens:list[TimedToken]) -> None:
        self.invalid = False
        self.timed_tokens = self.sortTokens(timed_tokens)
        if timed_tokens is not None and timed_tokens != []:
            self.start = self.timed_tokens[0].start
            self.end = self.timed_tokens[-1].end
        else:
            self.invalid = True

    def sortTokens(self, timed_tokens) -> list[TimedToken]:
        return sorted(timed_tokens, key=lambda token: token.start)



def _get_word_time_triples(line, pattern_time_stamp):
    # Find all timestamps
    timestamps = re.findall(pattern_time_stamp, line)
    
    # Split the line on the timestamps to get the text between them
    text_segments = re.split(pattern_time_stamp, line)
    
    # Strip spaces from segments and remove empty entries
    text_segments = [segment.strip() for segment in text_segments if segment.strip() != ""]
    
    # Prepare the list to store the triples
    triples = []
    
    # Iterate through each segment of text and assign it timestamps
    for i, segment in enumerate(text_segments):
        start_time = timestamps[i-1] if i > 0 else None
        end_time = timestamps[i] if i < len(timestamps) else None
        triples.append((start_time, end_time, segment))
    
    return triples



def _get_four_line_blocks(file_path:str) -> list[list[str]]:
    # Read the file and split it into lines
    with open(file_path, 'r') as file:
        lines = file.readlines()

    # Strip leading/trailing whitespace from each line (including newline characters)
    lines = [line.rstrip() for line in lines]

    # Remove trailing empty lines if present
    while lines and lines[-1] == '':
        lines.pop()

    # Calculate the number of lines left over after grouping by 4
    leftover = len(lines) % 4

    if leftover == 1:
        # If there's exactly 1 leftover line, remove it
        lines = lines[:-1]
    elif leftover > 1:
        # If there are 2 or 3 leftover lines, add empty lines to complete a 4-line block
        lines.extend([''] * (4 - leftover))

    # Now group the lines into 4-line blocks
    blocks = [lines[i:i + 4] for i in range(0, len(lines), 4)]

    return blocks



def _split_text_into_sentences(text:str) -> list[str]:
    # Suppressing Warning about depricated attribute in imported code
    original_warning_filters = warnings.filters[:]
    warnings.filterwarnings("ignore", message="`grouped_entities` is deprecated")
    punctuation_model = PunctuationModel()
    warnings.filters = original_warning_filters

    # Load model
    text_with_punctuation = punctuation_model.restore_punctuation(text)

    # Run model
    delimiters = r"[;:!?.]"
    sentences = re.split(delimiters, text_with_punctuation)
    return sentences



def _split_sentence_into_subtitle_lines(text:str, max_line_length=42) -> list[str]:
    words = text.split()
    lines = []
    current_line = ""

    for word in words:
        # Check if adding the next word would exceed the maximum length
        if len(current_line) + len(word) + 1 > max_line_length:
            # If current_line is empty, check if the word itself is too long
            if current_line:
                lines.append(current_line.strip())
                current_line = ""
            elif len(word) > max_line_length:
                # If the word is longer than max_line_length, split it
                lines.append(word)
                continue
        
        # Add the word to the current line
        current_line += word + " "

        # Check for a comma that might indicate a preferred break
        if ',' in current_line and len(current_line.strip()) > max_line_length * 0.8:
            # Split at the last comma
            split_index = current_line.rfind(',')
            # Ensure the comma is not part of a number
            if split_index != -1:
                # Check if the comma is surrounded by digits
                if (split_index > 0 and current_line[split_index - 1].isdigit() and
                        split_index < len(current_line) - 1 and current_line[split_index + 1].isdigit()):
                    continue  # Skip splitting at this comma
                
                # Split at the last valid comma
                lines.append(current_line[:split_index + 1].strip())
                current_line = current_line[split_index + 1:].strip() + " "

    # Append any remaining words in current_line
    if current_line:
        lines.append(current_line.strip())

    return lines



def _get_token_list(subtitle_file:str) -> list[TimedToken]:
    pattern_block_start = r"^\d{2}:\d{2}:\d{2}\.\d{3} --> \d{2}:\d{2}:\d{2}\.\d{3}"
    pattern_caption_start = r"<c>"
    pattern_caption_end = r"</c>"
    pattern_time_stamp = r"<\d{2}:\d{2}:\d{2}\.\d{3}>"

    # Extract TimedTokens
    list_of_all_tokens = [] 
    four_line_blocks = _get_four_line_blocks(subtitle_file)  
    for i, four_line_block in enumerate(four_line_blocks):
        # Skip header block
        if i == 0:
            continue 
            
        # Something went wrong or last block reached
        if not re.match(pattern_block_start, four_line_block[0]):
            continue
            
        # Get the block start and stop times
        block_start_time = four_line_block[0][:12]
        block_end_time = four_line_block[0][17:29]
        
        # Not sure if this is needed yet
        if four_line_block[1].strip() != '':
            pass

        line = four_line_block[2]
        line = re.sub(pattern_caption_start, '', line)
        line = re.sub(pattern_caption_end, '', line)

        # Extract new TimedTokens
        triples = _get_word_time_triples(line, pattern_time_stamp)
        for start, end, token in triples:
            if start is None:
                start = block_start_time
            if end is None:
                end = block_end_time
            list_of_all_tokens.append(TimedToken(start, end, token))

    # Remove duplicate tokens
    duplicate_token_indexes = []
    for i in range(len(list_of_all_tokens) - 1):
        current_token = list_of_all_tokens[i]
        next_token = list_of_all_tokens[i+1]

        if (current_token.token == next_token.token and 
            current_token.end == next_token.start):
            current_token.end = next_token.start
            duplicate_token_indexes.append(i+1)

    return [token for idx, token in enumerate(list_of_all_tokens)
            if idx not in duplicate_token_indexes]



def _get_caption_lines(list_of_all_tokens:list[TimedToken]) -> list[str]:
    # Concatenate all tokens into the overall transcript
    full_text = ''
    for timed_token in list_of_all_tokens:
        full_text += timed_token.token + ' '
    
    # Add punctuation to transcript and split text into sentences
    sentences = _split_text_into_sentences(full_text)

    # Split sentences into lines that fit on the screen
    caption_lines = []
    for sentence in sentences:
        caption_lines += _split_sentence_into_subtitle_lines(sentence)

    return caption_lines



def _clean_string(string:str) -> str:
    # Function to clean up sentences and tokens
    return re.sub(r'[;:!?.,-]', '', string.strip())



def generate_non_iterative_subtitles_reformat(caption_lines:str, list_of_all_tokens:list, 
                                     subtitle_file_header:str, output_file:str):
    # Find timing points for non-iterative subtitles
    i = 0
    line_triples = []
    for line in caption_lines:
        line_copy = _clean_string(line)
        line_start_time = None
        line_end_time = None

        if str.startswith(line_copy, _clean_string(list_of_all_tokens[i].token)):
            line_start_time = list_of_all_tokens[i].start

        while str.startswith(line_copy, _clean_string(list_of_all_tokens[i].token)):
            line_end_time = list_of_all_tokens[i].end
            line_copy = line_copy[len(_clean_string(list_of_all_tokens[i].token)) + 1:]
            
            i += 1
            if i >= len(list_of_all_tokens):
                break

        line_triples.append((line_start_time, line_end_time, line))

    # Write non-iterative subtitle file
    with open(output_file, 'w') as outfile:
        outfile.write(f'{subtitle_file_header}\n')

        for i, (start, end, line) in enumerate(line_triples):
            if None in [start, end, line]:
                raise Exception(f'Error when creating Subtitle-file \"{output_file}\"! '+
                                f'A value in {[start, end, line]} was None (line {i+1})')
            line = str.replace(line, '&nbsp', ' ')
            outfile.write(f'{start} --> {end} \n{line}\n\n\n')
    


def generate_iterative_subtitles_reformat(caption_lines:str, list_of_all_tokens:list, 
                                 subtitle_file_header:str, output_file:str):
    # Find timing points for iterative subtitles
    i = 0
    line_triples = []
    for line in caption_lines:
        line_copy = _clean_string(line)

        # Get all timed lines for a given block
        cumulative_block_line = ''
        while str.startswith(line_copy, _clean_string(list_of_all_tokens[i].token)):
            line_copy = line_copy[len(_clean_string(list_of_all_tokens[i].token)) + 1:]
            
            cumulative_block_line += list_of_all_tokens[i].token + ' '
            line_triples.append((list_of_all_tokens[i].start, 
                                 list_of_all_tokens[i].end, 
                                 cumulative_block_line))

            i += 1
            if i >= len(list_of_all_tokens):
                break

    # Write iterative subtitle file
    with open(output_file, 'w') as outfile:
        outfile.write(f'{subtitle_file_header}\n')

        for i, (start, end, line) in enumerate(line_triples):
            if None in [start, end, line]:
                raise Exception(f'Error when creating Subtitle-file \"{output_file}\"! '+
                                f'A value in {[start, end, line]} was None (line {i+1})')
            line = str.replace(line, '&nbsp', ' ')
            outfile.write(f'{start} --> {end} \n{line}\n\n\n')



def generate_iterative_subtitles_direct(subtitle_file:str, 
                                        subtitle_file_header:str, output_file:str) -> None:
    pattern_block_start = r"^\d{2}:\d{2}:\d{2}\.\d{3} --> \d{2}:\d{2}:\d{2}\.\d{3}"
    pattern_caption_start = r"<c>"
    pattern_caption_end = r"</c>"
    pattern_time_stamp = r"<\d{2}:\d{2}:\d{2}\.\d{3}>"

    list_of_all_tokens = [] 
    list_of_subtitle_blocks = []

    orignal_four_line_blocks = _get_four_line_blocks(subtitle_file)  

    for i, block in enumerate(orignal_four_line_blocks):
        # Skip header block
        if i == 0:
            continue 
            
        # Something went wrong or last block reached
        if not re.match(pattern_block_start, block[0]):
            continue
            
        # Get the block start and stop times
        block_start_time = block[0][:12]
        block_end_time = block[0][17:29]
        
        # Not sure if this is needed yet
        if block[1].strip() != '':
            pass

        line = block[2]
        line = re.sub(pattern_caption_start, '', line)
        line = re.sub(pattern_caption_end, '', line)

        # Extract new TimedTokens
        list_of_tokens_in_block = []
        triples = _get_word_time_triples(line, pattern_time_stamp)
        for start, end, token in triples:
            if start is None:
                start = block_start_time
            if end is None:
                end = block_end_time

            timed_token = TimedToken(start, end, token)
            list_of_all_tokens.append(timed_token)
            list_of_tokens_in_block.append(timed_token)

        # Make new block for timed tokens
        list_of_subtitle_blocks.append(Block(list_of_tokens_in_block))

    # Remove duplicate tokens
    duplicate_token_indexes = []
    for i in range(len(list_of_all_tokens) - 1):
        current_token = list_of_all_tokens[i]
        next_token = list_of_all_tokens[i+1]

        if (current_token.token == next_token.token and 
            current_token.end == next_token.start):
            current_token.end = next_token.start
            duplicate_token_indexes.append(i+1)

    list_of_all_tokens = [
        token for idx, token in enumerate(list_of_all_tokens)
        if idx not in duplicate_token_indexes]
    
    #for timed_token in list_of_all_tokens[:50]:
    #    print(timed_token)

    # Write new file
    with open(output_file, 'w') as outfile:
        outfile.write(f'{subtitle_file_header}\n')
        
        for block in list_of_subtitle_blocks:
            if block.invalid:
                continue
            block_text = ''
            for token in block.timed_tokens:
                block_text += f'{token.token} '
                outfile.write(f'{token.start} --> {token.end} \n')
                outfile.write(f'{block_text} \n\n\n')



if __name__ == '__main__':
    subtitle_file = 'Jodi Trolls Yvonne for 10 Minutes [CQMzhZEHex4].en.vtt'
    output_file = 'EN.vtt'

    with open(subtitle_file, 'r') as original:
        header = ''
        for i in range(4):
            header += original.readline()
        header = header[:-1]

    token_list = _get_token_list(subtitle_file)
    caption_lines = _get_caption_lines(token_list)


    generate_non_iterative_subtitles_reformat(caption_lines, token_list, header, 
        output_file[:-4] + '.reformatted.non-iterative' + output_file[-4:])
    generate_iterative_subtitles_reformat(caption_lines, token_list, header,
        output_file[:-4] + '.reformatted.iterative' + output_file[-4:])
    
    generate_iterative_subtitles_direct(subtitle_file, header, 
        output_file[:-4] + '.direct.iterative' + output_file[-4:])