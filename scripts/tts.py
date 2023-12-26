import requests
import argparse
import textwrap
from tqdm import tqdm
import subprocess

if __name__ == "__main__":
    # import argparse and define txt file path and output path
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=str, help="input text file path")
    parser.add_argument("--output", type=str, default="output", help="output mp3 file path")
    args = parser.parse_args()

    # example usage in comments for this python script tts.py
    # python tts.py --input raw/2023-29-11-synthetic.txt --output output.mp3

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

    with open(args.input, "r") as f:
        data = f.read()
        
    # Split the text into substrings of max length 2500 without splitting words
    substrings = textwrap.wrap(data, width=2500, break_long_words=False)

    # TODO remove all acronyms and other filtering, some that are bad are SOTA and MoE
    # TODO add seperate voice for quotes / quote detection
    # TODO make it so audio never clips a sentence
    # TODO shorten generation (volume can trail off)
    # TODO see image audio for figures
    
    for i, substring in tqdm(enumerate(substrings, start=1), desc="Processing substrings", unit="substring"):
        payload = {
            "model_id": "eleven_multilingual_v2",
            "text": substring,
            "voice_settings": {
                "similarity_boost": 0.75,
                "stability": 0.50,
                "style": 0.05,
                "use_speaker_boost": True
            }
        }

        response = requests.post(url_nathan, json=payload, headers=headers, params=querystring)
        with open(f"{args.output}_part{i}.mp3", 'wb') as part_file:
            for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                if chunk:
                    part_file.write(chunk)

    # Now, you need to concatenate all the parts into the final MP3 file
    output_files = [f"output_part{i}.mp3" for i in range(1, len(substrings) + 1)]
    subprocess.run(["ffmpeg", "-i", "concat:" + "|".join(output_files), "-c", "copy", args.output+".mp3"])

    # [OPTIONAL] Cleanup: Delete temporary part files
    # for part_file in output_files:
    #     subprocess.run(["rm", part_file])