# Please shoot me a message, open an issue, or comment on Interconnects if you're using this code! I'd love to know.

import argparse
import os

import cv2
import yaml
from moviepy.editor import AudioFileClip, ImageClip, concatenate_videoclips


def adjust_audio_durations(audio_durations, is_image):
    # Ensure the lists are of the same length
    if len(audio_durations) != len(is_image):
        raise ValueError("Lists audio_durations and is_image must be of the same length")

    # Create a copy of the audio_durations list to modify
    adjusted_durations = audio_durations.copy()

    for i in range(len(is_image)):
        if is_image[i]:
            # If the image is at the start
            if i == 0 and i + 1 < len(is_image):
                increase = 0.5 * adjusted_durations[i + 1]
                adjusted_durations[i] += increase
                adjusted_durations[i + 1] -= increase

            # If the image is at the end
            elif i == len(is_image) - 1 and i - 1 >= 0:
                increase = 0.25 * adjusted_durations[i - 1]
                adjusted_durations[i] += increase
                adjusted_durations[i - 1] -= increase

            # For images in the middle
            elif 0 < i < len(is_image) - 1:
                increase_preceding = 0.25 * adjusted_durations[i - 1]
                increase_following = 0.5 * adjusted_durations[i + 1]
                adjusted_durations[i] += increase_preceding + increase_following
                adjusted_durations[i - 1] -= increase_preceding
                adjusted_durations[i + 1] -= increase_following

    return adjusted_durations


def images_to_video(directory, skip=False):
    image_dir = os.path.join(directory, "images")
    audio_dir = os.path.join(directory, "audio")
    audio_file = os.path.join(audio_dir, "generated_audio.mp3")

    # get length of every audio file in audio_dir other than generated_audio.mp3 and generated_audio_podcast.mp3
    audio_files = [f for f in os.listdir(audio_dir) if f.endswith((".mp3"))]
    audio_files = sorted(audio_files)
    audio_files = [f for f in audio_files if f not in ["generated_audio.mp3", "generated_audio_podcast.mp3"]]
    audio_files = [os.path.join(audio_dir, f) for f in audio_files]
    audio_clips = [AudioFileClip(f) for f in audio_files]
    audio_durations = [c.duration for c in audio_clips]

    # load config file config.yml from directory, get boolean list of which are figures
    with open(directory + "config.yml", "r") as f:
        config = yaml.load(f, Loader=yaml.FullLoader)

    # create list of 0s for every item in nest dict except md and date
    is_image = []
    for key, value in config.items():
        if key in ["md", "date"]:
            continue
        else:
            is_image.append(False)
            for item in value:
                if "alt_text" in item.get("content", {}):
                    is_image.append(True)
                else:
                    is_image.append(False)

    # for talks
    if skip:
        is_image = is_image[1:]

    # for items where is_image is True, increase the time in audio_durations
    # by .25 of the preceeding paragraph and .5 of the following paragraph
    # reduce the time of the preceeding and following image accordingly
    # if image is at the beginning or end, only increase the following or preceeding paragraph
    new_audio_durations = adjust_audio_durations(audio_durations, is_image)

    # Get all image files in the directory
    image_files = [f for f in os.listdir(image_dir) if f.endswith((".jpg", ".jpeg", ".png", ".webp"))]
    image_files = sorted(image_files)

    assert len(image_files) == len(
        new_audio_durations
    ), f"Number of images {len(image_files) }and audio files {len(new_audio_durations)} must be the same"

    # Load the first image to get dimensions
    first_image = cv2.imread(os.path.join(image_dir, image_files[0]))
    # height, width, _ = first_image.shape

    # load all images
    all_images = [cv2.imread(os.path.join(image_dir, image_file)) for image_file in image_files[1:]]
    all_images = [first_image] + all_images
    # check coloring with cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
    all_images = [cv2.cvtColor(frame, cv2.COLOR_RGB2BGR) for frame in all_images]

    # get dimensions of all the images
    heights = [frame.shape[0] for frame in all_images]
    widths = [frame.shape[1] for frame in all_images]
    # take most common height and width pairing
    desired_height = max(set(heights), key=heights.count)
    desired_width = max(set(widths), key=widths.count)
    # if images are taller or wider than the most common (DALLE images), shrink to conflicting dimension
    # Resize images if they are larger than the most common dimensions
    resized_images = []
    for frame in all_images:
        (original_height, original_width) = frame.shape[:2]
        ratio_width = desired_width / float(original_width)
        ratio_height = desired_height / float(original_height)
        ratio = min(ratio_width, ratio_height)

        # Compute new dimensions
        new_width = int(original_width * ratio)
        new_height = int(original_height * ratio)

        # Resize the frame
        resized_frame = cv2.resize(frame, (new_width, new_height))

        # If you need to pad the image to maintain the desired dimensions
        delta_width = desired_width - new_width
        delta_height = desired_height - new_height
        top, bottom = delta_height // 2, delta_height - (delta_height // 2)
        left, right = delta_width // 2, delta_width - (delta_width // 2)
        color = [0, 0, 0]  # Color for padding, black in this case
        resized_frame = cv2.copyMakeBorder(resized_frame, top, bottom, left, right, cv2.BORDER_CONSTANT, value=color)

        resized_images.append(resized_frame)

    # Now, resized_images contains all your frames with uniform dimensions
    all_images = resized_images

    # load audio
    audio_clip = AudioFileClip(audio_file)
    # audio_duration = audio_clip.duration

    # Calculate duration for each image
    # image_duration = audio_duration / len(image_files)
    clips = [ImageClip(m).set_duration(d) for m, d in zip(all_images, new_audio_durations)]

    concat_clip = concatenate_videoclips(clips, method="compose")
    concat_clip_audio = concat_clip.set_audio(audio_clip)
    concat_clip_audio.write_videofile(
        "new_filename.mp4",
        fps=30,
        codec="libx264",
        audio_codec="aac",
        temp_audiofile="temp-audio.m4a",
        remove_temp=True,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=str, required=True, help="directory with images, config, and audio")
    parser.add_argument("--ignore_title", action="store_true", default=False, help="skip titles for generative talks")
    args = parser.parse_args()

    # Convert images and audio to video
    images_to_video(args.input, skip=args.ignore_title)
