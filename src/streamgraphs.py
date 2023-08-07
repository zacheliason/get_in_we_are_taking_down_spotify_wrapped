from src.plot_formatting import set_font, get_discrete_colors, get_axis_and_grid_colors
from matplotlib.dates import YearLocator, MonthLocator, DateFormatter
from scipy.ndimage import gaussian_filter1d
from matplotlib import pyplot as plt
from scipy import stats
import pandas as pd
import numpy as np
import traceback
import os

pd.options.mode.chained_assignment = None


def format_hours(hours):
	if hours < 1:
		return f'{int(hours*60)} min'
	elif hours < 30:
		return f'{int(hours)} hrs, {int((hours - int(hours))*60)} min'
	else:
		return f'{int(hours)} hrs'


def gaussian_smooth(x, y, sd):
	weights = np.array([stats.norm.pdf(x, m, sd) for m in x])
	weights = weights / weights.sum(1)
	return (weights * y).sum(1)

def create_streamgraphs(df, output_dir, top_n=10, darkmode=True, podcasts=False):
	print(f"STREAMGRAPHS")
	print(f"-----------")

	if not podcasts:
		groupings = [['track', 'artist'], ['artist'], ['album', 'artist']]
	else:
		groupings = [['podcast']]

	if top_n > 10:
		print(f'WARNING: top_n={top_n} is greater than 10. Replacing with 10.')
		top_n = 10

	min_year = df['year'].min()
	max_year = df['year'].max()

	for grouping in groupings:
		grouping_dir = os.path.join(output_dir, f'top_{grouping[0]}s')

		if not os.path.exists(grouping_dir):
			os.makedirs(grouping_dir)

		full_streamgraph_path = os.path.join(grouping_dir, f'streamgraph_top_{grouping[0]}s_{min_year}-{max_year}.png')
		if not os.path.exists(full_streamgraph_path):
			print(f'- Creating {grouping[0]}s streamgraphs at {grouping_dir}...')
			create_streamgraph(df, full_streamgraph_path, group_target=grouping, top_n=top_n, darkmode=darkmode)

		for year in df['year'].unique():
			year_df = df[df['year'] == year]
			year_streamgraph_path = os.path.join(grouping_dir, f'streamgraph_top_{grouping[0]}s_{year}.png')
			if os.path.exists(year_streamgraph_path):
				continue

			try:
				create_streamgraph(year_df, year_streamgraph_path, group_target=grouping, top_n=top_n, darkmode=darkmode)
			except:
				print(traceback.format_exc())
				print(f'Error creating streamgraph for {grouping[0]}, {year}')

	print()


