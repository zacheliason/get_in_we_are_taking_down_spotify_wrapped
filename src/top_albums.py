from src.plot_formatting import set_plot, set_font, get_discrete_colors, get_axis_and_grid_colors
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from matplotlib import pyplot as plt
from PIL import Image
import urllib.request
import pandas as pd
import numpy as np
import traceback
import requests
import json
import re
import os


def group_df_by_target(df, target_col, top_n, output_dir):
    album_art_dir = os.path.join(output_dir, 'album_art_dir')
    if not os.path.exists(album_art_dir):
        os.makedirs(album_art_dir)
    jpeg_dict = {}

    album = target_col[0]
    artist = target_col[1]

    unique_artists_per_album = df.groupby(album)[artist].nunique().reset_index()
    unique_artists_per_album.rename(columns={artist: 'unique_artists'}, inplace=True)

    grouped_df = df.groupby(target_col)['ms_played'].sum()
    grouped_df = grouped_df.reset_index()

    grouped_df = pd.merge(grouped_df, unique_artists_per_album, on=album)

    grouped_df.loc[grouped_df['unique_artists'] > 1, artist] = 'Various Artists'
    grouped_df = grouped_df.groupby(target_col)['ms_played'].sum()
    grouped_df = grouped_df.reset_index()

    # convert ms to hours
    grouped_df['hours_played'] = grouped_df['ms_played'] / 3600000
    # sort by hours_played
    grouped_df = grouped_df.sort_values(by='hours_played', ascending=False)

    # get top 100
    grouped_df = grouped_df.head(top_n)

    album_col_name = target_col[0]
    artist_col_name = target_col[1]
    for i, r in grouped_df.iterrows():
        album = r[album_col_name]
        artist = r[artist_col_name]

        found = False
        attempts = 0
        temp_album, temp_artist = None, None
        while found == False:
            if attempts > 5:
                temp_album = album
                temp_artist = artist
            if attempts > 15:
                raise Exception(f'could not find album art for {album} by {artist} after {attempts} attempts')
            try:
                album_art_path = os.path.join(album_art_dir, f'{album.replace(" ", "_")}.jpg')
                if os.path.exists(album_art_path):
                    jpeg_dict[album] = album_art_path
                    found = True
                    break

                if temp_album is not None or temp_artist is not None:
                    if temp_artist is None:
                        temp_artist = artist

                    url = f'https://itunes.apple.com/search?term={temp_album.replace(" ", "%20")}%20{temp_artist.replace(" ", "%20")}&entity=album&limit=1'
                else:
                    url = f'https://itunes.apple.com/search?term={album.replace(" ", "%20")}%20{artist.replace(" ", "%20")}&entity=album&limit=1'

                response = requests.get(url)
                # if response is successful
                if response.status_code == 200:
                    response = json.loads(response.text)
                    if len(response['results']) == 0:
                        raise Exception('No results')
                    if 'artworkUrl100' in response['results'][0]:
                        artwork_url = response['results'][0]['artworkUrl100']
                        urllib.request.urlretrieve(artwork_url, album_art_path)
                        jpeg_dict[album] = album_art_path
                        found = True
                    else:
                        raise Exception('No artworkUrl100')
                else:
                    raise Exception('Response not 200')
            except:
                if attempts == 1:
                    temp_album = re.sub(r'\([^)]*\)', '', album)
                    temp_album = re.sub(r'\[[^)]*\]', '', temp_album)
                if attempts == 2:
                    temp_artist = ""
                if attempts == 3:
                    temp_album = album.split(":")[0].strip()
                    temp_album = temp_album.split("-")[0].strip()

                attempts += 1

    # save jpeg_dict to json
    jpeg_path = os.path.join(output_dir, 'jpeg_dict.json')
    with open(jpeg_path, 'w') as fp:
        json.dump(jpeg_dict, fp)

    # reset index
    grouped_df = grouped_df.reset_index(drop=True)

    return grouped_df, jpeg_dict


def load_image(image_path, img_size):
    # Load and resize the image to a custom size for the bar chart label
    img = Image.open(image_path)
    img = img.resize((img_size, img_size))
    return np.array(img)


def add_value_labels(ax, color, spacing=5):
    seen_rect = []
    for i in range(len(ax.patches)):
        rect = ax.patches[i]
        if rect not in seen_rect:
            seen_rect.append(rect)
        else:
            continue

        y_value = rect.get_height()
        x_value = rect.get_x() + rect.get_width() / 2

        space = spacing
        va = 'bottom'

        if y_value < 0:
            space *= -1
            va = 'top'

        label = '{:.2f}'.format(y_value) + " hrs"

        # Create annotation
        ax.annotate(
            label,
            (x_value, y_value),
            xytext=(0, space),
            textcoords="offset points",
            ha='center',
            color=color,
            size=20,
            va=va)

