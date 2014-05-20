# This file is part of QuTiP: Quantum Toolbox in Python.
#
#    Copyright (c) 2011 and later, Paul D. Nation and Robert J. Johansson.
#    All rights reserved.
#
#    Redistribution and use in source and binary forms, with or without
#    modification, are permitted provided that the following conditions are
#    met:
#
#    1. Redistributions of source code must retain the above copyright notice,
#       this list of conditions and the following disclaimer.
#
#    2. Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#
#    3. Neither the name of the QuTiP: Quantum Toolbox in Python nor the names
#       of its contributors may be used to endorse or promote products derived
#       from this software without specific prior written permission.
#
#    THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
#    "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
#    LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
#    PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
#    HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
#    SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
#    LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
#    DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
#    THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
#    (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
#    OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
###############################################################################
"""
Functions for visualizing results of quantum dynamics simulations,
visualizations of quantum states and processes.
"""
import warnings
import numpy as np
from numpy import pi, array, sin, cos, angle
from operator import mul

import qutip.settings
if qutip.settings.qutip_graphics == 'YES':
    import matplotlib.pyplot as plt
    import matplotlib as mpl
    from matplotlib import cm
    from mpl_toolkits.mplot3d import Axes3D

from qutip.qobj import Qobj, isket, isbra
from qutip.states import ket2dm
from qutip.wigner import wigner
from qutip.tensor import tensor


# Adopted from the SciPy Cookbook.
def _blob(x, y, w, w_max, area):
    """
    Draws a square-shaped blob with the given area (< 1) at
    the given coordinates.
    """
    hs = np.sqrt(area) / 2
    xcorners = array([x - hs, x + hs, x + hs, x - hs])
    ycorners = array([y - hs, y - hs, y + hs, y + hs])

    plt.fill(xcorners, ycorners,
             color=cm.RdBu(int((w + w_max) * 256 / (2 * w_max))))


# Adopted from the SciPy Cookbook.
def hinton(rho, xlabels=None, ylabels=None, title=None, ax=None):
    """Draws a Hinton diagram for visualizing a density matrix.

    Parameters
    ----------
    rho : qobj
        Input density matrix.

    xlabels : list of strings
        list of x labels

    ylabels : list of strings
        list of y labels

    title : string
        title of the plot (optional)

    ax : a matplotlib axes instance
        The axes context in which the plot will be drawn.

    Returns
    -------
    fig, ax : tuple
        A tuple of the matplotlib figure and axes instances used to produce
        the figure.

    Raises
    ------
    ValueError
        Input argument is not a quantum object.

    """

    if isinstance(rho, Qobj):
        if isket(rho) or isbra(rho):
            raise ValueError("argument must be a quantum operator")

        W = rho.full()
    else:
        W = rho

    if ax is None:
        fig, ax = plt.subplots(1, 1, figsize=(8, 6))
    else:
        fig = None

    if not (xlabels or ylabels):
        ax.axis('off')

    ax.axis('equal')
    ax.set_frame_on(False)

    height, width = W.shape

    w_max = 1.25 * max(abs(np.diag(np.matrix(W))))
    if w_max <= 0.0:
        w_max = 1.0

    # x axis
    ax.xaxis.set_major_locator(plt.IndexLocator(1, 0.5))
    if xlabels:
        ax.set_xticklabels(xlabels)
    ax.tick_params(axis='x', labelsize=14)

    # y axis
    ax.yaxis.set_major_locator(plt.IndexLocator(1, 0.5))
    if ylabels:
        ax.set_yticklabels(list(reversed(ylabels)))
    ax.tick_params(axis='y', labelsize=14)

    ax.fill(array([0, width, width, 0]), array([0, 0, height, height]),
            color=cm.RdBu(128))
    for x in range(width):
        for y in range(height):
            _x = x + 1
            _y = y + 1
            if np.real(W[x, y]) > 0.0:
                _blob(_x - 0.5, height - _y + 0.5, abs(W[x,
                      y]), w_max, min(1, abs(W[x, y]) / w_max))
            else:
                _blob(_x - 0.5, height - _y + 0.5, -abs(W[
                      x, y]), w_max, min(1, abs(W[x, y]) / w_max))

    # color axis
    norm = mpl.colors.Normalize(-abs(W).max(), abs(W).max())
    cax, kw = mpl.colorbar.make_axes(ax, shrink=0.75, pad=.1)
    cb = mpl.colorbar.ColorbarBase(cax, norm=norm, cmap=cm.RdBu)

    return fig, ax


def sphereplot(theta, phi, values, fig=None, ax=None, save=False):
    """Plots a matrix of values on a sphere

    Parameters
    ----------
    theta : float
        Angle with respect to z-axis

    phi : float
        Angle in x-y plane

    values : array
        Data set to be plotted

    fig : a matplotlib Figure instance
        The Figure canvas in which the plot will be drawn.

    ax : a matplotlib axes instance
        The axes context in which the plot will be drawn.

    save : bool {False , True}
        Whether to save the figure or not

    Returns
    -------
    fig, ax : tuple
        A tuple of the matplotlib figure and axes instances used to produce
        the figure.
    """
    if fig is None or ax is None:
        fig = plt.figure()
        ax = Axes3D(fig)

    thetam, phim = np.meshgrid(theta, phi)
    xx = sin(thetam) * cos(phim)
    yy = sin(thetam) * sin(phim)
    zz = cos(thetam)
    r = array(abs(values))
    ph = angle(values)
    # normalize color range based on phase angles in list ph
    nrm = mpl.colors.Normalize(ph.min(), ph.max())

    # plot with facecolors set to cm.jet colormap normalized to nrm
    surf = ax.plot_surface(r * xx, r * yy, r * zz, rstride=1, cstride=1,
                           facecolors=cm.jet(nrm(ph)), linewidth=0)
    # create new axes on plot for colorbar and shrink it a bit.
    # pad shifts location of bar with repsect to the main plot
    cax, kw = mpl.colorbar.make_axes(ax, shrink=.66, pad=.02)

    # create new colorbar in axes cax with cm jet and normalized to nrm like
    # our facecolors
    cb1 = mpl.colorbar.ColorbarBase(cax, cmap=cm.jet, norm=nrm)
    # add our colorbar label
    cb1.set_label('Angle')

    if save:
        plt.savefig("sphereplot.png")

    return fig, ax


