# Tools for blogging!

```
conda activate media
```
Or, install from `requirements.txt`

## Example usage
Audio:
```
python tts.py --input=raw/2023-12-06-dpo.txt
```

Images:
```
python ttv-generate.py --input=raw/2023-29-11-synthetic.txt
```

Video:
```
python ttv-merge.py --audio=audio/20231129-synthetic.mp3 --images=images/
```