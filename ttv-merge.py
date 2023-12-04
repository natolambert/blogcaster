import os
import argparse
import cv2
from moviepy.editor import VideoFileClip, AudioFileClip, ImageClip, concatenate_videoclips, CompositeAudioClip

def images_to_video(image_dir, audio_file, output_file):
    # Get all image files in the directory
    image_files = [f for f in os.listdir(image_dir) if f.endswith(('.jpg', '.jpeg', '.png'))]
    image_files.sort()
    
    # Load the first image to get dimensions
    first_image = cv2.imread(os.path.join(image_dir, image_files[0]))
    height, width, _ = first_image.shape
    
    # load all images
    all_images = [cv2.imread(os.path.join(image_dir, image_file)) for image_file in image_files[1:]]
    all_images = [first_image] + all_images
    
    # load audio
    audio_clip = AudioFileClip(audio_file)
    audio_duration = audio_clip.duration

    # Calculate duration for each image
    image_duration = audio_duration / len(image_files)
    clips = [ImageClip(m).set_duration(image_duration) for m in all_images]

    concat_clip = concatenate_videoclips(clips, method="compose")
    # concat_clip.write_videofile("output.mp4", fps=30)

    # load video and add audio
    # videoclip = VideoFileClip("output.mp4")

    # new_audioclip = CompositeAudioClip([audio_clip])
    concat_clip_audio = concat_clip.set_audio(audio_clip)
    concat_clip_audio.write_videofile("new_filename.mp4", 
                                fps=30,
                                codec='libx264', 
                                audio_codec='aac', 
                                temp_audiofile='temp-audio.m4a', 
                                remove_temp=True
                            )

    # clips = [ImageClip(m).set_duration(2)
    #   for m in img]

    # concat_clip = concatenate_videoclips(clips, method="compose")
    # concat_clip.write_videofile("test.mp4", fps=24)


    # # Create VideoWriter object
    # fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # or use 'XVID'
    # video = cv2.VideoWriter(output_file, fourcc, 1.0 / image_duration, (width, height))

    # # Write images to video with corresponding audio segments
    # for i, image_file in enumerate(image_files):
    #     image_path = os.path.join(image_dir, image_file)
    #     frame = cv2.imread(image_path)

    #     # Calculate the start and end time for the audio segment
    #     start_time = i * image_duration
    #     end_time = (i + 1) * image_duration

    #     # Extract audio segment corresponding to the image
    #     audio_segment = audio_clip.subclip(start_time, end_time)
    #     import ipdb; ipdb.set_trace()
    #     # Write image and audio segment to video
    #     video.write(frame)
    #     video.write(audio_segment.to_soundarray(fps=44100))

    # video.release()

    # # Clean up the temporary video file without audio
    # os.remove(output_file)

if __name__ == "__main__":
    # import argparse and define txt file path and output path
    parser = argparse.ArgumentParser()
    parser.add_argument("--audio", type=str, help="input audio file path")
    parser.add_argument("--images", type=str, help="input images directory path")
    parser.add_argument("--output", type=str, default="output.mp4", help="output mp4 file path")
    args = parser.parse_args()
    
    # Convert images and audio to video
    images_to_video(args.images, args.audio, args.output)
