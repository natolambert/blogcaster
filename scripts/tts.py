import requests
import argparse
from tqdm import tqdm
import subprocess
import yaml
import os
from pydub import AudioSegment
import numpy as np
from datetime import timedelta
from math import floor 

def strip_title(string):
    """
    Config entry, as dicts, keep track of titles as N_title goes here. 
    Return the text after the _
    """
    if "_" in string:
        return string.split("_")[1]
    else:
        return string

def get_cumulative_length(file_list):
    cumulative_length = 0
    for filename in file_list:
        # filepath = os.path.join(directory, filename)
        audio = AudioSegment.from_file(filename)
        cumulative_length += len(audio)
    return cumulative_length / 1000.0  # Convert to seconds

def request_audio(url, payload, headers, querystring, filename):
    """
    A function to replace the following code:
    response = requests.post(url_nathan, json=payload, headers=headers, params=querystring)
    with open(f"{args.output}_part{i}.mp3", 'wb') as part_file:
        for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
            if chunk:
                part_file.write(chunk)
    """
    response = requests.post(url, json=payload, headers=headers, params=querystring)
    with open(filename, 'wb') as part_file:
        for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
            if chunk:
                part_file.write(chunk)

if __name__ == "__main__":
    # import argparse and define txt file path and output path
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=str, required=True, help="input directory to work with")
    parser.add_argument("--output", type=str, default="generated_audio", help="output mp3 file path")
    args = parser.parse_args()
    
    TOTAL_GEN_AUDIO_FILES = 0
                    
    # example usage in comments for this python script tts.py
    # python tts.py --input source/test-post

    CHUNK_SIZE = 1024
    url_nathan = "https://api.elevenlabs.io/v1/text-to-speech/JOTluSP6086ORVtQED4S"
    # url_newsread = "https://api.elevenlabs.io/v1/text-to-speech/frqJk20JrduLkgUgHtMR"

    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": "c23b31aabf009cb93c8feb5f4ddedc85"
    }

    # Uncomment for higher bitrate (larger files)
    # querystring = {"output_format":"mp3_44100_192"}
    querystring = {}
        
    # load yml file at args.input + config.yml
    with open(args.input + "config.yml", "r") as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
        
    # audio_config = 
    payload = {
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "similarity_boost": 0.75,
                "stability": 0.50,
                "style": 0.05,
                "use_speaker_boost": True
            }
        }
    
    # create dir audio at args.input + audio
    audio_dir = args.input + "audio"
    if not os.path.exists(audio_dir):
        os.makedirs(audio_dir)
        
    first_gen = True
    section_titles = []
    see_figures_idx = []
    # iterate over config file that contains headings, text, and figures
    for i, (heading, content) in tqdm(enumerate(config.items())):
        print(f"Generating audio for section {i}, {heading}")
        heading = strip_title(heading)
        # skip md file path and date
        if heading in ["md", "date"]:
            continue
        else: 
            section_titles.append(heading)
        
        if first_gen:
            # generate audio file for Title + date
            heading = heading + " was published on " + config["date"] + "."
            first_gen = False
            
        payload["text"] = heading
        # generate audio for heading
        
        fname = f"{audio_dir}/audio_{i}_0.mp3"
        if not os.path.exists(fname):
            request_audio(url_nathan, payload, headers, querystring, fname)
        TOTAL_GEN_AUDIO_FILES += 1
        
        # iterate over list of dicts in content and 
        for para in content:
            idx = para["index"]
            # convert IDX to 2 digit string
            idx = str(idx).zfill(2)
            
            # if para is dict, do nothing
            if type(para["content"]) == dict:
                # copy file source/repeat/see-figure.mp3 as audio_{idx}.mp3
                os.system(f"cp source/repeat/see-figure.mp3 {audio_dir}/audio_{i}_{idx}.mp3")
                see_figures_idx.append(TOTAL_GEN_AUDIO_FILES)
                TOTAL_GEN_AUDIO_FILES += 1
                pass
            # if para is str, generate audio
            elif type(para["content"]) == str:
                payload["text"] = para["content"]
                fname = f"{audio_dir}/audio_{i}_{idx}.mp3"
                if not os.path.exists(fname):
                    request_audio(url_nathan, payload, headers, querystring, fname)
                TOTAL_GEN_AUDIO_FILES += 1
            else:
                print("Config Error: para is neither dict nor str")
        
    # concatenate all files in audio_dir with ffmpeg into input dir

    # if file generated_audio.mp3 already exists, delete it (prevent infinite loop)
    if os.path.exists(audio_dir + '/' + args.output + ".mp3"):
        os.remove(audio_dir + '/' + args.output + ".mp3")
    if os.path.exists(audio_dir + '/' + args.output +"_podcast"+".mp3"):
        os.remove(audio_dir + '/' + args.output +"_podcast"+".mp3")
        
    # list mp3 files in audio_dir
    audio_files_short = [audio_dir + '/' + f for f in os.listdir(audio_dir) if f.endswith(('.mp3'))]
    audio_files = sorted(audio_files_short)
        
    # output_files = [f"{audio_dir}/audio_{i}.mp3" for i in range(0, TOTAL_GEN_AUDIO_FILES)]
    print(f"Sorted audio files {audio_files}")

    # for podcast version remove "see figures" from see_figures_idx of files above
    podcast_files = [f for i, f in enumerate(audio_files) if i not in see_figures_idx]

    subprocess.run(["ffmpeg", "-i", "concat:" + "|".join(audio_files), "-c", "copy", audio_dir + '/' + args.output+".mp3"])
    subprocess.run(["ffmpeg", "-i", "concat:" + "|".join(podcast_files), "-c", "copy", audio_dir + '/' + args.output+"_podcast"+".mp3"])

    # TODO remove all acronyms and other filtering, some that are bad are SOTA and MoE
    # TODO add seperate voice for quotes / quote detection
    
    # Get length of the sections and print in podcast format
    # get indicies in between first set of _ (e.g. audio_N_Y.mp3, get unique Ns)
    sections = np.unique([s.split("_")[1] for s in audio_files_short])
    sections = [str(s) for s in sections]
    
    def print_if_hour(seconds):
        if seconds > 3600:
            return str(timedelta(seconds=seconds))
        elif seconds < 600:
            return str(timedelta(seconds=seconds))[3:]
        else:
            return str(timedelta(seconds=seconds))[2:]
    
    # TODO make below work for multiple figures :/ 
    # iterate over headings for chapters, take first figure per section
    print(f"Printing podcast chapter versions (does not include `see figure` audio):")
    print(f"----------------------------------")
    files_list_of_lists = []
    for s in sections:
        files = [f for f in audio_files_short if f.split("_")[1] == s]
        files_list_of_lists.append(files)
    section_lens = [get_cumulative_length(l) for l in files_list_of_lists]
    print(f"Cumulative length of all audio files: {section_lens} seconds")

    cur_len = 0
    for section_title, section_len in zip(section_titles, section_lens):
        cur_len += floor(section_len)
        print(f"{print_if_hour(cur_len)} {section_title}")
    
    print(f"----------------------------------")
    print(f"Printing youtube chapter versions:")
    print(f"----------------------------------")
    files_list_of_lists = []
    for s in sections:
        files = [f for f in podcast_files if f.split("_")[1] == s]
        files_list_of_lists.append(files)
    section_lens = [get_cumulative_length(l) for l in files_list_of_lists]

    cur_len = 0
    for section_title, section_len in zip(section_titles, section_lens):
        cur_len += floor(section_len)
        print(f"{print_if_hour(cur_len)} {section_title}")