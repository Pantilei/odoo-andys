from matplotlib import pyplot as plt
from scipy import interpolate
import numpy as np
import io
import base64


def get_char_svg(x_cat, y1, y2, legend):
    plt.rcParams["figure.figsize"] = [7.50, 3.50]
    plt.rcParams["figure.autolayout"] = True

    MONTHS = [cat for x, cat in x_cat]
    MONTHS_INT = [x for x, cat in x_cat]
    print(MONTHS)
    print(MONTHS_INT)

    ax1 = plt.subplot()
    ax2 = ax1.twinx()

    l1 = ax1.scatter(MONTHS, y1, color="red", marker="o")
    for i, txt in enumerate(y1):
        ax1.annotate(txt, (MONTHS[i], y1[i]), xytext=(
            MONTHS_INT[i]-0.35, y1[i]))
    l2 = ax2.scatter(MONTHS, y2, color="orange", marker="o")
    for i, txt in enumerate(y2):
        ax2.annotate(txt, (MONTHS[i], y2[i]), xytext=(
            MONTHS_INT[i]+0.2, y2[i]))

    plt.legend([l1, l2], legend)
    plt.grid()

    bspline_y1 = interpolate.interp1d(MONTHS_INT, y1, kind="quadratic")
    bspline_y2 = interpolate.interp1d(MONTHS_INT, y2, kind="quadratic")

    x = np.linspace(0, 11, 100)
    y1_new = bspline_y1(x)
    y2_new = bspline_y2(x)

    l1, = ax1.plot(x, y1_new, color="red")
    l2, = ax2.plot(x, y2_new, color="orange")

    source = io.BytesIO()
    plt.savefig(source, format="svg")
    plt.close()

    return base64.b64encode(source.getvalue())
