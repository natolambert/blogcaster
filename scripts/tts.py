import requests
import argparse
from tqdm import tqdm
import subprocess
import yaml
import os

def strip_title(string):
    """
    Config entry, as dicts, keep track of titles as N_title goes here. 
    Return the text after the _
    """
    return string.split("_")[1]

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

    # with open(args.input, "r") as f:
    #     data = f.read()
        
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
    # iterate over config file that contains headings, text, and figures
    for i, (heading, content) in tqdm(enumerate(config.items())):
        # skip md file path and date
        if heading in ["md", "date"]:
            continue
        
        heading = strip_title(heading)
        if first_gen:
            # generate audio file for Title + date
            heading = heading + " was published on " + config["date"] + "."
            first_gen = False
            
        payload["text"] = heading
        # generate audio for heading
        request_audio(url_nathan, payload, headers, querystring, f"{audio_dir}/audio__{i}_0.mp3")
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
                TOTAL_GEN_AUDIO_FILES += 1
                pass
            # if para is str, generate audio
            elif type(para["content"]) == str:
                payload["text"] = para["content"]
                request_audio(url_nathan, payload, headers, querystring, f"{audio_dir}/audio_{i}_{idx}.mp3")
                TOTAL_GEN_AUDIO_FILES += 1
            else:
                print("Config Error: para is neither dict nor str")
        
    # concatenate all files in audio_dir with ffmpeg into input dir

    # list mp3 files in audio_dir
    audio_files = [audio_dir + '/' + f for f in os.listdir(audio_dir) if f.endswith(('.mp3'))]
    audio_files = sorted(audio_files)
    
    output_files = [f"{audio_dir}/audio_{i}.mp3" for i in range(0, TOTAL_GEN_AUDIO_FILES)]
    print(f"Sorted audio files {audio_files}")
    subprocess.run(["ffmpeg", "-i", "concat:" + "|".join(audio_files), "-c", "copy", audio_dir + '/' + args.output+".mp3"])

    # TODO remove all acronyms and other filtering, some that are bad are SOTA and MoE
    # TODO add seperate voice for quotes / quote detection
    # TODO see image audio for figures