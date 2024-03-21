import eyed3
from eyed3.id3.frames import ImageFrame


def get_figures_per_section(dictionary):
    """
    Given dictionary config as follows:
    1_Test Post:
        - content: The future of writing with AI
        index: 1
        - content: the brown boy walks the cat. Adding a sentence!
        index: 2
        - content:
            alt_text: "Screenshot 2023-12-22 at 10.56.47\u202FAM.png"
            path: Test%20Post%209516e8d6e5994c92a6d7d19245dc27e5/Screenshot_2023-12-22_at_10.56.47_AM.png
        index: 3
        2_Next section!:
        - content: How are you doing?
        index: 4
        - content: Let's have a couple paragraphs here. This one has another sentence.
        index: 5
        3_Final section:
        - content: Blah blah blah. Thanks for listening. Blah dog.
        index: 6
        - content: I hope my new workflow works great!
        index: 7
        date: December 27th 2023
        md: source/test-post/Test Post 9516e8d6e5994c92a6d7d19245dc27e5.md

    Check which sections as N_ have a member with "path" and extract the paths
    """
    # Extract paths from the sections
    paths = []
    for key, value in dictionary.items():
        if isinstance(value, list):  # Only process sections which are lists
            images_per_section = []
            for item in value:
                if "path" in item.get("content", {}):
                    images_per_section.append(item["content"]["path"].replace("%20", " "))

            paths.append(images_per_section)
    return paths


def embed_chapters_with_images(audio_file, chapters, images):
    # Load the audio file
    audio = eyed3.load(audio_file)
    # if audio.tag is None:
    audio.initTag(version=(2, 3, 0))

    # Add chapters
    for i, chapter in enumerate(chapters):
        start_time, end_time, title = chapter
        audio.tag.chapters.set(title, start_time, end_time)  # , title)
        # audio.tag.chapters.set(i, start_time, end_time, title)

        # Add image for the chapter if available
        if i < len(images) and images[i] is not None:
            with open(images[i], "rb") as img_file:
                # img_data = img_file.read()
                # import ipdb; ipdb.set_trace()
                audio.tag.images.set(ImageFrame.FRONT_COVER, img_file.read(), "image/png", "Figure for section")
            # import ipdb; ipdb.set_trace()
            # audio.tag.images.set(3, img_data, "image/png", u"Figure for section")

    audio.tag.save()


# Example usage
audio_file = audio_dir + "/" + args.output + ".mp3"
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