def matrix_histogram(M, xlabels=None, ylabels=None, title=None, limits=None,
                     colorbar=True, fig=None, ax=None):
    """
    Draw a histogram for the matrix M, with the given x and y labels and title.

    Parameters
    ----------
    M : Matrix of Qobj
        The matrix to visualize

    xlabels : list of strings
        list of x labels

    ylabels : list of strings
        list of y labels

    title : string
        title of the plot (optional)

    limits : list/array with two float numbers
        The z-axis limits [min, max] (optional)

    ax : a matplotlib axes instance
        The axes context in which the plot will be drawn.

    Returns
    -------
    fig, ax : tuple
        A tuple of the matplotlib figure and axes instances used to produce
        the figure.

    Raises
    ------
    ValueError
        Input argument is not valid.

    """

    if isinstance(M, Qobj):
        # extract matrix data from Qobj
        M = M.full()

    n = np.size(M)
    xpos, ypos = np.meshgrid(range(M.shape[0]), range(M.shape[1]))
    xpos = xpos.T.flatten() - 0.5
    ypos = ypos.T.flatten() - 0.5
    zpos = np.zeros(n)
    dx = dy = 0.8 * np.ones(n)
    dz = np.real(M.flatten())

    if limits and type(limits) is list and len(limits) == 2:
        z_min = limits[0]
        z_max = limits[1]
    else:
        z_min = min(dz)
        z_max = max(dz)
        if z_min == z_max:
            z_min -= 0.1
            z_max += 0.1

    norm = mpl.colors.Normalize(z_min, z_max)
    cmap = cm.get_cmap('jet')  # Spectral
    colors = cmap(norm(dz))

    if ax is None:
        fig = plt.figure()
        ax = Axes3D(fig, azim=-35, elev=35)

    ax.bar3d(xpos, ypos, zpos, dx, dy, dz, color=colors)

    if title and fig:
        ax.set_title(title)

    # x axis
    ax.axes.w_xaxis.set_major_locator(plt.IndexLocator(1, -0.5))
    if xlabels:
        ax.set_xticklabels(xlabels)
    ax.tick_params(axis='x', labelsize=14)

    # y axis
    ax.axes.w_yaxis.set_major_locator(plt.IndexLocator(1, -0.5))
    if ylabels:
        ax.set_yticklabels(ylabels)
    ax.tick_params(axis='y', labelsize=14)

    # z axis
    ax.axes.w_zaxis.set_major_locator(plt.IndexLocator(1, 0.5))
    ax.set_zlim3d([min(z_min, 0), z_max])

    # color axis
    if colorbar:
        cax, kw = mpl.colorbar.make_axes(ax, shrink=.75, pad=.0)
        cb1 = mpl.colorbar.ColorbarBase(cax, cmap=cmap, norm=norm)

    return fig, ax


def complex_phase_cmap():
    """
    Create a cyclic colormap for representing the phase of complex variables

    Returns
    -------
    cmap :
        A matplotlib linear segmented colormap.
    """
    cdict = {'blue': ((0.00, 0.0, 0.0),
                      (0.25, 0.0, 0.0),
                      (0.50, 1.0, 1.0),
                      (0.75, 1.0, 1.0),
                      (1.00, 0.0, 0.0)),
             'green': ((0.00, 0.0, 0.0),
                      (0.25, 1.0, 1.0),
                      (0.50, 0.0, 0.0),
                      (0.75, 1.0, 1.0),
                      (1.00, 0.0, 0.0)),
             'red': ((0.00, 1.0, 1.0),
                     (0.25, 0.5, 0.5),
                     (0.50, 0.0, 0.0),
                     (0.75, 0.0, 0.0),
                     (1.00, 1.0, 1.0))}

    cmap = mpl.colors.LinearSegmentedColormap('phase_colormap', cdict, 256)

    return cmap


