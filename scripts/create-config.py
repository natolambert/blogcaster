# Please shoot me a message, open an issue, or comment on Interconnects if you're using this code! I'd love to know.

import argparse
import os
import re
from urllib.parse import unquote

import unidecode
import yaml
from huggingface_hub import HfApi
from openai import OpenAI

client = OpenAI()


SYSTEM_PROMPT = (
    "Please perform the following task: translate the input into written word so a text-to-speech model can read it (things like fractions don't work well).\n\n"  # noqa
    "Examples include 1/4 to one quarter, 20-30 to twenty to thirty, or $1.5m to one point five million dollars. Most dollar signs should be converted. When given a sentence, just replace those."  # noqa
)

AUDIO_FIXES = {
    "\n": " ",
    ">": "",
    "**": "",
    "*": "",
    "~": "approximately ",  # for numbers
    " | ": " ",
    "\\ ": " ",
    "e.g.": "e g",
    "i.e.": "i e",
    "w.r.t.": "with respect to",
    '."': '".',
    "3.5": "3 point 5",
    "4.5": "4 point 5",
    "8x22B": "8 by 22 B",
    "8x7B": "8 by 7 B",
    "MoE": "M O E",
    "LLaVA": "llava",
    "do-or-die": "do or die",
    "LLM-as-a-judge": "LLM as a judge",
    "LMSYS": "L M sys",
    " (RLHF)": "",
    "Jan.": "January",
    "Feb.": "February",
    "Mar.": "March",
    "Apr.": "April",
    "Jun.": "June",
    "Jul.": "July",
    "Aug.": "August",
    "Sep.": "September",
    "Sept.": "September",
    "Oct.": "October",
    "Nov.": "November",
    "Dec.": "December",
    "Anon. ": "Anonymous ",
    "readme": "read me",  # for discussing code
    "README": "read me",
    "Q*": "Q star",
    "MW": "mega watt",
    "GW": "giga watt",
    # "Arxiv ": "Archive ",
    # "arxiv ": "Archive ",
    # "arXiv ": "Archive "
}


def replace_all(text):
    for old, new in AUDIO_FIXES.items():
        text = text.replace(old, new)
    return text


def prep_for_tts(text):
    """
    Rephrases challenging formats for TTS models.

    E.g. $1/4m -> one quarter million dollars

    Logic will be to look for the following symbols in text: $, /, x, . (without a space after it)
    Note: generate with 0 temperature for these :)
    """
    response = client.chat.completions.create(
        model="gpt-4o-2024-05-13",
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {"role": "user", "content": text},
        ],
        temperature=0.0,
        max_tokens=256,
        top_p=1,
    )
    return response.choices[0].message.content


def contains_decimal_number(s):
    # This regex pattern matches an optional sign (+ or -), followed by zero or more digits (\d*),
    # a decimal point (\.), and one or more digits (\d+).
    # The pattern also handles cases where there might be digits before the decimal point.
    pattern = re.compile(r"-?\d*\.\d+")
    return bool(pattern.search(s))


def has_nx_pattern(s):
    return bool(re.search(r"\d+(\.\d+)?x", s))


def has_range_pattern(s):
    return bool(re.search(r"\b\d+\s*-\s*\d+\b", s))


# create argparse function that takes in a directory (for later creating a yml file)
def get_args():
    parser = argparse.ArgumentParser()
    # only one argument so doesn't need a tag
    parser.add_argument("directory", type=str, help="input directory path")
    # add date to be published
    parser.add_argument("--date", type=str, help="date to be published")
    parser.add_argument(
        "--hf_fig_dir", type=str, default="natolambert/interconnects-figures", help="directory with images for figures"
    )
    parser.add_argument("--use_imgur", action="store_true", default=False, help="use imgur to upload images")
    args = parser.parse_args()
    return args


