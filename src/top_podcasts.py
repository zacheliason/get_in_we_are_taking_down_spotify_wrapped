from src.plot_formatting import find_cleanest_columns, set_font, get_discrete_colors, get_axis_and_grid_colors
from matplotlib import pyplot as plt
import os


def create_podcast_charts(df, output_dir, top_n=20, darkmode=True):
    print(f"TOP PODCASTS")
    print(f"-----------")

    podcast_output_dir = os.path.join(output_dir, 'top_podcasts')
    if not os.path.exists(podcast_output_dir):
        os.makedirs(podcast_output_dir)

    df['sum_hours_played'] = df.groupby('podcast')['ms_played'].transform('sum')
    df = df.sort_values(by=['sum_hours_played', 'year'], ascending=False)
    top_podcasts = df['podcast'].unique()[:top_n]

    full_df = df.copy()
    full_df = full_df.groupby(['year', 'podcast']).sum()
    full_df = full_df.reset_index()

    df = df[df['podcast'].isin(top_podcasts)]
    df = df.groupby(['podcast', 'year']).sum()
    df = df.reset_index()

    df = df[['podcast', 'year', 'ms_played']]

    years = df['year'].unique()
    # Complete df
    for year in years:
        for podcast in top_podcasts:
            if podcast not in df.loc[df['year'] == year]['podcast'].values:
                # add new row for podcast, year with ms_played=0
                df = df.append({'podcast': podcast, 'year': year, 'ms_played': 0}, ignore_index=True)

    top_podcasts = [(i, x) for i, x in enumerate(top_podcasts)]
    top_podcasts.reverse()

    podcast_path_by_year = os.path.join(podcast_output_dir, 'top_podcasts_all_time_by_year.png')
    podcast_path = os.path.join(podcast_output_dir, 'top_podcasts_all_time.png')

    df.loc[:, 'sum_hours_played'] = df.groupby('podcast')['ms_played'].transform('sum') / 3600000
    if not os.path.exists(podcast_path_by_year):
        top_podcast_by_year(df, top_podcasts, years, podcast_path_by_year, top_n=top_n, darkmode=darkmode)
    if not os.path.exists(podcast_path):
        top_podcast(df, podcast_path, top_n=top_n, darkmode=darkmode)

    # group full_df by year
    for year in years:
        temp_df = full_df[full_df['year'] == year]
        year_path = os.path.join(podcast_output_dir, f'top_podcasts_{year}.png')
        if os.path.exists(year_path):
            continue

        top_podcast(temp_df, year_path, top_n=top_n, darkmode=darkmode)

    print()


def top_podcast(df, output_path, top_n, darkmode=True):
    colors = get_discrete_colors()
    axis_color, grid_color = get_axis_and_grid_colors()

    if darkmode:
        title_color = "white"
        plt.style.use('dark_background')
    else:
        title_color = axis_color
        plt.style.use('default')

    print(f"- Creating top {top_n} podcasts chart at {output_path}...")

    padding_amount = 20

    plt.rcParams['font.family'] = set_font()

    golden_ratio = (1 + 5 ** 0.5) / 2
    height = 10
    fig, ax = plt.subplots(figsize=(height*golden_ratio, height))
    plt.grid(True, axis='x', color=grid_color, linewidth=1, zorder=-999, linestyle='--')

    min_year = df['year'].min()
    max_year = df['year'].max()

    df['sum_hours_played'] = df.groupby(['podcast'])['ms_played'].transform('sum') / 3600000
    df = df[['podcast', 'sum_hours_played']]
    df = df.drop_duplicates()
    df = df.sort_values(by='sum_hours_played', ascending=False)
    top_podcasts = [(i, x) for i, x in enumerate(df['podcast'].unique())][:top_n]
    top_podcasts.reverse()

    for i, podcast in top_podcasts:
        ax.barh(f"{podcast}: #{i+1}", df[df['podcast'] == podcast]['sum_hours_played'], color=colors[0], zorder=999, height=0.5)

    # Add title and axis names
    if min_year == max_year:
        title = f'Top {top_n} Podcasts {min_year}'
    else:
        title = f'Top {top_n} Podcasts {min_year}-{max_year}'

    plt.title(title, fontsize=20, fontweight='bold', color=title_color, pad=padding_amount)
    plt.ylabel('Podcast', fontsize=16, fontweight='bold', color=axis_color, labelpad=padding_amount)
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


def top_podcast_by_year(df, top_podcasts, years, output_path, top_n=20, darkmode=True):
    colors = get_discrete_colors()
    axis_color = "#7a7a7a"
    grid_color = "#d4d4d4"
    if darkmode:
        title_color = "white"
        plt.style.use('dark_background')
    else:
        title_color = axis_color
        plt.style.use('default')

    print(f"- Creating top {top_n} podcasts by year chart at {output_path}...")

    padding_amount = 20

    plt.rcParams['font.family'] = set_font()

    year_colors = colors[:len(years)]
    year_colors.reverse()

    golden_ratio = (1 + 5 ** 0.5) / 2
    height = 10
    fig, ax = plt.subplots(figsize=(height*golden_ratio, height))
    plt.grid(True, axis='x', color=grid_color, linewidth=1, zorder=-999, linestyle='--')

    min_year = df['year'].min()
    max_year = df['year'].max()

    # Plot the stacked bars
    for podcast in top_podcasts:
        bottom = None
        for i, year in enumerate(years):
            hours_played_that_year = df.loc[(df['podcast'] == podcast[1]) & (df['year'] == year), 'ms_played'].values[0]/3600000

            ax.barh(f"{podcast[1]}: #{podcast[0]+1}", hours_played_that_year, height=0.5, left=bottom, color=year_colors[i], label=year, zorder=999)
            if bottom is None:
                bottom = hours_played_that_year
            else:
                bottom += hours_played_that_year

    # Add title and axis names
    plt.title(f'Top {top_n} Podcasts {min_year}-{max_year} (by Year)', fontsize=20, fontweight='bold', color=title_color, pad=padding_amount)
    plt.ylabel('Podcast', fontsize=16, fontweight='bold', color=axis_color, labelpad=padding_amount)
    plt.xlabel('Hours Listened', fontsize=16, fontweight='bold', color=axis_color, labelpad=padding_amount)

    # Add legend
    handles, labels = ax.get_legend_handles_labels()
    handles = handles[:len(years)]
    labels = labels[:len(years)]
    handles.reverse()
    labels.reverse()
    ax.legend(handles, labels, title='Year', loc='center', bbox_to_anchor=(0.5, -0.2), borderaxespad=0., title_fontsize=12, frameon=False, ncol=find_cleanest_columns(len(labels)))

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
