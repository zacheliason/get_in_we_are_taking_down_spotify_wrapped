# README

## Description
Some fun/simple summary charts based on Spotify user data:
* Top Artist/Track/Album (for each year individually)![](images/top_artists_2020.png)
* Top Artist/Track/Album All Time by Year ![](images/top_artists_all_time_by_year.png)
* Top Artist/Track/Album Streamgraphs ![](images/streamgraph_top_artists_2020.png)
* Top Artist/Track/Album Streamgraphs All Time ![](images/streamgraph_top_artists_2013-2023.png)
* (all the same charts but for podcasts) ![](images/top_podcasts_all_time_by_year.png)
* Top Album (with album covers, for each year individually) ![](images/top_albums_2022.png) (sometimes the album covers itunes finds are wrong in funny ways, i.e. the Bob's Burgers single cover it downloads instead of the Mishima Soundtrack album cover)
* Top Album by Year (with album covers) ![](images/top_albums_full.png)

## Installation
First set up a `conda` environment with the required packages (miniconda can be downloaded [here](https://docs.conda.io/en/latest/miniconda.html)):
```bash
conda env create --file environment.yml
conda activate spotify_env
```

## Usage
The script requires a path to the directory containing the user data (a bunch of `json` StreamingHistory files). You can request a copy of your own data at [this link](https://www.spotify.com/us/account/privacy/). Make sure you request Extended Streaming History to get your entire dataset.

* `-i` or `--input_dir`: path to directory containing user data
* `-o` or `--output_dir`: path to directory to save output (default: `~/Downloads/spotify_summary_plots`)
* `-l` or `--lightmode`: toggle lightmode/darkmode for plots (default: `darkmode`)

Example command:
```bash
python3 main.py -i /Users/zacheliason/Downloads/SpotifyData -o ./example_output
```