def matrix_histogram_complex(M, xlabels=None, ylabels=None,
                             title=None, limits=None, phase_limits=None,
                             colorbar=True, fig=None, ax=None,
                             threshold=None):
    """
    Draw a histogram for the amplitudes of matrix M, using the argument
    of each element for coloring the bars, with the given x and y labels
    and title.

    Parameters
    ----------
    M : Matrix of Qobj
        The matrix to visualize

    xlabels : list of strings
        list of x labels

    ylabels : list of strings
        list of y labels

    title : string
        title of the plot (optional)

    limits : list/array with two float numbers
        The z-axis limits [min, max] (optional)

    phase_limits : list/array with two float numbers
        The phase-axis (colorbar) limits [min, max] (optional)

    ax : a matplotlib axes instance
        The axes context in which the plot will be drawn.

    threshold: float (None)
        Threshold for when bars of smaller height should be transparent. If 
        not set, all bars are colored according to the color map.

    Returns
    -------
    fig, ax : tuple
        A tuple of the matplotlib figure and axes instances used to produce
        the figure.

    Raises
    ------
    ValueError
        Input argument is not valid.

    """

    if isinstance(M, Qobj):
        # extract matrix data from Qobj
        M = M.full()

    n = np.size(M)
    xpos, ypos = np.meshgrid(range(M.shape[0]), range(M.shape[1]))
    xpos = xpos.T.flatten() - 0.5
    ypos = ypos.T.flatten() - 0.5
    zpos = np.zeros(n)
    dx = dy = 0.8 * np.ones(n)
    Mvec = M.flatten()
    dz = abs(Mvec)

    # make small numbers real, to avoid random colors
    idx, = np.where(abs(Mvec) < 0.001)
    Mvec[idx] = abs(Mvec[idx])

    if phase_limits:  # check that limits is a list type
        phase_min = phase_limits[0]
        phase_max = phase_limits[1]
    else:
        phase_min = -pi
        phase_max = pi

    norm = mpl.colors.Normalize(phase_min, phase_max)
    cmap = complex_phase_cmap()

    colors = cmap(norm(angle(Mvec)))
    if not threshold is None:
        colors[:,3] = 1 * (dz > threshold) 

    if ax is None:
        fig = plt.figure()
        ax = Axes3D(fig, azim=-35, elev=35)

    ax.bar3d(xpos, ypos, zpos, dx, dy, dz, color=colors)

    if title and fig:
        ax.set_title(title)

    # x axis
    ax.axes.w_xaxis.set_major_locator(plt.IndexLocator(1, -0.5))
    if xlabels:
        ax.set_xticklabels(xlabels)
    ax.tick_params(axis='x', labelsize=12)

    # y axis
    ax.axes.w_yaxis.set_major_locator(plt.IndexLocator(1, -0.5))
    if ylabels:
        ax.set_yticklabels(ylabels)
    ax.tick_params(axis='y', labelsize=12)

    # z axis
    if limits and isinstance(limits, list):
        ax.set_zlim3d(limits)
    else:
        ax.set_zlim3d([0, 1])  # use min/max
    # ax.set_zlabel('abs')

    # color axis
    if colorbar:
        cax, kw = mpl.colorbar.make_axes(ax, shrink=.75, pad=.0)
        cb = mpl.colorbar.ColorbarBase(cax, cmap=cmap, norm=norm)
        cb.set_ticks([-pi, -pi / 2, 0, pi / 2, pi])
        cb.set_ticklabels(
            (r'$-\pi$', r'$-\pi/2$', r'$0$', r'$\pi/2$', r'$\pi$'))
        cb.set_label('arg')

    return fig, ax


def plot_energy_levels(H_list, N=0, labels=None, show_ylabels=False,
                       figsize=(8, 12), fig=None, ax=None):
    """
    Plot the energy level diagrams for a list of Hamiltonians. Include
    up to N energy levels. For each element in H_list, the energy
    levels diagram for the cummulative Hamiltonian sum(H_list[0:n]) is plotted,
    where n is the index of an element in H_list.

    Parameters
    ----------

        H_list : List of Qobj
            A list of Hamiltonians.

        labels : List of string
            A list of labels for each Hamiltonian

        show_ylabels : Bool (default False)
            Show y labels to the left of energy levels of the initial
            Hamiltonian.

        N : int
            The number of energy levels to plot

        figsize : tuple (int,int)
            The size of the figure (width, height).

        fig : a matplotlib Figure instance
            The Figure canvas in which the plot will be drawn.

        ax : a matplotlib axes instance
            The axes context in which the plot will be drawn.

    Returns
    -------
    fig, ax : tuple
        A tuple of the matplotlib figure and axes instances used to produce
        the figure.

    Raises
    ------

        ValueError
            Input argument is not valid.

    """

    if not isinstance(H_list, list):
        raise ValueError("H_list must be a list of Qobj instances")

    if not fig and not ax:
        fig, ax = plt.subplots(1, 1, figsize=figsize)

    H = H_list[0]
    N = H.shape[0] if N == 0 else min(H.shape[0], N)

    xticks = []
    yticks = []

    x = 0
    evals0 = H.eigenenergies(eigvals=N) / (2 * np.pi)
    for e_idx, e in enumerate(evals0[:N]):
        ax.plot([x, x + 2], np.array([1, 1]) * e, 'b', linewidth=2)
        yticks.append(e)
    xticks.append(x + 1)
    x += 2

    for H1 in H_list[1:]:

        H = H + H1
        evals1 = H.eigenenergies() / (2 * np.pi)

        for e_idx, e in enumerate(evals1[:N]):
            ax.plot([x, x + 1], np.array([evals0[e_idx], e]), 'k:')
        x += 1

        for e_idx, e in enumerate(evals1[:N]):
            ax.plot([x, x + 2], np.array([1, 1]) * e, 'b', linewidth=2)
        xticks.append(x + 1)
        x += 2

        evals0 = evals1

    ax.set_frame_on(False)

    if show_ylabels:
        yticks = np.unique(np.around(yticks, 1))
        ax.set_yticks(yticks)
    else:
        ax.axes.get_yaxis().set_visible(False)

    if labels:
        ax.get_xaxis().tick_bottom()
        ax.set_xticks(xticks)
        ax.set_xticklabels(labels, fontsize=16)
    else:
        ax.axes.get_xaxis().set_visible(False)

    return fig, ax


