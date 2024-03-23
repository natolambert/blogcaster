# Please shoot me a message, open an issue, or comment on Interconnects if you're using this code! I'd love to know.

import argparse
import os
import re
import subprocess
from datetime import timedelta
from math import floor

import numpy as np
import requests
import yaml
from pydub import AudioSegment
from tqdm import tqdm

# todo implement elevenlabs
# from elevenlabs import save, generate
# from elevenlabs.client import ElevenLabs
# ELE_TOKEN = os.environ["ELELABS_API_KEY"]
# client = ElevenLabs(
#   api_key=ELE_TOKEN, # Defaults to ELEVEN_API_KEY
# )
# client.generate


def is_ffmpeg_normalize_runnable():
    # Check operating system
    if os.name == "posix":  # Unix-like OS
        cmd = ["which", "ffmpeg-normalize"]
    elif os.name == "nt":  # Windows
        cmd = ["where", "ffmpeg-normalize"]
    else:
        return False  # Unsupported OS

    try:
        # Run the command
        subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        return True  # Command succeeded
    except subprocess.CalledProcessError:
        return False  # Command failed


def strip_title(string):
    """
    Config entry, as dicts, keep track of titles as N_title goes here.
    Return the text after the _
    """
    if "_" in string:
        return string.split("_")[1]
    else:
        return string


def get_cumulative_length(file_list, offset: float = 0.0):
    cumulative_length = 0
    for filename in file_list:
        # filepath = os.path.join(directory, filename)
        audio = AudioSegment.from_file(filename)
        cumulative_length += len(audio)
    if offset:
        cumulative_length += offset

    return cumulative_length / 1000.0  # Convert to seconds


def get_11labs_audio(url, payload, headers, querystring, filename, per_sentence=False):
    pass


def request_audio(url, payload, headers, querystring, filename, per_sentence=False):
    """
    A function to replace the following code:
    response = requests.post(url_nathan, json=payload, headers=headers, params=querystring)
    with open(f"{args.output}_part{i}.mp3", 'wb') as part_file:
        for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
            if chunk:
                part_file.write(chunk)
    """

    # check if audio_boost in payload, if so remove it and grab the variable
    if "audio_boost" in payload:
        audio_boost = payload["audio_boost"]
        del payload["audio_boost"]
    else:
        audio_boost = 0.0

    if not os.path.exists(filename):
        try:
            full_text = payload["text"]
            # iterate over sentence in text, and create file
            if per_sentence:
                with open(filename, "wb") as part_file:
                    for sentence in re.split("[?.!]", full_text):
                        if len(sentence) > 0 and sentence not in [" ", ".", "!", "?"]:  # skip empty sentences
                            if sentence[0] == " ":  # remove leading space
                                sentence = sentence[1:]
                            payload["text"] = sentence + "."  # add period back
                            print("-> audio request send to 11labs")
                            try:
                                response = requests.post(url, json=payload, headers=headers, params=querystring)
                                for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                                    if chunk:
                                        part_file.write(chunk)
                            except Exception as e:
                                print(f"Error: {e}")
            else:
                print("-> audio request send to 11labs")
                payload["text"] = full_text
                try:
                    response = requests.post(url, json=payload, headers=headers, params=querystring)
                    with open(filename, "wb") as part_file:
                        for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                            if chunk:
                                part_file.write(chunk)
                except Exception as e:
                    print(f"Error: {e}")

        except Exception as e:
            print(f"Error: {e}")

        # boost volume if included with ffmpeg
        if audio_boost > 0:
            print(f"-> boosting audio file {filename}")
            subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-i",
                    filename,
                    "-af",
                    f"'volume={audio_boost}'",
                    "temp.mp3",
                ]
            )

            # move temp to filename with overwrite
            os.system(f"mv temp.mp3 {filename}")

    else:
        print(f"-> audio file {filename} already exists, skipping request")


