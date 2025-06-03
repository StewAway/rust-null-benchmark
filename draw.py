import os
import json
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import colors, ticker

# Parameters
base_dirs = ["results_none", "results_mq"]
patterns = ["seq_write", "seq_read", "rand_write", "rand_read"]
block_sizes = ["4k", "8k", "16k", "32k", "64k", "128k"]
num_jobs = ["1", "2", "3", "4"]
bs_labels = [int(bs.replace("k", "")) for bs in block_sizes]
nj_labels = [int(nj) for nj in num_jobs]
label_font_conf = {"size": 18}
data = []

# Load data for both schedulers
for sched in base_dirs:
    matrices = []
    for pattern in patterns:
        matrix = np.full((len(block_sizes), len(num_jobs)), np.nan)
        for i, bs in enumerate(block_sizes):
            for j, nj in enumerate(num_jobs):
                try:
                    base_path = os.path.expanduser(f"./{sched}/{pattern}")
                    c_file = os.path.join(base_path, f"c_bs{bs}_jobs{nj}.json")
                    r_file = os.path.join(base_path, f"rust_bs{bs}_jobs{nj}.json")
                    with open(c_file) as fc, open(r_file) as fr:
                        target = "read" if "read" in pattern else "write"
                        
                        c_bw = json.load(fc)["jobs"][0][target]["bw"] / 1024
                        r_bw = json.load(fr)["jobs"][0][target]["bw"] / 1024
                        
                        matrix[i][j] = ((r_bw - c_bw) / c_bw) * 100
                except Exception:
                    matrix[i][j] = np.nan
        matrices.append(matrix)
    data.append(matrices)

# Custom heatmap functions
def heatmap(data, row_labels, col_labels, ax=None, **kwargs):
    if ax is None:
        ax = plt.gca()
    im = ax.imshow(data, **kwargs)
    ax.set_xticks(np.arange(data.shape[1]), labels=col_labels, **label_font_conf)
    ax.set_yticks(np.arange(data.shape[0]), labels=row_labels, **label_font_conf)
    ax.tick_params(bottom=False, labelbottom=True, left=False, labelleft=True)
    plt.setp(ax.get_xticklabels(), ha="center", rotation_mode="anchor")
    ax.spines[:].set_visible(False)
    ax.set_xticks(np.arange(data.shape[1]+1)-.5, minor=True)
    ax.set_yticks(np.arange(data.shape[0]+1)-.5, minor=True)
    ax.grid(which="minor", color="w", linestyle='-', linewidth=3)
    ax.tick_params(which="minor", bottom=False, left=False)
    return im

def annotate_heatmap(im, data=None, valfmt="{x:.0f}", textcolors=("black", "white"), threshold=None, **textkw):
    if data is None:
        data = im.get_array()
    if threshold is None:
        threshold = im.norm(data.max())/2.
    kw = dict(horizontalalignment="center", verticalalignment="center")
    kw.update(textkw)
    valfmt = ticker.StrMethodFormatter(valfmt)
    for i in range(data.shape[0]):
        for j in range(data.shape[1]):
            kw.update(color=textcolors[int(im.norm(data[i, j]) > threshold)])
            im.axes.text(j, i, valfmt(data[i, j], None), **kw)

# Plot layout
fig, axs = plt.subplots(2, 4, figsize=(14, 6), dpi=100)
fig.supylabel("blocksize (KiB)", x=0.03, y=0.5, **label_font_conf)
fig.supxlabel("Number of IO jobs", x=0.44, y=0, **label_font_conf)

images = []
titles = ["seq write", "seq read", "rand write", "rand read"]
for i in range(2):  # sched=none (0), mq (1)
    for j in range(4):  # 4 IO patterns
        matrix = data[i][j]
        im = heatmap(matrix, bs_labels, nj_labels, ax=axs[i, j],
                     cmap="RdYlGn", aspect='auto', vmin=-40, vmax=40)
        annotate_heatmap(im, matrix, valfmt="{x:.0f}", fontsize=13,
                         textcolors=("#A52A2A", "darkgreen"))
        axs[i, j].label_outer()
        axs[i, j].set_title(titles[j], fontsize=20)
        images.append(im)

cbar = fig.colorbar(images[0], ax=axs, pad=0.05)
cbar.ax.tick_params(labelsize=16)
cbar.set_label("The Performance Superiority of Rust Over C (%)", size=16)
axs[0, 0].set_ylabel('sched=None', size=16)
axs[1, 0].set_ylabel('sched=mq-deadline', size=16)
plt.savefig("figure9_reproduction.pdf", bbox_inches="tight")
plt.show()
