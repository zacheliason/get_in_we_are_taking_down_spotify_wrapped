from src.plot_formatting import find_cleanest_columns, set_font, get_discrete_colors, get_axis_and_grid_colors
from matplotlib import pyplot as plt
import os


def create_track_charts(df, output_dir, top_n=20, darkmode=True):
    print(f"TOP TRACKS")
    print(f"-----------")

    track_output_dir = os.path.join(output_dir, 'top_tracks')
    if not os.path.exists(track_output_dir):
        os.makedirs(track_output_dir)

    df['sum_hours_played'] = df.groupby(['track', 'artist'])['ms_played'].transform('sum')/3600000
    df = df.sort_values(by=['sum_hours_played', 'year'], ascending=False)

    # create list of tuples of (track, artist) for top_n tracks
    top_tracks = df.drop_duplicates(subset=['track', 'artist'])[:top_n]
    top_tracks = [(i, x, y) for i, (x, y) in enumerate(list(zip(top_tracks['track'], top_tracks['artist'])))]

    full_df = df.copy()
    full_df = full_df.groupby(['track', 'year', 'artist']).sum()
    full_df = full_df.reset_index()
    full_df['sum_hours_played'] = full_df.groupby(['track', 'artist'])['ms_played'].transform('sum')/3600000
    full_df['hours_played'] = full_df.groupby(['track', 'artist', 'year'])['ms_played'].transform('sum')/3600000
    full_df = full_df.sort_values(by=['sum_hours_played', 'year'], ascending=True)
    full_df = full_df[['track', 'artist', 'year', 'hours_played', 'sum_hours_played']]

    # filter df by top track and artist
    df = df[df['track'].isin([x[1] for x in top_tracks]) & df['artist'].isin([x[2] for x in top_tracks])]
    df = df.groupby(['track', 'year', 'artist']).sum()
    df = df.reset_index()

    years = df['year'].unique()
    years.sort()

    # Complete df
    for year in years:
        for i, track, artist in top_tracks:
            year_df = df.loc[df['year'] == year]
            if not track in year_df['track'].values:
                # add new row for track, year with ms_played=0
                df = df.append({'track': track, 'artist': artist, 'year': year, 'ms_played': 0}, ignore_index=True)

    df['sum_hours_played'] = df.groupby(['track', 'artist'])['ms_played'].transform('sum')/3600000
    df['hours_played'] = df.groupby(['track', 'artist', 'year'])['ms_played'].transform('sum')/3600000
    df = df.sort_values(by=['sum_hours_played', 'year'], ascending=True)

    df = df[['track', 'artist', 'year', 'hours_played', 'sum_hours_played']]

    top_tracks.reverse()

    top_tracks_by_year_path = os.path.join(track_output_dir, 'top_tracks_all_time_by_year.png')
    if not os.path.exists(top_tracks_by_year_path):
        top_track_by_year(df, top_tracks, years, top_tracks_by_year_path, top_n=top_n, darkmode=darkmode)

    top_tracks_path = os.path.join(track_output_dir, 'top_tracks_all_time.png')
    if not os.path.exists(top_tracks_path):
        top_track(df, top_tracks_path, top_n=top_n, darkmode=darkmode)

    # group full_df by year
    for year in years:
        temp_df = full_df[full_df['year'] == year]
        year_path = os.path.join(track_output_dir, f'top_tracks_{year}.png')
        if os.path.exists(year_path):
            continue

        top_track(temp_df, year_path, top_n=top_n, darkmode=darkmode)

    print()


