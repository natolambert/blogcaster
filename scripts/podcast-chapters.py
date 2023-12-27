from eyed3.id3.frames import ImageFrame
import eyed3

def embed_chapters_with_images(audio_file, chapters, images):
    # Load the audio file
    audio = eyed3.load(audio_file)
    # if audio.tag is None:
    audio.initTag(version=(2, 3, 0))

    # Add chapters
    for i, chapter in enumerate(chapters):
        start_time, end_time, title = chapter
        audio.tag.chapters.set(title, start_time, end_time) #, title)
        # audio.tag.chapters.set(i, start_time, end_time, title)

        # Add image for the chapter if available
        if i < len(images) and images[i] is not None:
            with open(images[i], 'rb') as img_file:
                # img_data = img_file.read()
                # import ipdb; ipdb.set_trace()
                audio.tag.images.set(ImageFrame.FRONT_COVER, img_file.read(), "image/png", u"Figure for section")
            # import ipdb; ipdb.set_trace()
            # audio.tag.images.set(3, img_data, "image/png", u"Figure for section")

    audio.tag.save()

# Example usage
audio_file = audio_dir + '/' + args.output+".mp3"
chapters = []
files = []
start = 0
for l, s in zip(section_lens, section_titles):
    chapters.append((start, start + l, s))
    files.append([])
    start += l
    
# # images = ['path/to/intro.jpg', None, 'path/to/chapter2.jpg']  # paths to images, None where no image is available

list_of_figs = get_figures_per_section(config)
# # split list into single for now
# # TODO split chapter when multiple images
list_of_figs = [args.input + l[0] if len(l) > 0 else None for l in list_of_figs]
embed_chapters_with_images(audio_file, chapters, list_of_figs)
