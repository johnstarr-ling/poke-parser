# poke-parser
**GOAL:** Parsing Pokemon Showdown HTML replays and extracting numerous statistics -- on Pokemon and on their trainers -- from the matches.

**NOTE:** Only the _Gen 6 DRAFT_ format is operational. Trying to use the current script with other formats or generations will results in errors.

*If you have any questions on how to use this repository beyond the instructions reported here, please contact me.*


## REPOSITORY ORGANIZATION 
- `poke-parser.py` is the main Python script. Instructions for running this script are included in the next main section, though I have included many comments throughout the script if you are interested in unpacking its features or customizing it for your own use.
- `analyses.ipynb` is a Jupyter notebook that transforms the data (from the `csvs` folder) into the various graphs and final statistics found in the `stats` folder and subfolders therein. This notebook also uses Python. 
- `TODO.md` describes features that I am hoping to implement in the near future, though I make no guarantees that these features will be posted here. 

#### Directories 
- `csvs` contains the output `.csv` files of `poke-parser.py`. Player statistics are separated from pokemon statistics. 
- `htmls` contains replays, should you want to use the parser not in a weekly format but in a batch format. More description of the different kinds of processing later. 
- `replays` contains subfolders labeled by week, where each weekly subfolder contains all the replays from that week.
- `stats` contains subfolders labeled by their type, where each subfolder contains all the processed statistics from the `analyses.ipynb` folder. 

## INSTALLATION
This repository assumes that you have Python >= 3.10 installed. To download Python to your machine, go to [this link](https://www.python.org/downloads/) and find an appropriate version.

You will also need to install the `pandas` and `numpy` Python packages. Documentation for each can be found [here](https://pandas.pydata.org/) and [here](https://numpy.org/), respectively. To install `numpy` and `pandas` onto your machine, run the following code in your preferred terminal:


```pip install numpy pandas```


I traditionally develop my code in a [Conda virtual environment](https://conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html) using `miniconda`. If you are anticipating using different versions of Python/`numpy`/`pandas` for other projects, I'd encourage you to do the same!

## USE
Following installation of Python and the two packages, clone/download this repository by clicking the green `<> Code` button in the upper-right corner. If downloading the ZIP folder, unpack it in the repository of your choice. Then, open your preferred terminal and navigate to where you've placed this repository; to move around, use the `cd` command.

Once you are in the base directory for this repository (and not in any of the main folders), you can run the script in two ways:
1. Run batch statistics (aka no weekly format): `python poke-parser.py FOLDER/`
2. Run weekly statistics: `python poke-parser.py FOLDER/ -w`

The first command runs on the `htmls` folder; the second command runs on the `replays` folder; note the different kinds of file structure for these two folders, which aligns with the commands.

**NOTE:** Some errors may arise due to naming conventions. If possible, *minimize* the amount of special characters that are in your replay files. I have deleted all special characters from names that cause issues; see files in the `replays` folder for examples.




