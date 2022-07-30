import warnings
from matplotlib import pyplot as plt
from scipy import interpolate
import numpy as np
import io
import base64
import itertools

plt.set_loglevel('WARNING')
warnings.filterwarnings("ignore")

marker = itertools.cycle(
    (',', '+', '.', 'o', '*', 'v', '1', '2', '3', '4', '8', 'D', 's', 'p', 'x'))


def get_double_y_axis_chart_png(x_cat, y1, y2, legend, legend_loc=None, legend_ncol=None):
    plt.rcParams["figure.autolayout"] = True
    fig, ax1 = plt.subplots(figsize=(8.0, 4.50))
    ax2 = ax1.twinx()

    if not legend_loc:
        legend_loc = (0, -0.15)
    if not legend_ncol:
        legend_ncol = 2

    MONTHS = [cat for x, cat in x_cat]
    MONTHS_INT = [x for x, cat in x_cat]

    # ax1.set_ylim(bottom=0, top=max(y1)+max(y1)/10)
    # ax2.set_ylim(bottom=0, top=max(y2)+max(y2)/10)
    ax1.grid(visible=True, which='both', axis="both",
             color='#CCCCCC', linestyle='--', linewidth=1)
    ax2.grid(visible=True, which='both',
             color='#CCCCCC', linestyle=':', linewidth=1)

    l1 = ax1.plot(MONTHS, y1, color="red", marker="o", label=legend[0])

    max_y1 = max(y1)
    min_y1 = min(y1)
    y1_range = max_y1 - min_y1
    for i, txt in enumerate(y1):
        ax1.annotate(txt, (MONTHS[i], y1[i]), xytext=(
            MONTHS_INT[i]-0.35, y1[i]-y1_range*0.04))
    l2 = ax2.plot(MONTHS, y2, color="orange", marker="o", label=legend[1])
    for i, txt in enumerate(y2):
        ax2.annotate(txt, (MONTHS[i], y2[i]), xytext=(
            MONTHS_INT[i]+0.2, y2[i]))

    ax1.legend(handles=l1+l2, loc=legend_loc, ncol=legend_ncol)

    source = io.BytesIO()
    plt.savefig(source, format="png")
    plt.close()

    return base64.b64encode(source.getvalue())


def get_multi_line_png(x_cat, ys, legend, legend_loc=None, legend_ncol=None, figsize=None):

    if not legend_loc:
        legend_loc = (0, -0.40)
    if not legend_ncol:
        legend_ncol = 2

    if not figsize:
        figsize = [11, 6]

    plt.rcParams["figure.figsize"] = figsize
    plt.rcParams["figure.autolayout"] = True

    MONTHS = [cat for x, cat in x_cat]
    MONTHS_INT = [x for x, cat in x_cat]

    for idx, y in enumerate(ys):
        plt.plot(MONTHS, y, marker=next(marker),
                 markersize=10, label=legend[idx])
        for i, txt in enumerate(y):
            plt.annotate(txt, (MONTHS[i], y[i]), xytext=(
                MONTHS_INT[i]-0.25, y[i]))

    plt.legend(loc=legend_loc, ncol=legend_ncol)
    plt.grid()

    source = io.BytesIO()
    plt.savefig(source, format="png", dpi=150)
    plt.close()

    return base64.b64encode(source.getvalue())


def short_date(dt):
    a = dt.strftime('%m/%Y').split('/')
    return "/".join([a[0], a[1][2:]])


def get_double_y_axis_chart_png_old(x_cat, y1, y2, legend):
    plt.rcParams["figure.figsize"] = [7.50, 3.50]
    plt.rcParams["figure.autolayout"] = True

    MONTHS = [cat for x, cat in x_cat]
    MONTHS_INT = [x for x, cat in x_cat]

    ax1 = plt.subplot()
    ax2 = ax1.twinx()
    # ax1.set_ylim(bottom=0, top=max(y1)+max(y1)/10)
    # ax2.set_ylim(bottom=0, top=max(y2)+max(y2)/10)
    ax1.grid(visible=True, which='both', axis="both",
             color='#CCCCCC', linestyle='--', linewidth=1)
    ax2.grid(visible=True, which='both',
             color='#CCCCCC', linestyle=':', linewidth=1)

    l1 = ax1.plot(MONTHS, y1, color="red", marker="o")
    for i, txt in enumerate(y1):
        ax1.annotate(txt, (MONTHS[i], y1[i]), xytext=(
            MONTHS_INT[i]-0.35, y1[i]))
    l2 = ax2.plot(MONTHS, y2, color="orange", marker="o")
    for i, txt in enumerate(y2):
        ax2.annotate(txt, (MONTHS[i], y2[i]), xytext=(
            MONTHS_INT[i]+0.2, y2[i]))

    plt.legend([l1, l2], legend)

    bspline_y1 = interpolate.Akima1DInterpolator(MONTHS_INT, y1)
    bspline_y2 = interpolate.Akima1DInterpolator(MONTHS_INT, y2)
    x = np.linspace(0, 11, 100)
    y1_new = bspline_y1(x)
    y2_new = bspline_y2(x)

    l1, = ax1.plot(x, y1_new, color="red")
    l2, = ax2.plot(x, y2_new, color="orange")

    source = io.BytesIO()
    plt.savefig(source, format="png")
    plt.close()

    return base64.b64encode(source.getvalue())
