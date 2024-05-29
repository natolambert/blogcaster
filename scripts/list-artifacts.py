import argparse

from huggingface_hub import get_collection


def process_collection(collection_name, index, print_idx=False):
    collection = get_collection(collection_name)

    if index < 0 or index >= len(collection.items):
        return f"Error: invalid index: {index} for length of collection: {len(collection.items)}"

    markdown_list = f"\n# Artifacts Log N\n\n"
    categories = {"model": [], "dataset": [], "Space": []}

    for idx, item in enumerate(collection.items[index:]):
        author, model_name = item.item_id.split("/")
        if item.item_type == "model":
            model_link = f"https://huggingface.co/{item.item_id}"
        else:
            model_link = f"https://huggingface.co/{item.item_type}s/{item.item_id}"
        entry = f"- **[{model_name}]({model_link})** by [{author}](https://huggingface.co/{author}): TODO\n"

        if print_idx:
            entry = f"- {idx + index} [{model_name}]({model_link}) by {author}\n"

        if item.item_type in categories:
            categories[item.item_type].append(entry)

    for category, items in categories.items():
        if items:
            markdown_list += f"### {category.capitalize()}s\n\n"
            markdown_list += "".join(items)
            markdown_list += "\n"

    markdown_list += "\n References: ([2024 artifacts](https://huggingface.co/collections/natolambert/2024-interconnects-artifacts-6619a19e944c1e47024e9988), [2023 artifacts](https://huggingface.co/collections/natolambert/2023-interconnects-artifacts-661b19d27082ad0b43d67b17), [MMLU vs training compute model](https://docs.google.com/spreadsheets/d/13LMlSGQQ3_qxbjIcEkgqofr2Ay1JT0XEH4S-AWQi8so/edit?usp=sharing)) \n"
    return markdown_list


def main():
    parser = argparse.ArgumentParser(description="Process a Hugging Face collection into a Markdown list.")
    parser.add_argument(
        "collection_name",
        nargs="?",
        default="natolambert/2024-interconnects-artifacts-6619a19e944c1e47024e9988",
        help="The name of the Hugging Face collection (default: natolambert/2024-interconnects-artifacts-6619a19e944c1e47024e9988)",
    )
    parser.add_argument(
        "--index",
        type=int,
        default=0,
        help="The start index of the collection list (to take the most recent elements)",
    )
    parser.add_argument("--print_idx", action="store_true", help="Print the index of the collection list")
    args = parser.parse_args()

    markdown_list = process_collection(args.collection_name, args.index, args.print_idx)
    print(markdown_list)


if __name__ == "__main__":
    main()
