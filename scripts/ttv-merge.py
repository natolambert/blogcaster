# Please shoot me a message, open an issue, or comment on Interconnects if you're using this code! I'd love to know.

import argparse
import os

import cv2
import yaml
from moviepy.editor import (
    AudioFileClip,
    ImageClip,
    VideoFileClip,
    concatenate_videoclips,
)
from pydub import AudioSegment


def get_cumulative_length(file_list, offset: float = 0.0):
    cumulative_length = 0
    for filename in file_list:
        # filepath = os.path.join(directory, filename)
        audio = AudioSegment.from_file(filename)
        cumulative_length += len(audio)
    if offset:
        cumulative_length += offset

    return cumulative_length / 1000.0  # Convert to seconds


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


def images_to_video(directory, skip=False, use_music=False, m_file=None):
    image_dir = os.path.join(directory, "images")
    audio_dir = os.path.join(directory, "audio")
    audio_file = os.path.join(audio_dir, "generated_audio.mp3")

    # get length of every audio file in audio_dir other than generated_audio.mp3 and generated_audio_podcast.mp3
    audio_files = [f for f in os.listdir(audio_dir) if f.endswith((".mp3"))]
    audio_files = sorted(audio_files)
    audio_files = [f for f in audio_files if f not in ["generated_audio.mp3", "generated_audio_podcast.mp3"]]
    # remove audio files with _sec_ in it
    audio_files = [f for f in audio_files if "_sec_" not in f]  # remove sections if using music
    audio_files = [os.path.join(audio_dir, f) for f in audio_files]
    audio_clips = [AudioFileClip(f) for f in audio_files]
    audio_durations = [c.duration for c in audio_clips]

    # load config file config.yml from directory, get boolean list of which are figures
    with open(directory + "config.yml", "r") as f:
        config = yaml.load(f, Loader=yaml.FullLoader)

    # the indices to add the m_file length to are the first 'index' in each list of dictionaries in config
    # get the indices of the first 'index' in each list of dictionaries
    indices = [item[1][0]["index"] for i, item in enumerate(config.items()) if item[0] not in ["md", "date"]]
    indices = indices[1:]  # don't add time to the first frame
    if use_music and (m_file is not None):
        music_len = AudioFileClip(m_file).duration - 1
    else:
        music_len = 0
    # add music_len to indices (the minus 1 is the offset for the crossfade)
    audio_durations = [
        audio_durations[i] + music_len if i in indices else audio_durations[i] for i in range(len(audio_durations))
    ]

    # create list of 0s for every item in nest dict except md and date
    is_image = []
    is_video = []
    for key, value in config.items():
        if key in ["md", "date"]:
            continue
        else:
            is_image.append(False)
            is_video.append(False)
            for item in value:
                if "alt_text" in item.get("content", {}):
                    if ".mp4" in item["content"]["path"]:
                        is_video.append(True)
                        is_image.append(False)
                    else:
                        is_video.append(False)
                        is_image.append(True)
                else:
                    is_image.append(False)
                    is_video.append(False)

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

    video_files = [f for f in os.listdir(image_dir) if f.endswith(".mp4")]

    assert (len(image_files) + len(video_files)) == len(
        new_audio_durations
    ), f"Number of images {len(image_files) + len(video_files)} and audio files {len(new_audio_durations)} must be the same"  # noqa

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
    # for i, i_v, d, d_new in zip(is_image, is_video, audio_durations, new_audio_durations):
    #     print(i, i_v, d, d_new)

    # print(sum(audio_durations), sum(new_audio_durations))

    # Assign duration for each image
    # first, we need to copy the previous image for the figures that are videos (is_video), which is added after

    all_images_for_video = all_images.copy()
    for i, is_vid in enumerate(is_video):
        if is_vid:
            all_images_for_video.insert(i, all_images_for_video[i - 1])

    # extend all_video there to match length of new_audio_durations
    clips = [ImageClip(m).set_duration(d) for m, d in zip(all_images_for_video, new_audio_durations)]

    concat_clip = concatenate_videoclips(clips, method="compose")
    concat_clip_audio = concat_clip.set_audio(audio_clip)

    # if files with *.mp4 exist in the directory, we will add videos in line
    if len(video_files) > 0:
        video_files = sorted(video_files)
        video_files = [os.path.join(image_dir, f) for f in video_files]
        video_clips = [VideoFileClip(f) for f in video_files]

        # resuze video if bigger than desired_width or desired_height or pad if too small
        for i, clip in enumerate(video_clips):
            (original_width, original_height) = clip.size[:2]
            ratio_width = desired_width / float(original_width)
            ratio_height = desired_height / float(original_height)
            ratio = min(ratio_width, ratio_height)

            # Compute new dimensions
            new_width = int(original_width * ratio)
            new_height = int(original_height * ratio)

            # if height or width change:
            if (new_height, new_width) != (original_height, original_width):
                clip = clip.resize((new_width, new_height))

                # use clip.margin (left, right, top, bottom) to center the video
                # in the same size
                clip = clip.margin(
                    left=int((desired_width - new_width) / 2),
                    right=int((desired_width - new_width) / 2),
                    top=int((desired_height - new_height) / 2),
                    bottom=int((desired_height - new_height) / 2),
                )
            video_clips[i] = clip

        # for video clips, print the size
        # for clip in video_clips:
        #     print(clip.size)

        # process audio_durations and is_video to figure out insert_time for each video
        insert_times = []
        offset = 0  # offset the insert time based on cumualtive length of added videos
        video_count = 0
        for i, is_vid in enumerate(is_video):
            if is_vid:
                insert_times.append(sum(audio_durations[: i + 1]) + offset)  # noqa
                offset += video_clips[video_count].duration
                print(video_clips[video_count].duration, insert_times[-1], offset)
                video_count += 1

        for time, clip in zip(insert_times, video_clips):
            # clip = clip.set_duration(5) # max 5 seconds for now
            first_part = concat_clip_audio.subclip(0, time)
            second_part = concat_clip_audio.subclip(time)
            concat_clip_audio = concatenate_videoclips([first_part, clip, second_part], method="compose")

    # watermark_exists = os.path.exists("source/repeat/watermark.jpg")
    # if watermark_exists:
    #     print("WATERMARKING VIDEO")
    #     logo = (mp.ImageClip("source/repeat/watermark.jpg")
    #       .set_duration(concat_clip_audio.duration)
    #       .margin(right=8, top=8, bottom=8, opacity=0) # (optional) logo-border padding
    #       .set_pos(("right","bottom")))
    #         #   .resize(height=75) # if you need to resize...

    #     concat_clip_audio = mp.CompositeVideoClip([concat_clip_audio, logo])

    concat_clip_audio.write_videofile(
        "new_filename.mp4",
        fps=30,
        threads=8,
        codec="libx264",
        audio_codec="aac",
        temp_audiofile="temp-audio.m4a",
        remove_temp=True,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=str, required=True, help="directory with images, config, and audio")
    parser.add_argument("--ignore_title", action="store_true", default=False, help="skip titles for generative talks")
    parser.add_argument("--use_music", action="store_true", default=False, help="use music for audio")
    parser.add_argument(
        "--music_file",
        type=str,
        default="source/repeat/transition-mono-v2.mp3",
        help="audio file for used for music in audio (to get length)",
    )
    args = parser.parse_args()

    # Convert images and audio to video
    images_to_video(args.input, skip=args.ignore_title, use_music=args.use_music, m_file=args.music_file)
