import os 
import argparse
import re
import yaml
import unidecode

# create argparse function that takes in a directory (for later creating a yml file)
def get_args():
    parser = argparse.ArgumentParser()
    # only one argument so doesn't need a tag
    parser.add_argument("directory", type=str, help="input directory path")
    args = parser.parse_args()
    return args

def find_markdown_and_directories(directory):
    """
    Find a markdown file in the specified directory, ensure 'gen-images' directory exists,
    and list one other directory if available.

    Args:
    directory (str): The directory to search in.

    Returns:
    tuple: A tuple containing the filename of a markdown file, the 'gen-images' directory path,
           and another directory path if available.
    """
    markdown_file = None
    figures_directory = None
    images_dir = os.path.join(directory, "gen-images")

    # Ensure 'gen-images' directory exists
    if not os.path.exists(images_dir):
        os.makedirs(images_dir)

    # Search for a markdown file and another directory (which holds figures)
    for entry in os.listdir(directory):
        full_path = os.path.join(directory, entry)
        if os.path.isdir(full_path) and entry != "gen-images":
            figures_directory = full_path
        elif markdown_file is None and entry.lower().endswith('.md'):
            markdown_file = entry

        # If both are found, no need to continue
        if markdown_file and figures_directory:
            break

    return (markdown_file, images_dir, figures_directory)

def rename_spaces_to_underscores(path):
    if not os.path.exists(path):
        print(f"The path '{path}' does not exist.")
        return

    new_name = path.replace(' ', '_')
    os.rename(path, new_name)
    print(f"Renamed '{path}' to '{new_name}'")

def parse_markdown_to_dict(md_content):
    """
    Parse markdown content and return a dictionary with sections, paragraphs, and figures.
    """
    sections = {}
    current_section = ''
    paragraph_index = 0
    section_index = 0

    for line in md_content.split('\n'):
        if line.startswith('#'):
            # New section
            section_index += 1
            current_section = re.sub(r'#+\s*', '', line).strip()
            sections[f"{section_index}_" + current_section] = []
        elif line.strip():
            if line.strip().startswith('!['):
                # Figure found
                alt_text, img_path = re.findall(r'\[([^]]+)\]\(([^)]+)\)', line)[0]
                sections[f"{section_index}_" + current_section].append({'index': paragraph_index, 'content': {'alt_text': alt_text, 'path': img_path}})
            else:
                # Regular paragraph
                sections[f"{section_index}_" + current_section].append({'index': paragraph_index, 'content': unidecode.unidecode(line.strip())})
            paragraph_index += 1

    return sections

def read_markdown_file(filename):
    """
    Read markdown file and return its content.
    """
    with open(filename, 'r') as file:
        return file.read()

def write_yaml_file(data, filename):
    """
    Write data to a YAML file.
    """
    with open(filename, 'w') as file:
        yaml.dump(data, file)

def markdown_to_yaml(md_filename, yaml_filename):
    """
    Convert markdown file to YAML file.
    """
    md_content = read_markdown_file(md_filename)
    sections_dict = parse_markdown_to_dict(md_content)
    write_yaml_file(sections_dict, yaml_filename)


if __name__ == "__main__":
    args = get_args()
    markdown_file, images_dir, figures_directory = find_markdown_and_directories(args.directory)    
    # replace files and folders containing spaces with _ (in the OS)
    # rename_spaces_to_underscores(markdown_file)
    # rename_spaces_to_underscores(images_dir)
    # rename_spaces_to_underscores(figures_directory)
    
    markdown_to_yaml(args.directory + markdown_file, args.directory + "config.yml")
    print(f"INFO: Created post config file at {args.directory + 'config.yml'}")