def create_streamgraph(df, output_path, group_target, top_n=10, darkmode=True):
	if darkmode:
		plt.style.use('dark_background')

	padding_amount = 20
	colors = get_discrete_colors()

	axis_color, grid_color = get_axis_and_grid_colors()

	plt.rcParams['font.family'] = set_font()

	min_year = df['year'].min()
	max_year = df['year'].max()

	multiyear = False
	resample_value = "W"
	if min_year != max_year:
		multiyear = True
		resample_value = "M"

	# regex clean up entries
	if group_target[0] == 'track' or group_target[0] == 'album':
		df.loc[:, group_target[0]] = df[group_target[0]].replace(r' -.*', '', regex=True)
		df.loc[:, group_target[0]] = df[group_target[0]].replace(r' \(.+\)', '', regex=True)

	df.loc[:, 'sum_hours_played'] = df.groupby(group_target)['ms_played'].transform('sum') / 3600000
	top_targets = df.sort_values(by=['sum_hours_played'], ascending=False)[group_target[0]].unique()[:top_n]
	df = df[df[group_target[0]].isin(top_targets)]

	group_cols = group_target + ['sum_hours_played']
	targets_to_hours = df[group_cols].drop_duplicates(subset=group_target[0]).sort_values(by=['sum_hours_played'], ascending=False).set_index(group_target[0]).to_dict()['sum_hours_played']
	if len(group_target) > 1:
		targets_to_artists = df[group_cols].drop_duplicates(subset=group_target[0]).sort_values(by=['sum_hours_played'],ascending=False).set_index(group_target[0]).to_dict()[group_target[1]]

	# Convert the 'ts' column to datetime and set it as the DataFrame index
	df.loc[:, 'ts'] = pd.to_datetime(df['ts'])
	df.set_index('ts', inplace=True)

	# Group by 'target' and resample data by month, summing the 'ms_played' for each target
	grouped_df = df.groupby(group_target[0]).resample(resample_value)['ms_played'].sum().unstack(level=0).fillna(0)

	smooth = grouped_df.copy()
	# Create a new datetime index with hourly intervals using time interpolation
	start_time = smooth.index.min()
	end_time = smooth.index.max()
	hourly_index = pd.date_range(start=start_time, end=end_time, freq='1H')

	# Reindex the DataFrame with the hourly index and use time interpolation
	smooth = smooth.reindex(hourly_index).interpolate(method='linear')

	# Smoothing factor (adjust as needed for desired smoothing)
	sigma = len(smooth) / 200

	for col in smooth.columns:
		smooth[col] = gaussian_filter1d(smooth[col], sigma)

	if not multiyear:
		smooth['year'] = smooth.index.year
		smooth = smooth[smooth['year'] == min_year]
		smooth.drop('year', axis=1, inplace=True)
		smooth = smooth[:-12]

	smooth = smooth[top_targets]

	golden_ratio = (1 + 5 ** 0.5) / 2
	height = 10

	if multiyear:
		LEGEND_FONTSIZE = 16
		width = height*golden_ratio * (max_year - min_year) / 3
		if width > 50:
			width = 50
		DPI = 300
	else:
		LEGEND_FONTSIZE = 10
		DPI = 600
		width = height*golden_ratio

	fig, ax = plt.subplots(figsize=(width, height))

	ax.stackplot(smooth.index, smooth.values.T, labels=smooth.columns, colors=colors, baseline="sym", zorder=1000)

	handles, labels = ax.get_legend_handles_labels()
	legend_dict = dict(zip(labels, handles))

	new_handles = []
	for target in top_targets:
		new_handles.append(legend_dict[target])

	# Legend below the graph in two columns, centered
	new_handles, top_targets = ax.get_legend_handles_labels()

	if len(group_target) > 1:
		new_labels = [f"{i + 1}. {x}, {targets_to_artists[x]}: {format_hours(targets_to_hours[x])}" for i, x in enumerate(top_targets)]
	else:
		new_labels = [f"{i+1}. {x}: {format_hours(targets_to_hours[x])}" for i, x in enumerate(top_targets)]
	ax.legend(new_handles, new_labels, loc='center', bbox_to_anchor=(0.5, -0.35), borderaxespad=0., title_fontsize=16, fontsize=LEGEND_FONTSIZE, frameon=False, ncol=2)

	if multiyear:
		title = f"Top {top_n} {group_target[0].capitalize()}s ({min_year}-{max_year})"

		ax.xaxis.set_major_formatter(DateFormatter('%Y'))
		ax.xaxis.set_minor_locator(MonthLocator(bymonth=[1, 4, 7, 10]))
		ax.xaxis.set_major_locator(YearLocator())

		ax.xaxis.grid(which='major', linestyle='-', color=grid_color, zorder=-1000)
		ax.xaxis.grid(which='minor', linestyle=':', color=grid_color, zorder=-1000)
	else:
		title = f"Top {top_n} {group_target[0].title()}s of {min_year}"
		ax.xaxis.set_major_locator(MonthLocator())
		ax.xaxis.set_major_formatter(DateFormatter('%b'))
		ax.xaxis.grid(which='major', linestyle='--', color=grid_color, zorder=-1000)

	# Tick formatting
	ax.tick_params(axis='x', which='both', length=0)
	ax.tick_params(axis='y', which='both', length=0)
	ax.set_yticklabels([])

	for tick in ax.xaxis.get_major_ticks():
		tick.label.set_fontsize(14)
		tick.label.set_fontweight('bold')
		tick.label.set_color(grid_color)

	plt.title(title, fontsize=30, fontweight='bold', color=grid_color, pad=padding_amount)

	# Set spines
	ax.spines['top'].set_visible(False)
	ax.spines['right'].set_visible(False)
	ax.spines['bottom'].set_visible(False)
	ax.spines['left'].set_visible(False)

	plt.tight_layout()
	plt.savefig(output_path, dpi=DPI, facecolor=fig.get_facecolor(), edgecolor='none')

	plt.clf()
	plt.close()
