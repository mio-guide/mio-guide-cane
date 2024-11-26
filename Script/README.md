# Script

## Requirements

Besides Python, Ghostscript and FFmpeg are required in order to run the script and can be installed via the following commands on macOS via [Homebrew](https://brew.sh/):

```
brew install ghostscript
brew install ffmpeg
```

## Installing Dependencies

You can install the dependencies via the following command:

```bash
python3 -m pip install -r requirements.txt
```

## Running Script

You can run the script via the following command:

```bash
python3 script.py
```

## Input

The script scans the `./input` directory for `*.md` files and uses them to create the codes and tracks. There are two example `.md` files that show how to describe an exhibition. The following format is used to create codes:

```
# exhibit title

exhibit text
```

or

```
# crossing

- text for what's in front
- text for what's to the right
- text for what's in the back
- text for what's to the left
```

When describing different directions, `.` can be used as a keyword in order for that direction to be ignored for the audio track. Otherwise the texts are used in the generated audio tracks with the spoken prefix defined in the `TrackFactory` in `script.py`.

## Output

The output can be found in the `./output` directory which contains the codes in the `codes` directory and the audio tracks in the `tracks` directory. The `codes.html` file can be used to print the codes and `mapping.xlsx` describes the relation between IDs and the headings from the markdown input files.

## Tutorial Track

You can change the tutorial track by adjusting the text in `tutorial.py` and executing the script using the following command which will generate a new `tutorial.mp3`:

```bash
python3 tutorial.py
```

The generated tutorial track `template/tutorial.mp3` is going to be automatically added with a corresponding code on every subsequent run of `script.py`.