def top_track(df, output_path, top_n, darkmode=True):
    colors = get_discrete_colors()
    axis_color, grid_color = get_axis_and_grid_colors()

    if darkmode:
        title_color = "white"
        plt.style.use('dark_background')
    else:
        title_color = axis_color
        plt.style.use('default')

    print(f"- Creating top {top_n} tracks chart at {output_path}...")

    padding_amount = 20

    plt.rcParams['font.family'] = set_font()

    golden_ratio = (1 + 5 ** 0.5) / 2
    height = 10

    # get longest track name
    label_lengths = [len(f"{track}, {artist}") for track, artist in zip(df['track'], df['artist'])]
    label_adjustment = max(label_lengths) / 15

    fig, ax = plt.subplots(figsize=(height*golden_ratio + label_adjustment, height))
    plt.grid(True, axis='x', color=grid_color, linewidth=1, zorder=-999, linestyle='--')

    min_year = df['year'].min()
    max_year = df['year'].max()

    # df['sum_hours_played'] = df.groupby('track')['ms_played'].transform('sum') / 60000
    df = df[['track', 'artist', 'sum_hours_played']]
    df = df.drop_duplicates()
    df = df.sort_values(by='sum_hours_played', ascending=False)
    top_tracks = df.drop_duplicates(subset=['track', 'artist'])[:top_n]
    top_tracks = [(i, x, y, z) for i, (x, y, z) in enumerate(list(zip(top_tracks['track'], top_tracks['artist'], top_tracks['sum_hours_played'])))]

    top_tracks.reverse()

    for i, track, artist, hours in top_tracks:
        ax.barh(f"{track}, {artist}: #{i+1}", hours, color=colors[0], zorder=999, height=0.5)

    # Add title and axis names
    if min_year == max_year:
        title = f'Top {top_n} Tracks {min_year}'
    else:
        title = f'Top {top_n} Tracks {min_year}-{max_year}'

    plt.title(title, fontsize=20, fontweight='bold', color=title_color, pad=padding_amount)
    plt.ylabel('Track', fontsize=16, fontweight='bold', color=axis_color, labelpad=padding_amount)
    plt.xlabel('Hours Listened', fontsize=16, fontweight='bold', color=axis_color, labelpad=padding_amount)

    # Set spines
    ax.spines['left'].set_zorder(1000)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.spines['left'].set_visible(True)

    # Save figure
    plt.tight_layout()
    plt.savefig(output_path, dpi=600, bbox_inches='tight')

    plt.clf()
    plt.close()


def top_track_by_year(df, top_tracks, years, output_path, top_n=20, darkmode=True):
    colors = get_discrete_colors()
    axis_color = "#7a7a7a"
    grid_color = "#d4d4d4"
    if darkmode:
        title_color = "white"
        plt.style.use('dark_background')
    else:
        title_color = axis_color
        plt.style.use('default')

    print(f"- Creating top {top_n} tracks by year chart at {output_path}...")

    padding_amount = 20

    plt.rcParams['font.family'] = set_font()

    year_colors = colors[:len(years)]
    year_colors.reverse()

    golden_ratio = (1 + 5 ** 0.5) / 2
    height = 10

    label_adjustment = max([len(f"{track[1]}, {track[2]}: #{track[0]+1}") for track in top_tracks]) / 15

    fig, ax = plt.subplots(figsize=(height*golden_ratio + label_adjustment, height))
    plt.grid(True, axis='x', color=grid_color, linewidth=1, zorder=-999, linestyle='--')

    min_year = df['year'].min()
    max_year = df['year'].max()

    # Plot the stacked bars
    for track in top_tracks:
        bottom = None
        for i, year in enumerate(years):
            slice_df = df.loc[(df['track'] == track[1]) & (df['year'] == year), 'hours_played']
            hours_played_that_year = slice_df.values[0]

            ax.barh(f"{track[1]}, {track[2]}: #{track[0]+1}", hours_played_that_year, height=0.5, left=bottom, color=year_colors[i], label=year, zorder=999)
            if bottom is None:
                bottom = hours_played_that_year
            else:
                bottom += hours_played_that_year

    # Add title and axis names
    plt.title(f'Top {top_n} Tracks {min_year}-{max_year} (by Year)', fontsize=20, fontweight='bold', color=title_color)
    plt.ylabel('Track', fontsize=16, fontweight='bold', color=axis_color, labelpad=padding_amount)
    plt.xlabel('Hours Listened', fontsize=16, fontweight='bold', color=axis_color, labelpad=padding_amount)

    # Add legend
    handles, labels = ax.get_legend_handles_labels()
    handles = handles[:len(years)]
    labels = labels[:len(years)]
    handles.reverse()
    labels.reverse()
    ax.legend(handles, labels, title='Year', loc='center', bbox_to_anchor=(0.5, -0.35), borderaxespad=0., title_fontsize=12, frameon=False, ncol=find_cleanest_columns(len(labels)))

    # Set spines
    ax.spines['left'].set_zorder(1000)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.spines['left'].set_visible(True)

    # Save figure
    plt.tight_layout()
    plt.savefig(output_path, dpi=600, bbox_inches='tight')

    plt.clf()
    plt.close()
