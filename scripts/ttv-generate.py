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
    "Please create elegant, and awesome images: \n\n"
)

SYSTEM_PROMPT_STLYE = (
    "Please draw art, or an artistic diagram, to accompany this summary or short snippet."
    "Filled from edge to edge with vibrant art, white base, with sky blue coloring (some light grey) "
    "and be in the style of 3blue1brown videos or educational animations. A little flashy. "
    "It's about AI, so visualize intelligence, feedback, and the future. \n\n"
)

# from OpenAI docs
# https://platform.openai.com/docs/guides/images/usage?context=node
REWRITE_OVERRIDE = (
    "I NEED to test how the tool works with extremely simple prompts. DO NOT add any detail, just use it AS-IS:"
)

client = OpenAI()


def summarize_text(text):
    """
    Tool to mitigate randomness of generations. Used when text length > 250 characters.
    """
    response = client.chat.completions.create(
        model="gpt-4o-2024-05-13",
        messages=[
            {
                "role": "system",
                "content": "Summarize content you are provided in two descriptive sentences that will be used to effectively prompt DALLE 3 for text-to-image generation.",  # noqa
            },
            {"role": "user", "content": text},
        ],
        temperature=0.7,
        max_tokens=64,
        top_p=1,
    )

    return response.choices[0].message.content


def strip_title(string):
    """
    Config entry, as dicts, keep track of titles as N_title goes here.
    Return the text after the _
    """
    if "_" in string:
        return string.split("_")[1]
    else:
        return string


def get_image(idx, inputs, vivid=True, hd=True, rewrite=True, no_sleep=False):
    """
    Default selections tested for style consistency and quality.
    """
    string, title = inputs  # unpack inputs

    style = "vivid" if vivid else "natural"
    quality = "hd" if hd else "standard"

    # when figures exist, do not generate (string is None)
    if string is None:
        return

    if len(string) > 250:
        string = summarize_text(string)
    elif len(string) < 50 and idx > 0:
        string += f"\n For context, the title of this post is {title}"
    prompt = SYSTEM_PROMPT_STLYE + string

    if not rewrite:
        prompt = REWRITE_OVERRIDE + prompt

    try:
        # call DALLE 3
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1792x1024",
            quality=quality,  # hd for higher quality
            style=style,  # vivid for more extreme
            n=1,
        )

        image_url = response.data[0].url
        image_response = requests.get(image_url)

        # Save the image to a local file
        idx = str(idx).zfill(3)
        with open(f"temp-images/img_{idx}.png", "wb") as file:
            file.write(image_response.content)
    except Exception as e:
        print(f"Idx: {idx}, Error: {e}")

    if not no_sleep:
        time.sleep(20)  # 20/23 sec was rate limit erroring


if __name__ == "__main__":
    # import argparse and define txt file path and output path
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=str, required=True, help="input text file dir")
    parser.add_argument("--do_not_gen", action="store_true", default=False, help="only download images")
    parser.add_argument("--start_idx", type=int, default=0, help="start index for generation")
    args = parser.parse_args()

    # load yml file at args.input + config.yml
    with open(args.input + "config.yml", "r") as f:
        config = yaml.load(f, Loader=yaml.FullLoader)

    # if images subdir doesn't exist, created it
    if not os.path.exists(args.input + "images"):
        os.makedirs(args.input + "images")

    prompts = []
    heading_count = 0
    first_gen = True
    # iterate over yaml file, record text per paragraph in string, don't create images for figures
    for i, (heading, content) in tqdm(enumerate(config.items())):
        heading_count += 1
        heading = strip_title(heading)
        # skip md file path and date
        if heading in ["md", "date"]:
            continue

        if first_gen:
            # generate audio file for Title + date
            if config["date"] is None:
                heading = heading + " by Nathan Lambert."
            else:
                heading = heading + " was published on " + config["date"] + "."
            first_gen = False

        prompts.append(heading)

        # iterate over list of dicts in content and
        for para in content:
            # if para is dict, do nothing
            if isinstance(para["content"], dict):
                prompts.append(None)  # for keeping track of index

            # if para is str, generate audio
            elif isinstance(para["content"], str):
                prompts.append(para["content"])
            else:
                print("Config Error: para is neither dict nor str")

    # if temp-images dir doesn't exist, make it
    if not os.path.exists("temp-images"):
        os.makedirs("temp-images")

    title = prompts[0]
    title = [title for _ in range(len(prompts))]
    # if --do_not_gen, do not do this
    if not args.do_not_gen:
        with Pool(processes=3) as pool:
            # enumerate based on start index
            pool.starmap(
                get_image, enumerate(zip(prompts[args.start_idx :], title[args.start_idx :]), start=args.start_idx)
            )

        # move all images from temp-images to args.input/images
        os.system(f"mv temp-images/* {args.input}images")
