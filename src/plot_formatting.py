from matplotlib import font_manager
import matplotlib.ticker as mtick
import matplotlib.pyplot as plt
import matplotlib

def get_axis_and_grid_colors():
	axis_color = "#7a7a7a"
	grid_color = "#d4d4d4"
	return axis_color, grid_color


def get_discrete_colors():
	return ['#ff472e', '#00a99d', '#ff7bac', '#8cc63f', '#4662eb', '#d9e021', '#662d91', '#fdfdb8', '#ffca1c', '#bdc6bc', '#ff472e', '#00a99d', '#ff7bac', '#8cc63f', '#4662eb', '#d9e021', '#662d91', '#fdfdb8', '#ffca1c', '#bdc6bc']


def set_font():
	font_info = {
		'dir': "Work_Sans",
		'name': "Work Sans"
	}

	fonts = font_manager.findSystemFonts(fontpaths=font_info['dir'])
	for font in fonts:
		font_manager.fontManager.addfont(font)
	fontname = font_info['name']
	return fontname


def set_plot():
	axis_color = "#7a7a7a"
	grid_color = "#d4d4d4"
	colors = ["#dc523f", "#662d91", "#00a99d", "#ff7bac", "#ffca1c", "#8cc63f", "#4662eb", "#bdc6bc", "#d9e021",
	          "#c2a089", "#fdfdb8", "#dc523f", "#662d91", "#00a99d", "#ff7bac", "#ffca1c", "#8cc63f", "#4662eb",
	          "#bdc6bc", "#d9e021", "#c2a089", "#fdfdb8"]

	font_dir = '../Work_Sans'
	fonts = font_manager.findSystemFonts(fontpaths=font_dir)
	for font in fonts:
		font_manager.fontManager.addfont(font)

	fontname = "Work Sans"
	plt.rcParams['font.family'] = fontname

	plt.legend(loc='center left',
	           bbox_to_anchor=(1, 0.5),
	           frameon=False)

	graph_color = colors[0]

	plt.tick_params(
		axis='both',
		which='both',
		bottom=True,
		top=False,
		left=False,
		right=False,
		labelbottom=True,
		labelleft=True,
	)

	matplotlib.rc('axes', edgecolor=axis_color)
	plt.grid(True, axis='y', color=grid_color, linewidth=2, zorder=-1)
	plt.gca().yaxis.set_major_formatter(plt.matplotlib.ticker.StrMethodFormatter('{x:,.0f}'))

	locs, labels = plt.yticks()  # Get the current locations and labels.
	labels = ['{:,.0f}'.format(x) for x in locs]
	labels = [x.replace("-", "") for x in labels]

	plt.yticks(locs, labels, color=axis_color)

	plt.rcParams['axes.labelcolor'] = axis_color
	plt.rcParams['font.family'] = "Work Sans"
	plt.rcParams['text.color'] = axis_color
	plt.rcParams['axes.spines.left'] = False
	plt.rcParams['axes.spines.top'] = False
	plt.rcParams['axes.spines.right'] = False


def find_cleanest_columns(N):
	import math

	# Find the integer square root (rounded down) of N
	num_columns = int(math.sqrt(N))

	# Find the divisors of N (excluding 1 and N)
	divisors = [i for i in range(2, N) if N % i == 0]

	# Choose the divisor pair that results in a balanced layout
	min_diff = float('inf')
	best_columns = num_columns

	for divisor in divisors:
		columns = N // divisor
		rows = divisor
		diff = abs(rows - columns)

		if diff < min_diff:
			min_diff = diff
			best_columns = columns

	return best_columns
