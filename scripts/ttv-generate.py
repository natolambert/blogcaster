# Please shoot me a message, open an issue, or comment on Interconnects if you're using this code! I'd love to know.

import argparse
import os
import time
from multiprocessing import Pool

import requests
import yaml
from huggingface_hub import HfApi
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
            quality="hd",
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
    parser.add_argument("--input", type=str, required=True, help="input text file dir")
    parser.add_argument("--do_not_gen", action="store_true", default=False, help="only download images")
    parser.add_argument("--hf_fig_dir", type=str, default=None, help="directory with images for figures")
    args = parser.parse_args()
    hf_dataset = args.hf_fig_dir

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
            heading = heading + " was published on " + config["date"] + "."
            first_gen = False

        prompts.append(heading)
        # TODO if prompt is less than a certain length, merge with previous?

        # iterate over list of dicts in content and
        for para in content:
            # if para is dict, do nothing
            if isinstance(para["content"], dict):
                # copy png from source to gen-images, rename with appropriate idx
                idx = str(len(prompts)).zfill(3)
                path = para["content"]["path"]
                img_type = path.split(".")[-1]  # one of png, jpg, jpeg, webp

                # if path is url, download to img_{idx}.png with curl
                if path.startswith("http"):
                    # TODO debug this again
                    # download image with correct type
                    # os.system(f"curl {path} -o {args.input}images/img_{idx}.png")
                    os.system(f"curl {path} -o {args.input}images/img_{idx}.{img_type}")

                # else move to args.input + gen-images as name img_{idx}.png
                else:
                    os.system(f"cp {args.input}{path} {args.input}images/img_{idx}.{img_type}")
                prompts.append(None)  # for keeping track of index

            # if para is str, generate audio
            elif isinstance(para["content"], str):
                prompts.append(para["content"])
            else:
                print("Config Error: para is neither dict nor str")

    # before starting generation, upload the local images (those already) to the
    if hf_dataset:
        # get hf token from HF_TOKEN
        HF_TOKEN = os.environ["HF_TOKEN"]
        api = HfApi(token=HF_TOKEN)

        # path is input + images/
        # repo_path is just the post name (what follows source in input path, after / )
        # repo_id is hf_dataset
        path = args.input + "images/"
        repo_path = args.input.split("/")[-2]
        api.upload_folder(
            folder_path=path,
            path_in_repo=repo_path,
            repo_id=hf_dataset,
            repo_type="dataset",
        )

        # iterate through figures in images, and print "Figure {N}: {clickable link on hf}"
        # example link
        # https://huggingface.co/datasets/natolambert/interconnects-figures/resolve/main/test-post/img_003.png
        print("Podcast figures:")
        for i, fig in enumerate(os.listdir(path)):
            print(f"Figure {i}: https://huggingface.co/datasets/{hf_dataset}/resolve/main/{repo_path}/{fig}")

    # if --do_not_gen, do not do this
    if not args.do_not_gen:
        with Pool(processes=3) as pool:
            pool.starmap(get_image, enumerate(prompts))

        # move all images from temp-images to args.input/images
        os.system(f"mv temp-images/* {args.input}images")