def create_image_barchart(labels, values, jpeg_dict, output_file, top_n, img_size=100, bar_width=.6, DPI=600, append_title="", years=None):
    plt.style.use('default')

    print(f"- Creating top {top_n} albums chart at {output_file}...")

    colors = get_discrete_colors()
    plot_color = colors[0]
    fig, ax = plt.subplots()

    for i, (label, value) in enumerate(zip(labels, values)):
        # Load the image corresponding to the label
        image_path = jpeg_dict[label]
        image = load_image(image_path, img_size)

        # Plot the bar
        x_pos = i
        ax.bar(x_pos, value, bar_width, align='center', color=plot_color, zorder=3)

        # Add the image as a label beneath the bar
        imagebox = OffsetImage(image, zoom=1.23)
        ab = AnnotationBbox(imagebox, (x_pos, 0), xybox=(0, -img_size / 1), frameon=False, xycoords='data', boxcoords="offset points", pad=8)
        ax.add_artist(ab)

    set_plot()

    axis_color, grid_color = get_axis_and_grid_colors()

    fontname = set_font()
    plt.rcParams['font.family'] = fontname

    ax.tick_params(axis='y', direction='in', color=axis_color)

    num_bars = len(labels)
    ax.set_xticks(range(num_bars))

    repeating_range = list(range(1, top_n + 1)) * int(num_bars / top_n)
    ax.set_xticklabels(repeating_range, color=axis_color, fontsize=50, fontweight='bold', fontfamily=fontname)
    ax.xaxis.set_tick_params(pad=200)

    ax.set_yticklabels([int(x) for x in plt.gca().get_yticks()], color=axis_color, fontsize=30, fontfamily=fontname)
    ax.yaxis.set_tick_params(pad=55)

    if int(num_bars / top_n) != 1:
        add_value_labels(ax, axis_color)

    plt.tick_params(axis='both', which='both', length=0)

    plt.gca().spines['top'].set_visible(False)
    plt.gca().spines['bottom'].set_visible(False)
    plt.gca().spines['left'].set_visible(False)
    plt.gca().spines['right'].set_visible(False)

    ax.set_ylabel('Hours Listened', color=axis_color, fontsize=40, labelpad=50, fontfamily=fontname)
    ax.set_title(f'Top {top_n} Albums{append_title}', color=axis_color, fontsize=60, pad=50, fontfamily=fontname)
    figure_width_inches = 12 * (len(labels) * (img_size / bar_width)) / DPI
    plt.gcf().set_size_inches(figure_width_inches, 20)  # Adjust figure size based on the number of bars
    plt.tight_layout()
    plt.savefig(output_file)

    plt.clf()
    plt.close()


def create_album_charts(df, output_dir, top_n=5, by_year=True):
    print(f"TOP ALBUMS")
    print(f"----------")
    top_albums_dir = os.path.join(output_dir, 'top_albums')
    if not os.path.exists(top_albums_dir):
        os.makedirs(top_albums_dir)

    df = df[df['album'] != 'Babylon']

    grouping_cols = ['album', 'artist']
    if by_year:
        # filter df by year
        full_labels = []
        full_values = []
        jpeg_master_dict = {}
        years = list(sorted(df['year'].unique()))
        for year in years:
            output_file = os.path.join(top_albums_dir, f'top_albums_{year}.png')
            if os.path.exists(output_file):
                continue

            temp_df = df[df['year'] == year]

            try:
                grouped_df, jpeg_dict = group_df_by_target(temp_df, grouping_cols, top_n, top_albums_dir)
            except:
                print(traceback.format_exc())
                print(f'Error grouping df for {year}, skipping...')
                continue

            labels = grouped_df[grouping_cols[0]].values
            full_labels.extend(labels)
            values = grouped_df['hours_played'].values

            full_values.extend(values)
            jpeg_master_dict.update(jpeg_dict)

            create_image_barchart(labels, values, jpeg_dict, output_file, top_n, append_title=f' {year}')

        if min(years) != max(years):
            output_file = os.path.join(top_albums_dir, f'top_albums_full.png')
            if not os.path.exists(output_file):
                create_image_barchart(full_labels, full_values, jpeg_master_dict, output_file, top_n, append_title=f' {min(years)} - {max(years)}', years=years)

    try:
        grouped_df, jpeg_dict = group_df_by_target(df, grouping_cols, top_n, top_albums_dir)
        labels = grouped_df[grouping_cols[0]].values
        values = grouped_df['hours_played'].values

        output_file = os.path.join(top_albums_dir, f'top_albums_all_time.png')
        if not os.path.exists(output_file):
            create_image_barchart(labels, values, jpeg_dict, output_file, top_n)
    except:
        print(traceback.format_exc())

    print()