def find_markdown_and_directories(directory):
    """
    Find a markdown file in the specified directory, ensure 'images' directory exists,
    and list one other directory if available.

    Args:
    directory (str): The directory to search in.

    Returns:
    tuple: A tuple containing the filename of a markdown file, the 'images' directory path,
           and another directory path if available.
    """
    markdown_file = None
    figures_directory = None
    images_dir = os.path.join(directory, "images")

    # Ensure 'images' directory exists
    if not os.path.exists(images_dir):
        os.makedirs(images_dir)

    # Search for a markdown file and another directory (which holds figures)
    for entry in os.listdir(directory):
        full_path = os.path.join(directory, entry)
        if os.path.isdir(full_path) and entry != "images":
            figures_directory = full_path
        elif markdown_file is None and entry.lower().endswith(".md"):
            markdown_file = entry

        # If both are found, no need to continue
        if markdown_file and figures_directory:
            break

    return (markdown_file, images_dir, figures_directory)


def rename_spaces_to_underscores(path):
    if not os.path.exists(path):
        print(f"The path '{path}' does not exist.")
        return

    new_name = path.replace(" ", "_")
    os.rename(path, new_name)
    print(f"Renamed '{path}' to '{new_name}'")


def parse_markdown_to_dict(md_content, filename):
    """
    Parse markdown content and return a dictionary with sections, paragraphs, and figures.
    """
    sections = {}
    current_section = ""
    total_index = 0
    section_index = 0
    fig_indices = []

    for line in md_content.split("\n\n"):
        if line.startswith("---"):
            continue
        elif line.strip() == ">":
            continue
        elif line.startswith("#"):
            # New section
            current_section = unidecode.unidecode(re.sub(r"#+\s*", "", line).strip())
            sections[f"{str(section_index).zfill(2)}_" + current_section] = []
            section_index += 1
            total_index += 1
        elif line.strip():
            if line.strip().startswith("!["):
                # Figure found
                alt_text, img_path = re.findall(r"\[([^]]+)\]\(([^)]+)\)", line)[0]
                sections[f"{str(section_index - 1).zfill(2)}_" + current_section].append(
                    {"index": total_index, "content": {"alt_text": alt_text, "path": img_path}}
                )

                # save figures / move to correct folder
                # if path ends with png, jpeg, jpg, or webp, split on . and take last
                if img_path.endswith((".png", ".jpeg", ".jpg", ".webp", ".mp4")):
                    img_type = img_path.split(".")[-1]  # one of png, jpg, jpeg, webp
                # sometimes format=jpg or =png is included in the url, so split on = and take last
                elif "format=jpg" in img_path or "format=png" in img_path:
                    # split assuming it is the first = in the string
                    img_type = img_path.split("=")[-1][:3]
                else:
                    img_type = "png"

                dir = os.path.dirname(filename)
                # if img_path is url, download to img_{idx}.png with curl
                if img_path.startswith("http"):
                    # download image with correct type
                    os.system(f"curl {img_path} -o {dir}/images/img_{str(total_index).zfill(3)}.{img_type}")

                # else move to args.directory + gen-images as name img_{idx}.png
                else:
                    # extract path from filename
                    # import ipdb; ipdb.set_trace()
                    os.system(f"cp {dir}/{unquote(img_path)} {dir}/images/img_{str(total_index).zfill(3)}.{img_type}")

                # check that image exists, if not raise error
                if not os.path.exists(f"{dir}/images/img_{str(total_index).zfill(3)}.{img_type}"):
                    raise FileNotFoundError(
                        f"Image not found at {dir}/images/img_{str(total_index).zfill(3)}.{img_type}"
                    )
                fig_indices.append(total_index)
            else:
                # Regular paragraph
                text = line.strip()
                text = text.replace("\u2019", "'")

                # if text starts with >, remove it and add "Quote: " to the beginning and " End Quote." to the end
                if text.startswith(">"):
                    text = text[1:]
                    text = "I quote:" + text + " End Quote."

                # remove the urls from text. It's in [xyz](www) format, extract xyz
                text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
                text = replace_all(text)

                # rephrase text for TTS if symbols are present
                # if any of the following symbols are present in text, prep for TTS
                if (
                    any(symbol in text for symbol in ["$", "/"])
                    or contains_decimal_number(text)
                    or has_nx_pattern(text)
                    or has_range_pattern(text)
                ):
                    text = prep_for_tts(text)
                    print(f"Rewrote index {total_index} with AI for TTS formatting.")
                    # sometimes has bugs with commas,
                    if " , " in text:
                        text = text.replace(" , ", ", ")

                # remove :, -, and leading space from text
                text = text.replace(":", ",")
                text = text.replace("--", ",")  # simpler pause
                if text.startswith(" "):
                    text = text[1:]

                # if starts with '- ', remove it, from list
                if text.startswith("- "):
                    text = text[2:]

                # change trailing space and period to just period
                if text.endswith(" ."):
                    # change to period
                    text = text[:-2] + "."

                # remove trailing space
                if text.endswith(" "):
                    text = text[:-1]

                # Remove any () and everything inside them
                text = re.sub(r"\([^)]*\)", "", text)

                # decode
                text = unidecode.unidecode(text)

                sections[f"{str(section_index - 1).zfill(2)}_" + current_section].append(
                    {"index": total_index, "content": unidecode.unidecode(text)}
                )

            total_index += 1

    return sections