def energy_level_diagram(H_list, N=0, labels=None, show_ylabels=False,
                         figsize=(8, 12), fig=None, ax=None):
    warnings.warn("Deprecated: Use plot_energy_levels")
    return plot_energy_levels(H_list, N=N, labels=labels,
                              show_ylabels=show_ylabels,
                              figsize=figsize, fig=fig, ax=ax)


def wigner_cmap(W, levels=1024, shift=0, invert=False):
    """A custom colormap that emphasizes negative values by creating a
    nonlinear colormap.

    Parameters
    ----------
    W : array
        Wigner function array, or any array.

    levels : int
        Number of color levels to create.

    shift : float
        Shifts the value at which Wigner elements are emphasized.
        This parameter should typically be negative and small (i.e -5e-3).

    invert : bool
        Invert the color scheme for negative values so that smaller negative
        values have darker color.

    Returns
    -------
    Returns a Matplotlib colormap instance for use in plotting.

    Notes
    -----
    The 'shift' parameter allows you to vary where the colormap begins
    to highlight negative colors. This is beneficial in cases where there
    are small negative Wigner elements due to numerical round-off and/or
    truncation.
    """
    max_color = np.array([0.020, 0.19, 0.38, 1.0])
    mid_color = np.array([1, 1, 1, 1.0])
    if invert:
        min_color = np.array([1, 0.70, 0.87, 1])
        neg_color = np.array([0.4, 0.0, 0.12, 1])
    else:
        min_color = np.array([0.4, 0.0, 0.12, 1])
        neg_color = np.array([1, 0.70, 0.87, 1])
    # get min and max values from Wigner function
    bounds = [W.min(), W.max()]
    # create empty array for RGBA colors
    adjust_RGBA = np.hstack((np.zeros((levels, 3)), np.ones((levels, 1))))
    zero_pos = np.round(levels * np.abs(shift - bounds[0])
                        / (bounds[1] - bounds[0]))
    num_pos = levels - zero_pos
    num_neg = zero_pos - 1
    # set zero values to mid_color
    adjust_RGBA[zero_pos] = mid_color
    # interpolate colors
    for k in range(0, levels):
        if k < zero_pos:
            interp = k / (num_neg + 1.0)
            adjust_RGBA[k][0:3] = (1.0 - interp) * \
                min_color[0:3] + interp * neg_color[0:3]
        elif k > zero_pos:
            interp = (k - zero_pos) / (num_pos + 1.0)
            adjust_RGBA[k][0:3] = (1.0 - interp) * \
                mid_color[0:3] + interp * max_color[0:3]
    # create colormap
    wig_cmap = mpl.colors.LinearSegmentedColormap.from_list('wigner_cmap',
                                                            adjust_RGBA,
                                                            N=levels)
    return wig_cmap


def plot_fock_distribution(rho, offset=0, fig=None, ax=None,
                           figsize=(8, 6), title=None, unit_y_range=True):
    """
    Plot the Fock distribution for a density matrix (or ket) that describes
    an oscillator mode.

    Parameters
    ----------
    rho : :class:`qutip.qobj.Qobj`
        The density matrix (or ket) of the state to visualize.

    fig : a matplotlib Figure instance
        The Figure canvas in which the plot will be drawn.

    ax : a matplotlib axes instance
        The axes context in which the plot will be drawn.

    title : string
        An optional title for the figure.

    figsize : (width, height)
        The size of the matplotlib figure (in inches) if it is to be created
        (that is, if no 'fig' and 'ax' arguments are passed).

    Returns
    -------
    fig, ax : tuple
        A tuple of the matplotlib figure and axes instances used to produce
        the figure.
    """

    if not fig and not ax:
        fig, ax = plt.subplots(1, 1, figsize=figsize)

    if isket(rho):
        rho = ket2dm(rho)

    N = rho.shape[0]

    ax.bar(np.arange(offset, offset + N) - .4, np.real(rho.diag()),
           color="green", alpha=0.6, width=0.8)
    if unit_y_range:
        ax.set_ylim(0, 1)

    ax.set_xlim(-.5 + offset, N + offset)
    ax.set_xlabel('Fock number', fontsize=12)
    ax.set_ylabel('Occupation probability', fontsize=12)

    if title:
        ax.set_title(title)

    return fig, ax


def fock_distribution(rho, offset=0, fig=None, ax=None,
                      figsize=(8, 6), title=None, unit_y_range=True):
    warnings.warn("Deprecated: Use plot_fock_distribution")
    return plot_fock_distribution(rho, offset=offset, fig=fig, ax=ax,
                                  figsize=figsize, title=title,
                                  unit_y_range=unit_y_range)


