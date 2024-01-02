# Please shoot me a message, open an issue, or comment on Interconnects if you're using this code! I'd love to know.

import argparse
import os
import time
from multiprocessing import Pool

import requests
import yaml
from openai import OpenAI
from tqdm import tqdm

SYSTEM_PROMPT = (
    "The following instructions are text taken from a blog post on AI and ML,"
    "please create pretty images to accompany an audio version of this post: \n\n"
)
client = OpenAI()


def strip_title(string):
    """
    Config entry, as dicts, keep track of titles as N_title goes here.
    Return the text after the _
    """
    if "_" in string:
        return string.split("_")[1]
    else:
        return string



def get_image(idx, string):
    # when figures exist, do not generate (string is None)
    if string is None:
        return

    prompt = SYSTEM_PROMPT + string
    # truncate too long of prompts (4000 is limit)
    if len(prompt) > 4000:
        prompt = prompt[:4000]

    try:
        # call DALLE 3
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1792x1024",
            quality="standard",
            n=1,
        )
        # print(f'Response code: {response.status_code}')
        image_url = response.data[0].url
        image_response = requests.get(image_url)

        # Save the image to a local file
        idx = str(idx).zfill(3)
        with open(f"temp-images/img_{idx}.png", "wb") as file:
            file.write(image_response.content)
    except Exception as e:
        print(f"Error: {e}")

    time.sleep(23)  # 20sec was rate limit erroring


if __name__ == "__main__":
    # import argparse and define txt file path and output path
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=str, help="input text file dir")
    args = parser.parse_args()

    # read input
    # with open(args.input, "r") as f:
    #     data = f.read()

    # load yml file at args.input + config.yml
    with open(args.input + "config.yml", "r") as f:
        config = yaml.load(f, Loader=yaml.FullLoader)

    prompts = []
    first_gen = True
    # iterate over yaml file, record text per paragraph in string, don't create images for figures
    for i, (heading, content) in tqdm(enumerate(config.items())):
        heading = strip_title(heading)
        # skip md file path and date
        if heading in ["md", "date"]:
            continue

        if first_gen:
            # generate audio file for Title + date
            heading = heading + " was published on " + config["date"] + "."
            first_gen = False

        prompts.append(heading)
        # TODO if prompt is less than a certain length, merge with previous?

        # iterate over list of dicts in content and
        for para in content:
            # if para is dict, do nothing
            if isinstance(para["content"], dict):
                # copy png from source to gen-images, rename with appropriate idx
                idx = str(para["index"]).zfill(3)
                path = para["content"]["path"]
                # move to args.input + gen-images as name img_{idx}.png
                os.system(f"cp {args.input}{path} {args.input}images/img_{idx}.png")
                prompts.append(None)  # for keeping track of index

            # if para is str, generate audio
            elif isinstance(para["content"], str):
                prompts.append(para["content"])
            else:
                print("Config Error: para is neither dict nor str")

    with Pool(processes=3) as pool:
        pool.starmap(get_image, enumerate(prompts))

    # move all images from temp-images to args.input/images
    os.system(f"mv temp-images/* {args.input}images")