if __name__ == "__main__":
    # import argparse and define txt file path and output path
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=str, required=True, help="input directory to work with")
    parser.add_argument("--output", type=str, default="generated_audio", help="output mp3 file path")
    parser.add_argument(
        "--elelabs_voice", type=str, default="kR0divO0lqMjNIyZ85Am", help="11labs voice id"
    )  # previous version WerIBRrBvioo2do7d1qq
    parser.add_argument("--elelabs_voice_alt", type=str, default="nH0VmfcJAjdwUZ3yUYTf", help="11labs voice id")
    parser.add_argument("--start_heading", type=str, default="", help="start at section named in generation")
    parser.add_argument("--farewell_audio", type=str, default="source/repeat/farewell.mp3", help="farewell audio path")
    parser.add_argument(
        "--ignore_title",
        action="store_true",
        default=False,
        help="ignore title and date in config (for research video example)",
    )
    parser.add_argument("--per_sentence", action="store_true", default=False, help="generate audio per sentence")
    parser.add_argument("--section_music", action="store_true", default=False, help="use section music")
    parser.add_argument("--use_quote_voice", action="store_true", default=False, help="use quote voice")
    parser.add_argument(
        "--boost", type=float, default=0.0, help="audio boost for quiet 11labs voices (core voice only, not quotes)"
    )
    args = parser.parse_args()
    per_sentence = args.per_sentence

    CHUNK_SIZE = 512  # size of chunks to write to file / download
    url_nathan = f"https://api.elevenlabs.io/v1/text-to-speech/{args.elelabs_voice}"
    url_newsread = f"https://api.elevenlabs.io/v1/text-to-speech/{args.elelabs_voice_alt}"

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
        # for quick fine-tunes
        # "model_id": "eleven_multilingual_v2",
        # "voice_settings": {
        #     "similarity_boost": 0.75,
        #     "stability": 0.45,
        #     "style": 0.05,
        #     "use_speaker_boost": True,
        # },
        # for PVC
        "model_id": "eleven_turbo_v2",
        "voice_settings": {
            "similarity_boost": 0.6,
            "stability": 0.45,
        },
    }
    if args.boost > 0:
        payload["audio_boost"] = args.boost

    if args.use_quote_voice:
        payload_quote = {
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "similarity_boost": 0.66,
                "stability": 0.55,
                "style": 0.00,
                "use_speaker_boost": True,
            },
        }
    else:
        payload_quote = payload
        url_newsread = url_nathan

    # create dir audio at args.input + audio
    audio_dir = args.input + "audio"
    if not os.path.exists(audio_dir):
        os.makedirs(audio_dir)

    first_gen = True
    skip_found = False
    section_titles = []
    fig_count = 1
    section_audios = []

    # iterate over config file that contains headings, text, and figures
    for sec_idx, (heading, content) in tqdm(enumerate(config.items())):
        i = str(sec_idx).zfill(2)
        if heading in ["md", "date"]:
            continue

        section_files = []
        if not args.ignore_title:
            print(f"Generating audio for section {i}, {heading}")
            if len(args.start_heading) > 0:
                if heading == args.start_heading or skip_found:
                    if sec_idx > 0:
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
                if config["date"] is not None:
                    heading = heading + " was published on " + config["date"] + "."
                    first_gen = False
            else:
                # articial pause
                # heading = '- -' + heading
                pass

            payload["text"] = heading
            # generate audio for heading

            fname = f"{audio_dir}/audio_{i}_00.mp3"
            request_audio(url_nathan, payload, headers, querystring, fname, per_sentence)
            section_files.append(fname)

        # iterate over list of dicts in content and
        for para in content:
            idx = para["index"]
            # convert IDX to 2 digit string
            idx = str(idx).zfill(2)

            # if para is dict, prepare special audio to indicate figure
            if isinstance(para["content"], dict):
                # check if dir source/repeat/ exists, if not create it
                if not os.path.exists("source/repeat"):
                    os.makedirs("source/repeat")

                fig_count_str = str(fig_count).zfill(2)
                # check if file source/repeat/figure_{fig_count_str}.mp3 exists,
                # if so copy it to audio_dir with naming scheme
                if os.path.exists(f"source/repeat/figure_{fig_count_str}.mp3"):
                    os.system(f"cp source/repeat/figure_{fig_count_str}.mp3 {audio_dir}/audio_{i}_{idx}.mp3")
                    fname = f"{audio_dir}/audio_{i}_{idx}.mp3"  # for merging ( see below )

                # else generate the audio with index
                else:
                    payload["text"] = f"See figure {fig_count}"
                    fname = f"source/repeat/figure_{fig_count_str}.mp3"
                    request_audio(url_nathan, payload, headers, querystring, fname, per_sentence)
                    # copy fname to audio dir f"{audio_dir}/audio_{i}_{idx}.mp3"
                    os.system(f"cp {fname} {audio_dir}/audio_{i}_{idx}.mp3")

                fig_count += 1

            # if para is str, generate audio
            elif isinstance(para["content"], str):
                fname = f"{audio_dir}/audio_{i}_{idx}.mp3"
                # if payload["text"] contains starts with >, use different voice
                if para["content"].startswith(">"):
                    payload_quote["text"] = para["content"]
                    request_audio(url_newsread, payload_quote, headers, querystring, fname, per_sentence)
                else:
                    payload["text"] = para["content"]
                    request_audio(url_nathan, payload, headers, querystring, fname, per_sentence)
            else:
                print("Config Error: para is neither dict nor str")

            section_files.append(fname)
        section_audios.append(section_files)
    # concatenate all files in audio_dir with ffmpeg into input dir

    # if file generated_audio.mp3 already exists, delete it (prevent infinite loop)
    if os.path.exists(audio_dir + "/" + args.output + ".mp3"):
        os.remove(audio_dir + "/" + args.output + ".mp3")
    if os.path.exists(audio_dir + "/" + args.output + "_podcast" + ".mp3"):
        os.remove(audio_dir + "/" + args.output + "_podcast" + ".mp3")

    # list mp3 files in audio_dir
    audio_files_short = [audio_dir + "/" + f for f in os.listdir(audio_dir) if f.endswith((".mp3"))]
    audio_files = sorted(audio_files_short)

    print(f"Sorted audio files {audio_files}")

    # [OPTIONAL] add source/repeat/farewell.mp3 to end of list (here to not mess with later code)
    # only do this if the farewell audio exists
    if os.path.exists(args.farewell_audio):
        audio_files.append(args.farewell_audio)

    if args.section_music:
        print("----------------------------------")
        print("Merging with section music:")
        print("----------------------------------")
        # if transition audio exists, do fancy crossfade and merge
        music_path = "source/repeat/transition-mono-v2.mp3"
        if os.path.exists(music_path):
            offset_duration = True
            if os.path.exists(args.farewell_audio):
                section_audios[-1].append(args.farewell_audio)

            # First concatenate all the sections (based on config) into files per section
            # concatenate section audios into section files
            for s, section_files in enumerate(section_audios):
                s_str = str(s)
                subprocess.run(
                    [
                        "ffmpeg",
                        "-y",
                        "-i",
                        "concat:" + "|".join(section_files),
                        "-c",
                        "copy",
                        audio_dir + "/" + args.output + "_sec_" + s_str + ".mp3",
                    ]
                )

            # get the list of section audios (all with _sec_) in it
            audio_chunks = sorted([f for f in audio_files_short if "_sec_" in f])

            # while there are files in audio_chunks, crossfade a music item to it,
            # then crossfade the next chunk to it, then append the last one
            output_path = "experiment.mp3"
            output_path_tmp = "experiment_tmp.mp3"
            did_music_last = False

            # transitioning to merging rather than crossfade, see:
            # https://superuser.com/questions/1509582/ffmpeg-merge-two-audio-file-with-defined-overlapping-time
            while len(audio_chunks) > 1:
                # get the first two files in the list
                first = audio_chunks.pop(0)

                # "-y", overwrites the output file
                if not did_music_last:
                    second = music_path
                    d = 1
                    did_music_last = True

                    # crossfade the first two files
                    subprocess.run(
                        [
                            "ffmpeg",
                            "-y",
                            "-i",
                            first,
                            "-i",
                            second,
                            "-filter_complex",
                            f"acrossfade=d={d}:c1=tri:c2=tri",
                            output_path,
                        ]
                    )
                else:
                    # fade the first file (the music ending)
                    subprocess.run(["ffmpeg", "-y", "-i", first, "-af", "afade=t=out:st=0:d=1", output_path_tmp])
                    second = audio_chunks.pop(0)
                    # Concatentate the first file and the second ( no crossfade )
                    subprocess.run(
                        [
                            "ffmpeg",
                            "-y",
                            "-i",
                            output_path_tmp,
                            "-i",
                            second,
                            "-filter_complex",
                            "concat=n=2:v=0:a=1",
                            output_path,
                        ]
                    )
                    did_music_last = False  # redundant

                # copy expertment to experiment_copy to avoid file overwriting
                os.system("cp experiment.mp3 experiment_tmp.mp3")

                # prepend the output to the list (it's the beginnging audio)
                audio_chunks.insert(0, output_path_tmp)
                print(audio_chunks)

            # move experiment to output + generated_audio.mp3
            # os.system(f"mv {output_path} {audio_dir}/{args.output}.mp3")

            # delete experiment and experiment_tmp
            # os.system("rm experiment_tmp.mp3")

    # else, keep the logic below
    else:
        print("----------------------------------")
        print("Basic concatenation:")
        print("----------------------------------")
        offset_duration = False
        subprocess.run(
            ["ffmpeg", "-i", "concat:" + "|".join(audio_files), "-c", "copy", audio_dir + "/" + args.output + ".mp3"]
        )

    # TODO remove all acronyms and other filtering, some that are bad are SOTA and MoE
    # TODO add seperate voice for quotes / quote detection
    # normalize audio file
    if is_ffmpeg_normalize_runnable():
        filename = audio_dir + "/" + args.output + ".mp3"
        print(f"-> normalizing audio file {filename}")
        # default bitrate 128K and sample rate 44100 for 11labs, change if needed
        subprocess.run(
            [
                "ffmpeg-normalize",
                filename,
                "-o",
                filename,
                "-f",
                "-c:a",
                "libmp3lame",
                "-b:a",
                "128K",
                "-ar",
                "44100",
                "--target-level",
                "-20",  # in DB, normally before was about -24
            ]
        )

    # if _sec_ in file in audio_files_short, remove it
    audio_files_short = [f for f in audio_files_short if "_sec_" not in f]

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

    offset = len(AudioSegment.from_file(music_path)) - 1000 if offset_duration else 0  # if using crossfade

    for s in sections:
        files = [f for f in audio_files_short if f.split("_")[1] == s]
        files_list_of_lists.append(files)
    section_lens = [get_cumulative_length(list_l, offset=offset) for list_l in files_list_of_lists]
    total_len = sum(section_lens)

    print("----------------------------------")
    print(f"Cumulative length of all audio files: {section_lens} seconds")
    print(f"Saving show notes to {args.input}notes.txt")
    print("----------------------------------")

    with open(args.input + "notes.txt", "w") as file:
        # Writing the first section title and the first config content
        file.write(section_titles[0] + "\n")
        file.write(next(iter(config.values()))[0]["content"] + "\n")
        file.write("This is AI generated audio with Python and 11Labs.\n")
        file.write("Source code: https://github.com/natolambert/interconnects-tools\n")
        file.write("Original post: [INSERT URL HERE]\n")
        file.write("\n")

        cur_len = 0
        for section_title, section_lens in zip(section_titles, section_lens):
            # Assuming print_if_hour is a function you've defined elsewhere
            file.write(f"{print_if_hour(floor(cur_len), total_len)} {section_title}\n")
            cur_len += section_lens