def read_markdown_file(filename):
    """
    Read markdown file and return its content.
    """
    with open(filename, "r") as file:
        return file.read()


def write_yaml_file(data, filename):
    """
    Write data to a YAML file.
    """
    with open(filename, "w") as file:
        yaml.dump(data, file)


def markdown_to_yaml(md_filename, yaml_filename, date):
    """
    Convert markdown file to YAML file.
    """
    md_content = read_markdown_file(md_filename)
    # print total number of characters in md_content
    print(f"INFO: Total number of characters in markdown file: {len(md_content)}")
    sections_dict = parse_markdown_to_dict(md_content, md_filename)

    # add markdown filename to dictionary
    sections_dict["md"] = md_filename
    sections_dict["date"] = date
    write_yaml_file(sections_dict, yaml_filename)


# def upload_images_imgur(directory_path, client_id):
#     headers = {"Authorization": f"Client-ID {client_id}"}
#     url = "https://api.imgur.com/3/upload"
#     uploaded_images_urls = []

#     for image_name in os.listdir(directory_path):
#         if image_name.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".bmp")):
#             image_path = os.path.join(directory_path, image_name)
#             with open(image_path, "rb") as image:
#                 payload = {"image": image}
#                 response = requests.post(url, headers=headers, files=payload)
#                 if response.status_code == 200:
#                     image_url = response.json()["data"]["link"]
#                     print(f"Image {image_name} uploaded successfully: {image_url}")
#                     uploaded_images_urls.append(image_url)
#                 else:
#                     print(f"Failed to upload image {image_name}. Status code: {response.status_code}")

#     return uploaded_images_urls


if __name__ == "__main__":
    args = get_args()
    markdown_file, images_dir, figures_directory = find_markdown_and_directories(args.directory)

    markdown_to_yaml(args.directory + markdown_file, args.directory + "config.yml", args.date)

    print(f"INFO: Created post config file at {args.directory + 'config.yml'}")

    path = args.directory + "images/"
    # if any images in path, execute
    if os.path.exists(path) and len(os.listdir(path)) > 0:
        # upload figures via huggingface
        if not args.use_imgur:
            # get hf token from HF_TOKEN
            HF_TOKEN = os.environ["HF_TOKEN"]
            api = HfApi(token=HF_TOKEN)

            # path is input + images/
            # repo_path is just the post name (what follows source in input path, after / )
            # repo_id is hf_dataset

            repo_path = args.directory.split("/")[-2]
            api.upload_folder(
                folder_path=path,
                path_in_repo=repo_path,
                repo_id=args.hf_fig_dir,
                repo_type="dataset",
            )

            img_urls = []
            for i, fig in enumerate(sorted(os.listdir(path))):
                # only print if corresponding index in prompts is None
                # strip number from last three digists img_NNN.png -> NNN
                fig_idx = int(fig.split("_")[-1].split(".")[0])
                img_urls.append(f"https://huggingface.co/datasets/{args.hf_fig_dir}/resolve/main/{repo_path}/{fig}")

        # leaving this commented if someone wants to give me a tutorial on using their API
        # else:  # upload via imgur
        #     img_urls = upload_images_imgur(args.directory + "images/")

        # Save URLs to a text file
        with open(args.directory + "figure_urls.txt", "w") as file:
            for i, url in enumerate(img_urls):
                file.write(f"Fig {i+1}: " + url + "\n")

        print(f"All image URLs have been saved to {args.directory}figure_urls.txt")
