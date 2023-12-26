# Tools for blogging!

```
conda activate media
```
Or, install from `requirements.txt`

## Example usage
This is designed to work with the following data format:
```
scripts/
source/
└─- post-title/
|   |-- post-title-name.md
|   └- post-title-name/
|       | img0.png
|       | ...
|       └─ imgN.pnd
| ...
└─- post-title-two/
| ...
```

Generate the config file (that contains the paragraphs etc)
```
python create-config source/test-post/ --date="24 December 2023"
```

Audio gen:
```
python tts.py --input=source/test-post/
```

Audio add music + outro:
```
python add-music.py --input=audio/20231129-synthetic.mp3
```

Images:
```
python ttv-generate.py --input=raw/2023-29-11-synthetic.txt
```

Video:
```
python ttv-merge.py --audio=audio/20231129-synthetic.mp3 --images=images/
```