def plot_wigner(rho, fig=None, ax=None, figsize=(8, 4),
                cmap=None, alpha_max=7.5, colorbar=False,
                method='iterative', projection='2d'):
    """
    Plot the the Wigner function for a density matrix (or ket) that describes
    an oscillator mode.

    Parameters
    ----------
    rho : :class:`qutip.qobj.Qobj`
        The density matrix (or ket) of the state to visualize.

    fig : a matplotlib Figure instance
        The Figure canvas in which the plot will be drawn.

    ax : a matplotlib axes instance
        The axes context in which the plot will be drawn.

    figsize : (width, height)
        The size of the matplotlib figure (in inches) if it is to be created
        (that is, if no 'fig' and 'ax' arguments are passed).

    cmap : a matplotlib cmap instance
        The colormap.

    alpha_max : float
        The span of the x and y coordinates (both [-alpha_max, alpha_max]).

    colorbar : bool
        Whether (True) or not (False) a colorbar should be attached to the
        Wigner function graph.

    method : string {'iterative', 'laguerre', 'fft'}
        The method used for calculating the wigner function. See the
        documentation for qutip.wigner for details.

    projection: string {'2d', '3d'}
        Specify whether the Wigner function is to be plotted as a
        contour graph ('2d') or surface plot ('3d').

    Returns
    -------
    fig, ax : tuple
        A tuple of the matplotlib figure and axes instances used to produce
        the figure.
    """

    if not fig and not ax:
        if projection == '2d':
            fig, ax = plt.subplots(1, 1, figsize=figsize)
        elif projection == '3d':
            fig = plt.figure(figsize=figsize)
            ax = fig.add_subplot(1, 1, 1, projection='3d')
        else:
            raise ValueError('Unexpected value of projection keyword argument')

    if isket(rho):
        rho = ket2dm(rho)

    xvec = np.linspace(-alpha_max, alpha_max, 200)
    W0 = wigner(rho, xvec, xvec, method=method)

    W, yvec = W0 if type(W0) is tuple else (W0, xvec)

    wlim = abs(W).max()

    if cmap is None:
        cmap = cm.get_cmap('RdBu')

    if projection == '2d':
        cf = ax.contourf(xvec, yvec, W, 100,
                         norm=mpl.colors.Normalize(-wlim, wlim), cmap=cmap)
    elif projection == '3d':
        X, Y = np.meshgrid(xvec, xvec)
        cf = ax.plot_surface(X, Y, W0, rstride=5, cstride=5, linewidth=0.5,
                             norm=mpl.colors.Normalize(-wlim, wlim), cmap=cmap)
    else:
        raise ValueError('Unexpected value of projection keyword argument.')

    if xvec is not yvec:
        ax.set_ylim(xvec.min(), xvec.max())

    ax.set_xlabel(r'$\rm{Re}(\alpha)$', fontsize=12)
    ax.set_ylabel(r'$\rm{Im}(\alpha)$', fontsize=12)

    if colorbar:
        cb = fig.colorbar(cf, ax=ax)

    ax.set_title("Wigner function", fontsize=12)

    return fig, ax


def plot_wigner_fock_distribution(rho, fig=None, axes=None, figsize=(8, 4),
                                  cmap=None, alpha_max=7.5, colorbar=False,
                                  method='iterative', projection='2d'):
    """
    Plot the Fock distribution and the Wigner function for a density matrix
    (or ket) that describes an oscillator mode.

    Parameters
    ----------
    rho : :class:`qutip.qobj.Qobj`
        The density matrix (or ket) of the state to visualize.

    fig : a matplotlib Figure instance
        The Figure canvas in which the plot will be drawn.

    axes : a list of two matplotlib axes instances
        The axes context in which the plot will be drawn.

    figsize : (width, height)
        The size of the matplotlib figure (in inches) if it is to be created
        (that is, if no 'fig' and 'ax' arguments are passed).

    cmap : a matplotlib cmap instance
        The colormap.

    alpha_max : float
        The span of the x and y coordinates (both [-alpha_max, alpha_max]).

    colorbar : bool
        Whether (True) or not (False) a colorbar should be attached to the
        Wigner function graph.

    method : string {'iterative', 'laguerre', 'fft'}
        The method used for calculating the wigner function. See the
        documentation for qutip.wigner for details.

    projection: string {'2d', '3d'}
        Specify whether the Wigner function is to be plotted as a
        contour graph ('2d') or surface plot ('3d').

    Returns
    -------
    fig, ax : tuple
        A tuple of the matplotlib figure and axes instances used to produce
        the figure.
    """

    if not fig and not axes:
        if projection == '2d':
            fig, axes = plt.subplots(1, 2, figsize=figsize)
        elif projection == '3d':
            fig = plt.figure(figsize=figsize)
            axes = [fig.add_subplot(1, 2, 1),
                    fig.add_subplot(1, 2, 2, projection='3d')]
        else:
            raise ValueError('Unexpected value of projection keyword argument')

    if isket(rho):
        rho = ket2dm(rho)

    plot_fock_distribution(rho, fig=fig, ax=axes[0])
    plot_wigner(rho, fig=fig, ax=axes[1], figsize=figsize, cmap=cmap,
                alpha_max=alpha_max, colorbar=colorbar, method=method,
                projection=projection)

    return fig, axes


def wigner_fock_distribution(rho, fig=None, axes=None, figsize=(8, 4),
                             cmap=None, alpha_max=7.5, colorbar=False,
                             method='iterative'):
    warnings.warn("Deprecated: Use plot_wigner_fock_distribution")
    return plot_wigner_fock_distribution(rho, fig=fig, axes=axes,
                                         figsize=figsize, cmap=cmap,
                                         alpha_max=alpha_max,
                                         colorbar=colorbar,
                                         method=method)


