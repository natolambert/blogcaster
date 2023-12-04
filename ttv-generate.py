from openai import OpenAI
import argparse
# from tqdm import tqdm
from multiprocessing import Pool, current_process
import requests
import time 

SYSTEM_PROMPT = "The following instructions are text taken from a blog post on AI and ML, please create pretty images to accompany an audio version of this post: \n\n"
client = OpenAI()

def get_image(idx, string):
    # pidx = current_process()
    prompt = SYSTEM_PROMPT + string
    # truncate too long of prompts (4000 is limit)
    if len(prompt) > 4000:
        prompt = prompt[:4000]
        
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
    with open(f"images/temp-{idx}.png", 'wb') as file:
        file.write(image_response.content)
        
    time.sleep(20)

if __name__ == "__main__":
    # import argparse and define txt file path and output path
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=str, help="input text file path")
    parser.add_argument("--outputs", type=str, default="images/", help="output path for created images")
    args = parser.parse_args()

    # Replace 'your_long_text_document_here' with the actual text document
    long_text_document = """
    Your long text document goes here.
    It can have multiple paragraphs.
    Each paragraph should be separated by two newlines.
    """
    
    # read input
    with open(args.input, "r") as f:
        data = f.read()
        
    def split_string_into_segments(text, paragraphs_per_segment=2):
        paragraphs = text.split('\n\n')  # Assuming paragraphs are separated by two newline characters
        segments = [paragraphs[i:i + paragraphs_per_segment] for i in range(0, len(paragraphs), paragraphs_per_segment)]
        
        result_segments = ['\n\n'.join(segment) for segment in segments]
        
        return result_segments

        
    # Split the text into substrings of max length 5000 without splitting words
    substrings = split_string_into_segments(data)

    # alternate loop
    # for i, substring in tqdm(enumerate(substrings, start=1), desc="Processing substrings", unit="substring"):

    with Pool(processes=3) as pool:
        pool.starmap(get_image, enumerate(substrings))
        
        

        
        
