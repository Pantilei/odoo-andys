import warnings
from matplotlib import pyplot as plt
from scipy import interpolate
import numpy as np
import io
import base64

plt.set_loglevel('WARNING')
warnings.filterwarnings("ignore")


def get_char_svg(x_cat, y1, y2, legend):
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

    l1 = ax1.scatter(MONTHS, y1, color="red", marker="o")
    for i, txt in enumerate(y1):
        ax1.annotate(txt, (MONTHS[i], y1[i]), xytext=(
            MONTHS_INT[i]-0.35, y1[i]))
    l2 = ax2.scatter(MONTHS, y2, color="orange", marker="o")
    for i, txt in enumerate(y2):
        ax2.annotate(txt, (MONTHS[i], y2[i]), xytext=(
            MONTHS_INT[i]+0.2, y2[i]))

    plt.legend([l1, l2], legend)
    # plt.grid()

    # bspline_y1 = interpolate.interp1d(MONTHS_INT, y1, kind="quadratic")
    # bspline_y2 = interpolate.interp1d(MONTHS_INT, y2, kind="quadratic")

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


def short_date(dt):
    a = dt.strftime('%m/%Y').split('/')
    return "/".join([a[0], a[1][2:]])
