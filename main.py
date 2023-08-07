from src.top_podcasts import create_podcast_charts
from src.streamgraphs import create_streamgraphs
from src.top_artists import create_artist_charts
from src.top_albums import create_album_charts
from src.top_tracks import create_track_charts
import pandas as pd
import argparse
import os
import re


def format_df(df):
    print('- Formatting data...')
    df['ts'] = pd.to_datetime(df['ts'])
    df = df.sort_values(by=['ts'])

    # make barcharts for shuffle versus non-shuffle each year
    df['year'] = df['ts'].dt.year
    df['month'] = df['ts'].dt.month
    df['day'] = df['ts'].dt.day
    df['hour'] = df['ts'].dt.hour

    podcasts_df = df[~df['episode_name'].isna()]
    df = df[df['episode_name'].isna()]
    print(f"- Filtered out {int(podcasts_df['ms_played'].sum()/3600000)} hours of listening from {len(podcasts_df['episode_show_name'].unique())} different podcasts")

    # rename column names
    df = df.rename(columns={'master_metadata_album_artist_name': 'artist', 'master_metadata_album_album_name': 'album', 'master_metadata_track_name': 'track'})
    podcasts_df = podcasts_df.rename(columns={'episode_name': 'episode', 'episode_show_name': 'podcast'})

    aliases_to_replace = {
        'DOOM': 'MF DOOM',
        'Viktor Vaughn': 'MF DOOM',
        'Zev Love X': 'MF DOOM',
        'King Geedorah': 'MF DOOM',
        'Madvillain': 'MF DOOM',
        'JJ DOOM': 'MF DOOM',
        'MF Grimm': 'MF DOOM',
        'Danger Doom': 'MF DOOM',
        'Metal Fingers': 'MF DOOM',
        'Philip Glass Ensemble': 'Philip Glass'
    }

    # Replace all artist aliases
    num_replaced = len(df[df['artist'].isin(aliases_to_replace.keys())])
    df['artist'] = df['artist'].replace(aliases_to_replace)

    if num_replaced > 0:
        print(f"- Renamed {num_replaced} aliases with artist name")

    return df, podcasts_df


def cast_bool_to_numeric(df):
    bool_cols = df.select_dtypes(include=bool).columns
    df[bool_cols] = df[bool_cols].astype(int)
    return df


def load_data(json_dir, output_dir):
    temp_json = os.path.join(output_dir, 'spotify_data.json')
    temp_podcasts_json = os.path.join(output_dir, 'spotify_podcasts_data.json')

    if os.path.exists(temp_json):
        print('- Loading data from json...')
        df = pd.read_json(temp_json, orient='records')
        df['ts'] = pd.to_datetime(df['ts'])

        podcasts_df = pd.read_json(temp_podcasts_json, orient='records')
        podcasts_df['ts'] = pd.to_datetime(podcasts_df['ts'])
        return df, podcasts_df
    else:
        print(f'- Loading data from {json_dir}...')
        available_encodings = ['utf-8', 'utf-16', 'latin-1', 'ISO-8859-1']
        valid_files = []
        valid_file_pattern = r"Streaming_History.+\.json"
        for f in os.listdir(json_dir):
            if not re.match(valid_file_pattern, f):
                continue

            for encoding in available_encodings:
                try:
                    df = pd.read_json(f'{json_dir}/{f}', encoding=encoding)
                    df = cast_bool_to_numeric(df)
                    valid_files.append((f, encoding, df))
                    break
                except (UnicodeDecodeError, ValueError):
                    pass

        # Process valid files
        cumulative_df = None
        for filename, encoding, df in valid_files:
            if cumulative_df is None:
                cumulative_df = df
            else:
                cumulative_df = pd.concat([cumulative_df, df])

        df, podcasts_df = format_df(cumulative_df)

        print('- Saving data to json...')
        # save df to json but make timestamps work
        df['ts'] = df['ts'].astype(str)
        df.to_json(temp_json, orient='records')

        podcasts_df['ts'] = podcasts_df['ts'].astype(str)
        podcasts_df.to_json(temp_podcasts_json, orient='records')

    print()
    return df, podcasts_df


def main(json_dir, output_dir, darkmode=True):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    df, podcasts_df = load_data(json_dir, output_dir)

    create_podcast_charts(podcasts_df, output_dir, top_n=20, darkmode=darkmode)
    create_streamgraphs(podcasts_df, output_dir, top_n=10, darkmode=darkmode, podcasts=True)
    create_artist_charts(df, output_dir, top_n=20, darkmode=darkmode)
    create_streamgraphs(df, output_dir, top_n=10, darkmode=darkmode)
    create_track_charts(df, output_dir, top_n=20, darkmode=darkmode)
    create_album_charts(df, output_dir, top_n=10) # There is no darkmode option for top albums (looks better in white)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Summary statistics from Spotify data')
    parser.add_argument('--input_dir', '-i', type=str, help='Directory containing json files from Spotify')
    parser.add_argument('--output_dir', '-o', type=str, default=os.path.expanduser("~/Downloads/spotify_summary_plots"), help='Directory to save output')
    parser.add_argument('--lightmode', '-l', help='Use light mode for plots', action='store_true', default=False)
    args = parser.parse_args()

    if args.input_dir is None:
        print('Please specify a directory containing json files from Spotify')
        exit(1)

    main(json_dir=args.input_dir, output_dir=args.output_dir, darkmode=not args.lightmode)
