import numpy as np
import matplotlib.pyplot as plt
import torch
import matplotlib.colors as mcolors
from util import is_outlier

_tableaeu_colors = list(mcolors.TABLEAU_COLORS.keys())

def plot_2d_log_density(points, labels, density_model, resolution=100, levels=10, label_names=None):
    """ Makes a 2d log-density plot of a space. 
    
    Parameters:
    -----------
    points : torch.tensor, shape [N, 2]
        points to place as points in the density space.
    labels : torch.tensor, shape [N]
        Labels for the points to place (will be added to the legend).
    density_model : torch.nn.Module
        A model that evaluates the logit space density.
    resolution : int
        Resolution for the plot. Default: 100
    levels : int
        How many countour levels. Default: 10
    label_names : dict or None
        Names of the labels. If None is given, each label is rerred to by its number.
    
    Returns:
    --------
    plt.Figure
        The plot.
    plt.axis.Axes
        The axis of the plot.
    """
    points = points.cpu().numpy()
    labels = labels.cpu().numpy()

    if points.shape[1] != 2:
        print(f'Cant plot 2d density for logit space of dimension {points.shape[1]}')
        return None, None

    if label_names is None:
        label_names = {label : f'{label}' for label in np.unique(labels)}

    density_model = density_model.cpu()

    (xmin, ymin), (xmax, ymax) = points.min(axis=0), points.max(axis=0)
    mesh = np.array(np.meshgrid(np.linspace(xmin, xmax, resolution), np.linspace(ymin, ymax, resolution))).reshape(2, -1).T
    mesh = torch.tensor(mesh)
    mesh_log_density = np.log(density_model(mesh).cpu().numpy().T.reshape(resolution, resolution))
    xx, yy = mesh.cpu().numpy().T.reshape(2, resolution, resolution)
    fig, ax = plt.subplots(1, 1)
    ax.contourf(xx, yy, mesh_log_density, levels=20)
    for label, name in label_names.items():
        ax.scatter(points[:, 0][labels==label], points[:, 1][labels==label], c=_tableaeu_colors[label], label=name, marker='x', linewidth=1.0)
    ax.legend()
    return fig, ax

def plot_log_density_histograms(log_density, labels, label_names=None, bins=20, overlapping=True):
    """ Plots an (overlapping) histogram for log-densities for all labels.
    
    Parameters:
    -----------
    log_density : torch.tensor, shape [N]
        Log-densities to plot a histogram of.
    labels : torch.tensor, shape [N]
        Label for each point.
    label_names : dict or None
        Name for each label in the legend. If None is given, it is set to the label's idx.
    bins : int
        How many bins to use. Default: 20
    overlapping : bool
        If True, the log densities will be placed in one plot that overlaps. If False, subplots for each log density will be built.
    
    Returns:
    --------
    plt.Figure
        The plot.
    plt.axis.Axes
        The axis of the plot or an array of axis if `overlapping` is set to `False`.
    """
    log_density = log_density.cpu().numpy()
    labels = labels.cpu().numpy()

    if label_names is None:
        label_names = {label : f'{label}' for label in np.unique(labels)}

    log_density_clean = log_density[~is_outlier(log_density)]
    try:
        bins = np.linspace(max(-2000, log_density_clean.min()), min(2000, log_density_clean.max()), bins + 1)
    except:
        bins = np.linspace(-2000, 2000, bins + 1)
    if overlapping:
        fig, ax = plt.subplots(1, 1)
        for label in label_names:
            ax.hist(log_density[labels == label], bins, alpha=0.5, label=label_names[label], density=True)
        ax.legend()
        return fig, ax
    else:
        fig, axs = plt.subplots(int(np.ceil(len(label_names) / 3)), 3, sharex=True, sharey=True)
        axs = axs.flatten()
        for idx, label in enumerate(label_names):
            axs[idx].hist(log_density[labels == label], bins, alpha=0.5, label=label_names[label], density=True)
            axs[idx].legend()
        return fig, axs