def plot_expectation_values(results, ylabels=[], title=None, show_legend=False,
                            fig=None, axes=None, figsize=(8, 4)):
    """
    Visualize the results (expectation values) for an evolution solver.
    `results` is assumed to be an instance of Odedata, or a list of Odedata
    instances.

    Parameters
    ----------
    results : (list of) :class:`qutip.Odedata`
        List of results objects returned by any of the QuTiP evolution solvers.

    ylabels : list of strings
        The y-axis labels. List should be of the same length as `results`.

    title : string
        The title of the figure.

    show_legend : bool
        Whether or not to show the legend.

    fig : a matplotlib Figure instance
        The Figure canvas in which the plot will be drawn.

    axes : a matplotlib axes instance
        The axes context in which the plot will be drawn.

    figsize : (width, height)
        The size of the matplotlib figure (in inches) if it is to be created
        (that is, if no 'fig' and 'ax' arguments are passed).

    Returns
    -------
    fig, ax : tuple
        A tuple of the matplotlib figure and axes instances used to produce
        the figure.
    """
    if not isinstance(results, list):
        results = [results]

    n_e_ops = max([len(result.expect) for result in results])

    if not fig or not axes:
        if not figsize:
            figsize = (12, 3 * n_e_ops)
        fig, axes = plt.subplots(n_e_ops, 1, sharex=True,
                                 figsize=figsize, squeeze=False)

    for r_idx, result in enumerate(results):
        for e_idx, e in enumerate(result.expect):
            axes[e_idx, 0].plot(result.times, e,
                                label="%s [%d]" % (result.solver, e_idx))

    if title:
        axes[0, 0].set_title(title)

    axes[n_e_ops - 1, 0].set_xlabel("time", fontsize=12)
    for n in range(n_e_ops):
        if show_legend:
            axes[n, 0].legend()
        if ylabels:
            axes[n, 0].set_ylabel(ylabels[n], fontsize=12)

    return fig, axes


def plot_spin_distribution_2d(P, THETA, PHI,
                              fig=None, ax=None, figsize=(8, 8)):
    """
    Plot a spin distribution function (given as meshgrid data) with a 2D
    projection where the surface of the unit sphere is mapped on the unit disk.

    Parameters
    ----------
    P : matrix
        Distribution values as a meshgrid matrix.

    THETA : matrix
        Meshgrid matrix for the theta coordinate.

    PHI : matrix
        Meshgrid matrix for the phi coordinate.

    fig : a matplotlib figure instance
        The figure canvas on which the plot will be drawn.

    ax : a matplotlib axis instance
        The axis context in which the plot will be drawn.

    figsize : (width, height)
        The size of the matplotlib figure (in inches) if it is to be created
        (that is, if no 'fig' and 'ax' arguments are passed).

    Returns
    -------
    fig, ax : tuple
        A tuple of the matplotlib figure and axes instances used to produce
        the figure.
    """

    if not fig or not ax:
        if not figsize:
            figsize = (8, 8)
        fig, ax = plt.subplots(1, 1, figsize=figsize)

    Y = (THETA - pi / 2) / (pi / 2)
    X = (pi - PHI) / pi * np.sqrt(cos(THETA - pi / 2))

    if P.min() < -1e12:
        cmap = cm.RdBu
    else:
        cmap = cm.RdYlBu

    ax.pcolor(X, Y, P.real, cmap=cmap)
    ax.set_xlabel(r'$\varphi$', fontsize=18)
    ax.set_ylabel(r'$\theta$', fontsize=18)

    ax.set_xticks([-1, 0, 1])
    ax.set_xticklabels([r'$0$', r'$\pi$', r'$2\pi$'], fontsize=18)
    ax.set_yticks([-1, 0, 1])
    ax.set_yticklabels([r'$\pi$', r'$\pi/2$', r'$0$'], fontsize=18)

    return fig, ax


def plot_spin_distribution_3d(P, THETA, PHI,
                              fig=None, ax=None, figsize=(8, 6)):
    """Plots a matrix of values on a sphere

    Parameters
    ----------
    P : matrix
        Distribution values as a meshgrid matrix.

    THETA : matrix
        Meshgrid matrix for the theta coordinate.

    PHI : matrix
        Meshgrid matrix for the phi coordinate.

    fig : a matplotlib figure instance
        The figure canvas on which the plot will be drawn.

    ax : a matplotlib axis instance
        The axis context in which the plot will be drawn.

    figsize : (width, height)
        The size of the matplotlib figure (in inches) if it is to be created
        (that is, if no 'fig' and 'ax' arguments are passed).

    Returns
    -------
    fig, ax : tuple
        A tuple of the matplotlib figure and axes instances used to produce
        the figure.

    """

    if fig is None or ax is None:
        fig = plt.figure(figsize=figsize)
        ax = Axes3D(fig, azim=-35, elev=35)

    xx = sin(THETA) * cos(PHI)
    yy = sin(THETA) * sin(PHI)
    zz = cos(THETA)

    if P.min() < -1e12:
        cmap = cm.RdBu
        norm = mpl.colors.Normalize(-P.max(), P.max())
    else:
        cmap = cm.RdYlBu
        norm = mpl.colors.Normalize(P.min(), P.max())

    surf = ax.plot_surface(xx, yy, zz, rstride=1, cstride=1,
                           facecolors=cmap(norm(P)), linewidth=0)

    cax, kw = mpl.colorbar.make_axes(ax, shrink=.66, pad=.02)
    cb1 = mpl.colorbar.ColorbarBase(cax, cmap=cmap, norm=norm)
    cb1.set_label('magnitude')

    return fig, ax


#
# Qubism and other qubistic visualizations
#

