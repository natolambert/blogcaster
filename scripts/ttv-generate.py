from openai import OpenAI
import argparse
# from tqdm import tqdm
from multiprocessing import Pool, current_process
import requests
import time 
import yaml

SYSTEM_PROMPT = "The following instructions are text taken from a blog post on AI and ML, please create pretty images to accompany an audio version of this post: \n\n"
client = OpenAI()

# TODO investigate below
"""
Exception in thread Thread-3 (_handle_results):
Traceback (most recent call last):
  File "/Users/nato/miniconda3/envs/media/lib/python3.10/threading.py", line 1009, in _bootstrap_inner
    self.run()
  File "/Users/nato/miniconda3/envs/media/lib/python3.10/threading.py", line 946, in run
    self._target(*self._args, **self._kwargs)
  File "/Users/nato/miniconda3/envs/media/lib/python3.10/multiprocessing/pool.py", line 576, in _handle_results
    task = get()
  File "/Users/nato/miniconda3/envs/media/lib/python3.10/multiprocessing/connection.py", line 256, in recv
    return _ForkingPickler.loads(buf.getbuffer())
TypeError: APIStatusError.__init__() missing 2 required keyword-only arguments: 'response' and 'body'
"""
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
    
    # read input
    with open(args.input, "r") as f:
        data = f.read()
        
    def split_string_into_segments(text, paragraphs_per_segment=1):
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
        
        

        
        
