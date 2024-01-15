# Please shoot me a message, open an issue, or comment on Interconnects if you're using this code! I'd love to know.

import argparse
import os
import subprocess
from datetime import timedelta
from math import floor

import numpy as np
import requests
import yaml
from pydub import AudioSegment
from tqdm import tqdm


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
    # remove \n and > from payload text
    payload["text"] = payload["text"].replace("\n", " ")
    payload["text"] = payload["text"].replace(">", "")

    if not os.path.exists(filename):
        print("-> audio request send to 11labs")
        try:
            response = requests.post(url, json=payload, headers=headers, params=querystring)
            with open(filename, "wb") as part_file:
                for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                    if chunk:
                        part_file.write(chunk)
        except Exception as e:
            print(f"Error: {e}")
    else:
        print(f"-> audio file {filename} already exists, skipping request")


if __name__ == "__main__":
    # import argparse and define txt file path and output path
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=str, required=True, help="input directory to work with")
    parser.add_argument("--output", type=str, default="generated_audio", help="output mp3 file path")
    parser.add_argument("--elelabs_voice", type=str, default="WerIBRrBvioo2do7d1qq", help="11labs voice id")
    parser.add_argument("--start_heading", type=str, default="", help="start at section named in generation")
    parser.add_argument("--farewell_audio", type=str, default="source/repeat/farewell.mp3", help="farewell audio path")
    parser.add_argument("--ignore_title", action="store_true", default=False, help="ignore title and date in config")
    args = parser.parse_args()

    TOTAL_GEN_AUDIO_FILES = 0

    CHUNK_SIZE = 512  # size of chunks to write to file / download
    url_nathan = f"https://api.elevenlabs.io/v1/text-to-speech/{args.elelabs_voice}"
    # url_newsread = "https://api.elevenlabs.io/v1/text-to-speech/frqJk20JrduLkgUgHtMR"

    API_KEY = os.getenv("ELELABS_API_KEY")
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": API_KEY,  # "c23b31aabf009cb93c8feb5f4ddedc85", this isn't a valid API key
    }

    # Uncomment for higher bitrate (larger files)
    # querystring = {"output_format":"mp3_44100_192"}
    querystring = {}

    # load yml file at args.input + config.yml
    with open(args.input + "config.yml", "r") as f:
        config = yaml.load(f, Loader=yaml.FullLoader)

    # audio_config for 11labs, can change these
    payload = {
        "model_id": "eleven_multilingual_v2",
        # "voice_settings": {"similarity_boost": 0.75,
        # "stability": 0.50,
        # "style": 0.05,
        # "use_speaker_boost": True}, # orig settings
        "voice_settings": {
            "similarity_boost": 0.80,
            "stability": 0.45,
            "style": 0.05,
            "use_speaker_boost": True,
        },  # voice v2 settings
    }

    # create dir audio at args.input + audio
    audio_dir = args.input + "audio"
    if not os.path.exists(audio_dir):
        os.makedirs(audio_dir)

    first_gen = True
    skip_found = False
    section_titles = []
    fig_count = 1
    # iterate over config file that contains headings, text, and figures
    for idx, (heading, content) in tqdm(enumerate(config.items())):
        i = str(idx).zfill(2)
        if heading in ["md", "date"]:
            continue
        if not args.ignore_title:
            print(f"Generating audio for section {i}, {heading}")
            if len(args.start_heading) > 0:
                if heading == args.start_heading or skip_found:
                    if idx > 0:
                        first_gen = False
                    skip_found = True
                    pass
                else:
                    continue

            heading = strip_title(heading)

            # skip md file path and date
            section_titles.append(heading)

            if first_gen:
                # generate audio file for Title + date
                heading = heading + " was published on " + config["date"] + "."
                first_gen = False

            payload["text"] = heading
            # generate audio for heading

            fname = f"{audio_dir}/audio_{i}_0.mp3"
            request_audio(url_nathan, payload, headers, querystring, fname)
            TOTAL_GEN_AUDIO_FILES += 1

        # iterate over list of dicts in content and
        for para in content:
            idx = para["index"]
            # convert IDX to 2 digit string
            idx = str(idx).zfill(2)

            # if para is dict, prepare special audio to indicate figure
            if isinstance(para["content"], dict):
                fig_count_str = str(fig_count).zfill(2)
                # check if file source/repeat/figure_{fig_count_str}.mp3 exists, 
                # if so copy it to audio_dir with naming scheme
                if os.path.exists(f"source/repeat/figure_{fig_count_str}.mp3"):
                    os.system(f"cp source/repeat/figure_{fig_count_str}.mp3 {audio_dir}/audio_{i}_{idx}.mp3")

                # else generate the audio with index
                else:
                    payload["text"] = f"See figure {fig_count}"
                    fname = f"source/repeat/figure_{fig_count_str}.mp3"
                    request_audio(url_nathan, payload, headers, querystring, fname)
                    # copy fname to audio dir f"{audio_dir}/audio_{i}_{idx}.mp3"
                    os.system(f"cp {fname} {audio_dir}/audio_{i}_{idx}.mp3")

                TOTAL_GEN_AUDIO_FILES += 1
                fig_count += 1

            # if para is str, generate audio
            elif isinstance(para["content"], str):
                payload["text"] = para["content"]
                fname = f"{audio_dir}/audio_{i}_{idx}.mp3"
                request_audio(url_nathan, payload, headers, querystring, fname)
                TOTAL_GEN_AUDIO_FILES += 1
            else:
                print("Config Error: para is neither dict nor str")

    # concatenate all files in audio_dir with ffmpeg into input dir

    # if file generated_audio.mp3 already exists, delete it (prevent infinite loop)
    if os.path.exists(audio_dir + "/" + args.output + ".mp3"):
        os.remove(audio_dir + "/" + args.output + ".mp3")
    if os.path.exists(audio_dir + "/" + args.output + "_podcast" + ".mp3"):
        os.remove(audio_dir + "/" + args.output + "_podcast" + ".mp3")

    # list mp3 files in audio_dir
    audio_files_short = [audio_dir + "/" + f for f in os.listdir(audio_dir) if f.endswith((".mp3"))]
    audio_files = sorted(audio_files_short)

    # output_files = [f"{audio_dir}/audio_{i}.mp3" for i in range(0, TOTAL_GEN_AUDIO_FILES)]
    print(f"Sorted audio files {audio_files}")

    # [OPTIONAL] add source/repeat/farewell.mp3 to end of list (here to not mess with later code)
    # only do this if the farewell audio exists
    if os.path.exists(args.farewell_audio):
        audio_files.append(args.farewell_audio)

    subprocess.run(
        ["ffmpeg", "-i", "concat:" + "|".join(audio_files), "-c", "copy", audio_dir + "/" + args.output + ".mp3"]
    )

    # TODO remove all acronyms and other filtering, some that are bad are SOTA and MoE
    # TODO add seperate voice for quotes / quote detection

    # Get length of the sections and print in podcast format
    # get indicies in between first set of _ (e.g. audio_N_Y.mp3, get unique Ns)
    sections = np.unique([s.split("_")[1] for s in audio_files_short])
    sections = [str(s) for s in sections]

    def print_if_hour(seconds, total_len):
        if total_len > 3600:
            return str(timedelta(seconds=seconds))
        elif total_len < 600:
            return str(timedelta(seconds=seconds))[3:]
        else:
            return str(timedelta(seconds=seconds))[2:]

    # TODO make below work for multiple figures :/
    # iterate over headings for chapters, take first figure per section
    files_list_of_lists = []
    for s in sections:
        files = [f for f in audio_files_short if f.split("_")[1] == s]
        files_list_of_lists.append(files)
    section_lens = [get_cumulative_length(list_l) for list_l in files_list_of_lists]
    total_len = sum(section_lens)

    print(f"Cumulative length of all audio files: {section_lens} seconds")
    print("----------------------------------")
    print("Printing chapter times:")
    print("----------------------------------")

    print(section_titles[0])
    print(next(iter(config.values()))[0]["content"])
    print("This is AI generated audio with Python and 11Labs")
    print("Source code: https://github.com/natolambert/interconnects-tools")
    print("Original post: TODO")
    print()
    cur_len = 0
    for section_title, section_len in zip(section_titles, section_lens):
        print(f"{print_if_hour(floor(cur_len), total_len)} {section_title}")
        cur_len += section_len