def complex_array_to_rgb(X, theme='light', rmax=None):
    """Makes an array of complex number and converts it to an array of [r, g, b],
    where phase gives hue and saturation/value are given by the absolute value.
    Especially for use with imshow for complex plots.

    For more info on coloring, see:
        Emilia Petrisor,
        Visualizing complex-valued functions with Matplotlib and Mayavi
        http://nbviewer.ipython.org/github/empet/Math/blob/master/DomainColoring.ipynb

    Parameters
    ----------
    X : array
        Array (of any dimension) of complex numbers. 

    theme : 'light' (default) or 'dark'
        Set coloring theme for mapping complex values into colors.

    rmax : float
        Maximal abs value for color normalization.
        If None (default), uses np.abs(X).max().

    Returns
    -------
    Y : array
        Array of colors (of shape X.shape + (3,)).

    """

    absmax = rmax or np.abs(X).max()
    Y = np.zeros(X.shape + (3,), dtype='float')
    Y[..., 0] = np.angle(X) / (2 * pi) % 1
    if theme == 'light':
        Y[..., 1] = np.clip(np.abs(X) / absmax, 0, 1)
        Y[..., 2] = 1
    elif theme == 'dark':
        Y[..., 1] = 1
        Y[..., 2] = np.clip(np.abs(X) / absmax, 0, 1)
    Y = mpl.colors.hsv_to_rgb(Y)
    return Y


def _index_to_sequence(i, dim_list):
    """
    For a matrix entry with index i it returns state it corresponds to.
    In particular, for dim_list=[2]*n it returns i written as a binary number.

    Parameters
    ----------
    i : int
        Index in a matrix.

    dim_list : list of int
        List of dimensions of consecutive particles.

    Returns
    -------
    seq : list
        List of coordinates for each particle.

    """
    res = []
    j = i
    for d in reversed(dim_list):
        j, s = divmod(j, d)
        res.append(s)
    return list(reversed(res))


def _sequence_to_index(seq, dim_list):
    """
    Inverse of _index_to_sequence.

    Parameters
    ----------
    seq : list of ints
        List of coordinates for each particle.

    dim_list : list of int
        List of dimensions of consecutive particles.

    Returns
    -------
    i : list
        Index in a matrix.

    """
    i = 0
    for s, d in zip(seq, dim_list):
        i *= d
        i += s

    return i


def _to_qubism_index_pair(i, dim_list, how='pairs'):
    """
    For a matrix entry with index i it returns x, y coordinates in qubism mapping.

    Parameters
    ----------
    i : int
        Index in a matrix.

    dim_list : list of int
        List of dimensions of consecutive particles.

    how : 'pairs' ('default'), 'pairs_skewed' or 'before_after'
        Type of qubistic plot.

    Returns
    -------
    x, y : tuple of ints
        List of coordinates for each particle.

    """
    seq = _index_to_sequence(i, dim_list)

    if how == 'pairs':
        y = _sequence_to_index(seq[::2], dim_list[::2])
        x = _sequence_to_index(seq[1::2], dim_list[1::2])
    elif how == 'pairs_skewed':
        dim_list2 = dim_list[::2]
        y = _sequence_to_index(seq[::2], dim_list2)
        seq2 = [(b - a) % d for a, b, d in zip(seq[::2], seq[1::2], dim_list2)]
        x = _sequence_to_index(seq2, dim_list2)
    elif how == 'before_after':
        # https://en.wikipedia.org/wiki/File:Ising-tartan.png
        n = len(dim_list)
        y = _sequence_to_index(reversed(seq[:n/2]), reversed(dim_list[:n/2]))
        x = _sequence_to_index(seq[n/2:], dim_list[n/2:])
    else:
        raise Exception("Not such 'how'.")
    return x, y


def _product(li):
    return reduce(mul, li)


def plot_qubism(ket, theme='light', how='pairs',
                grid_iteration=1, legend_iteration=0,
                fig=None, ax=None, figsize=(6, 6)):
    """
    Qubism plot for pure states of many qudits.
    Works best for spin chains, especially with even number of particles
    of the same dimension.
    Allows to see entanglement between first 2*k particles and the rest.

    More information:
        J. Rodriguez-Laguna, P. Migdal, M. Ibanez Berganza, M. Lewenstein, G. Sierra,
        "Qubism: self-similar visualization of many-body wavefunctions",
        New J. Phys. 14 053028 (2012), arXiv:1112.3560, 
        http://dx.doi.org/10.1088/1367-2630/14/5/053028 (open access)

    Parameters
    ----------
    ket : Qobj
        Pure state for plotting.

    theme : 'light' (default) or 'dark'
        Set coloring theme for mapping complex values into colors.
        See: complex_array_to_rgb.

    how : 'pairs' (default), 'pairs_skewed' or 'before_after'
        Type of Qubism plotting.

    grid_iteration : int (default 1)
        Helper lines to be drawn on plot.
        Show tiles for 2*grid_iteration particles vs all others.

    legend_iteration : int (default 0) or 'grid_iteration' or 'all'
        Show labels for first 2*legend_iteration particles.
        Option 'grid_iteration' sets the same number of particles as for grid_iteration.
        Option 'all' makes label for all particles.
        Typically it should be 0, 1, 2 or perhaps 3. 

    fig : a matplotlib figure instance
        The figure canvas on which the plot will be drawn.

    ax : a matplotlib axis instance
        The axis context in which the plot will be drawn.

    figsize : (width, height)
        The size of the matplotlib figure (in inches) if it is to be created
        (that is, if no 'fig' and 'ax' arguments are passed).

    Returns
    -------
    fig, ax : tuple
        A tuple of the matplotlib figure and axes instances used to produce
        the figure.

    """

    if not isket(ket):
        raise Exception("Qubism works only for pure states, i.e. kets.")
        # add for bra?
        # add for dm? (perhaps a separate function, plot_qubism_dm)

    if not fig and not ax:
        fig, ax = plt.subplots(1, 1, figsize=figsize)
 
    dim_list = ket.dims[0]
    n = len(dim_list)

    # for odd number of particles - pixels are rectangular
    if n % 2 == 1:
        ket = tensor(ket, Qobj([1]*dim_list[-1]))
        dim_list = ket.dims[0]
        n += 1

    ketdata = ket.full()

    if how == 'pairs':
        dim_list_y = dim_list[::2]
        dim_list_x = dim_list[1::2]
    elif how == 'pairs_skewed':
        dim_list_y = dim_list[::2]
        dim_list_x = dim_list[1::2]
        if dim_list_x != dim_list_y:
            raise Exception("For 'pairs_skewed' pairs of dimensions need to be the same.")
    elif how == 'before_after':
        dim_list_y = list(reversed(dim_list[:n/2]))
        dim_list_x = dim_list[n/2:]
    else:
        raise Exception("Not such 'how'.")

    size_x = _product(dim_list_x)
    size_y = _product(dim_list_y)

    qub = np.zeros([size_x, size_y], dtype=complex)
    for i in range(ketdata.size):
        qub[_to_qubism_index_pair(i, dim_list, how=how)] = ketdata[i,0]
    qub = qub.transpose()
    
    quadrants_x = _product(dim_list_x[:grid_iteration])
    quadrants_y = _product(dim_list_y[:grid_iteration])

    ticks_x = [size_x/(float(quadrants_x)) * i for i in range(1, quadrants_x)]
    ticks_y = [size_y/(float(quadrants_y)) * i for i in range(1, quadrants_y)]

    ax.set_xticks(ticks_x)
    ax.set_xticklabels([""]*(quadrants_x - 1))
    ax.set_yticks(ticks_y)
    ax.set_yticklabels([""]*(quadrants_y - 1))
    theme2color_of_lines = {'light': '#000000',
                            'dark': '#FFFFFF'}
    ax.grid(True, color=theme2color_of_lines[theme])
    ax.imshow(complex_array_to_rgb(qub, theme=theme),
               interpolation="none",
               extent=(0, size_x, 0, size_y))

    if legend_iteration == 'all':
        label_n = n/2
    elif legend_iteration == 'grid_iteration':
        label_n = grid_iteration
    else:
        label_n = legend_iteration

    if label_n:

        if how == 'before_after':
            dim_list_small = list(reversed(dim_list_y[-label_n:])) + dim_list_x[:label_n]
        else:
            dim_list_small = []
            for j in range(label_n):
                dim_list_small.append(dim_list_y[j])
                dim_list_small.append(dim_list_x[j])

        scale_x = float(size_x) / _product(dim_list_x[:label_n])
        shift_x = 0.5 * scale_x
        scale_y = float(size_y) / _product(dim_list_y[:label_n])
        shift_y = 0.5 * scale_y

        opts = {'fontsize': int((30 * figsize[0]) / _product(dim_list_x[:label_n]) / label_n), 
                'color': theme2color_of_lines[theme],
                'horizontalalignment': 'center',
                'verticalalignment': 'center'}
        for i in range(_product(dim_list_small)):
            x, y = _to_qubism_index_pair(i, dim_list_small, how=how)
            label = "".join(map(str, _index_to_sequence(i, dim_list=dim_list_small)))
            ax.text(scale_x * x + shift_x,
                    size_y - (scale_y * y + shift_y),
                    "$\\left|{0}\\right\\rangle$".format(label),
                    **opts)
    return fig, ax


def plot_schmidt(ket, splitting=None,
                grid_iterationation=(1,1), legend_iteration=0,
                theme='light',
                fig=None, ax=None, figsize=(6, 6)):
    """
    Plotting scheme related to Schmidt decomposition.
    (Under development.)


    Parameters
    ----------
    ket : Qobj
        Pure state for plotting.

    splitting : int
        Plot for a number of first particles versus the rest.
        If not given, it is floor(number of particles / 2).

    theme : 'light' (default) or 'dark'
        Set coloring theme for mapping complex values into colors.
        See: complex_array_to_rgb.

    grid_iteration : pair of ints (default (1,1))
        Helper lines to be drawn on plot.
        Show tiles for 2*grid_iteration particles vs all others.

    legend_iteration : int (default 0) or 'grid_iteration' or 'all'
        Show labels for first 2*legend_iteration particles.
        Option 'grid_iteration' sets the same number of particles as for grid_iteration.
        Option 'all' makes label for all particles.
        Typically it should be 0, 1, 2 or perhaps 3. 

    fig : a matplotlib figure instance
        The figure canvas on which the plot will be drawn.

    ax : a matplotlib axis instance
        The axis context in which the plot will be drawn.

    figsize : (width, height)
        The size of the matplotlib figure (in inches) if it is to be created
        (that is, if no 'fig' and 'ax' arguments are passed).

    Returns
    -------
    fig, ax : tuple
        A tuple of the matplotlib figure and axes instances used to produce
        the figure.

    """

    raise Exception("Not yet implemented.")

