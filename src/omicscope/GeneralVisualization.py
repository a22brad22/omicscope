""" Module for Single Omics Experiment Visualization
This module allows the user to extract information from Omics data using visualization tools.
Here, it is possible to evaluate data normalization (MA-Plot, Volcano Plot, Dynamic range plot,),
individual protein abundance (barplot, boxplots), and perform Principal Component Analysis (PCA) and
Hierarchical clustering analysis (heatmap, pearson correlation plot)

@author: Reis-de-Oliveira G <guioliveirareis@gmail.com>
"""

import copy
import itertools
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn import preprocessing
from sklearn.decomposition import PCA


def bar_ident(OmicScope, logscale=True, col='darkcyan', save='', dpi=300,
             vector=True):
    """Show the amount of entities identified and differentially regulated
    in the study.

    Args:
        OmicScope (OmicScope): OmicScope Experiment
        logscale (bool, optional): Y-axis log-scaled. Defaults to True.
        col (str, optional): Color. Defaults to 'darkcyan'.
        save (str, optional): Path to save figure. Defaults to ''.
        dpi (int, optional): Resolution to save figure. Defaults to 300.
        vector (bool, optional): Save figure in as vector (.svg). Defaults to
        True.

    Returns:
        ax [matplotlib object]: Barplot
    """
    # Define plt parameters
    plt.style.use('default')
    sns.set(rc={'figure.figsize': (11.7, 8.27)})
    sns.set_style("ticks")
    plt.rcParams["figure.dpi"] = dpi
    OmicScope = copy.copy(OmicScope)
    df = OmicScope.quant_data
    # Get number of identified proteins
    identified = df.Accession.count()
    # Get number of quantified proteins
    quantified = df.dropna(axis=0, subset=['pvalue']).Accession.count()
    # Get number of differentially regulated proteins
    deps = OmicScope.deps['Accession'].count()
    if identified != quantified:
        df = ['Identified', 'Quantified', 'Differentially\nregulated']
        protein_number = [identified, quantified, deps]
    else:
        df = ['Quantified', 'Differentially\nregulated']
        protein_number = [quantified, deps]
    df = pd.DataFrame(protein_number, df)
    # Log scaling y-axis
    if logscale is True:
        ax = df.plot(kind='bar', color=col, rot=0, edgecolor="black", log=True,
                      figsize=(2.4, 3.5))
    else:
        ax = df.plot(kind='bar', color=col, rot=0, edgecolor="black",
                     figsize=(2.4, 3.5))
    # Add label upside bar

    def autolabel(rects, ax):
        for rect in rects:
            x = rect.get_x() + rect.get_width() / 2.
            y = rect.get_height()
            ax.annotate("{}".format(y), (x, y), xytext=(0, 5), textcoords="offset points",
                        ha='center', va='bottom')
    autolabel(ax.patches, ax)
    ax.margins(y=0.1)
    ax.legend().remove()
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)
    plt.ylabel('#Proteins')
    plt.title(label=OmicScope.ctrl + ' vs ' + '-'.join(OmicScope.experimental), loc='left')
    plt.grid(b=False)
    if save != '':
        if vector == True:
            plt.savefig(save + 'barplot.svg')
        else:
            plt.savefig(save + 'barplot.png', dpi=dpi)
    plt.show()
    return ax


def volcano_Multicond(OmicScope, *Proteins, pvalue=0.05, palette='viridis',
                      bcol='#962558', non_regulated='#606060',
                      save='', dpi=300, vector=True):
    """Creates a volcano plot for multiple conditions .
    In general, volcano plots are designed to plot 2 conditions.
    Here, we aim to see the distribution of quantified proteins' p-value and
    fold changes among multiple conditions.
    Args:
        OmicScope (OmicScope object): OmicScope Experiment
        pvalue (float, optional): p-value threshold. Defaults to 0.05.
        palette (str, optional): Color palette to differentiate dots.
        Defaults to 'viridis'.
        bcol (str, optional): color for density plot. Defaults to '#962558'.
        non_regulated (str, optional): Proteins not differentially regulated.
         Defaults to '#606060'.
        save (str, optional): Path to save figure. Defaults to ''.
        dpi (int, optional): figure resolution. Defaults to 300.
        vector (bool, optional): Save figure in as vector (.svg). Defaults to
        True.
    """
    plt.style.use('default')
    plt.rcParams["figure.dpi"] = dpi
    OmicScope = copy.copy(OmicScope)
    FoldChange_cutoff = OmicScope.FoldChange_cutoff
    # Definitions for the axes
    df_initial = OmicScope.quant_data
    fc = df_initial['log2(fc)']
    max_fc = max([x for x in fc if x < max(fc)])
    min_fc = min([x for x in fc if x > min(fc)])
    fc = fc.replace([np.inf], max_fc + 1)
    fc = fc.replace([-np.inf], min_fc - 1)
    pval = df_initial['-log10(p)']
    max_pval = max([x for x in pval if x < max(pval)])
    pval = pval.replace([np.inf], max_pval + 1)
    df_initial['-log10(p)'] = pval
    df_initial['log2(fc)'] = fc

    # colors per condition
    comparisons = df_initial.Comparison
    comparisons = comparisons.str[-1] + '-' + comparisons.str[0]
    number_of_comparison = len(comparisons.drop_duplicates())
    color_per_comparison = sns.color_palette(palette=palette,
                                            n_colors=number_of_comparison).as_hex()
    color_comp_dict = dict(zip(comparisons, color_per_comparison))
    col = []
    comparison = []
    for pv, comp in zip(pval, comparisons):
        if pv > -np.log10(pvalue):
            comparison.append(comp)
            col.append(comp)
        else:
            col.append(non_regulated)
            comparison.append('Non-regulated')

    col = pd.Series(col)
    comparison = pd.Series(comparison)
    df = pd.DataFrame(data=zip(pval, fc, col, comparison))
    df.columns = ['pvalue', 'fc', 'col', 'comparison']
    df['pvalue'] = df['pvalue'].astype(float)
    df['fc'] = df['fc'].astype(float)
    df['col'] = df.col.replace(color_comp_dict)

    # annotation if it is on args

    if len(Proteins) > 0:
        ls = pd.DataFrame(Proteins)
        ls.columns = ['gene_name']
        ls_final = ls.merge(df_initial)
        ls_final = ls_final[['gene_name', '-log10(p)', 'log2(fc)']]
        ls_final = ls_final.sort_values('log2(fc)', ascending=False)

    # dimensions
    left, width = 0.1, 0.65
    bottom, height = 0.1, 0.65
    spacing = 0.02
    rect_scatter = [left, bottom, width, height]
    rect_histx = [left, bottom + height + spacing, width, 0.2]
    rect_histy = [left + width + spacing, bottom, 0.2, height]
    # plot
    plt.style.use('bmh')
    plt.figure(figsize=(8, 8))
    # Scatter plot
    ax_scatter = plt.axes(rect_scatter)
    sns.scatterplot(df.fc, df.pvalue, alpha=0.7,
                     hue=df.comparison,
                     palette=list(df.col.drop_duplicates()))
    sns.despine(left=False)
    plt.xlabel("log2( FC)")
    plt.ylabel("-log10(p)")
    ax_scatter.tick_params(direction='in', top=True, right=True)
    plt.grid(b=None)
    ax_scatter.plot(alpha=0.5)
    # Density plot on x-axis (upper)
    ax_histx = plt.axes(rect_histx)
    plt.ylabel("Density")
    plt.title(label=OmicScope.ctrl + ' vs ' + '-'.join(OmicScope.experimental), loc='left')
    ax_histx.tick_params(direction='in', labelbottom=False)
    ax_histx.set_facecolor('white')
    ax_histx.grid(b=None)
    sns.kdeplot(fc, shade=True, color=bcol, edgecolor='black')
    sns.despine(bottom=True, top=True)
    # Density plot on y-axis (right)
    ax_histy = plt.axes(rect_histy)
    ax_histy.tick_params(direction='in', labelleft=False)
    ax_histy.set_facecolor('white')
    ax_histy.grid(b=None)
    sns.kdeplot(pval, shade=True, color=bcol, vertical=True, edgecolor='black')
    sns.despine(top=True, left=True)
    plt.xlabel("Density")
    ax_scatter.set_facecolor('white')
    # Annotation positions
    if len(Proteins) > 0:
        from adjustText import adjust_text
        texts = []
        for a, b, c in zip(ls_final['log2(fc)'], ls_final['-log10(p)'],
                            ls_final['gene_name']):
            texts.append(ax_scatter.text(a, b, c, size=8))
            adjust_text(texts, ax=ax_scatter, force_points=0.25, force_text=0.25,
                        expand_points=(1.5, 1.5), expand_text=(1.5, 1.5),
                        arrowprops=dict(arrowstyle="-", color='black', lw=0.5))
    ax_scatter.axhline(y=-np.log10(0.05), color='gray', linestyle=':')
    ax_scatter.legend()
    if FoldChange_cutoff == 0:
        ax_scatter.axvline(x=0, color='gray', linestyle=':')
    else:
        ax_scatter.axvline(x=FoldChange_cutoff, color='gray', linestyle=':')
    limh = round(fc.max(), 2)
    liml = round(fc.min(), 2)
    limp = round(pval.max() + 0.5, 0)
    ax_scatter.set_xlim((liml - (limh - liml) * 0.10, limh + ((limh - liml) * 0.10)))
    ax_scatter.set_ylim((0, limp + limp * .1))
    ax_histx.set_xlim(ax_scatter.get_xlim())
    ax_histy.set_ylim(ax_scatter.get_ylim())
    if save != '':
        if vector is True:
            plt.savefig(save + 'volcano.svg')
        else:
            plt.savefig(save + 'volcano.png', dpi=dpi)
    plt.show()
    plt.show(block=True)


def volcano_2cond(OmicScope, *Proteins, pvalue=0.05, bcol='darkcyan',
            non_regulated='#606060', up_regulated='#E4001B', down_regulated='#6194BC',
            save='', dpi=300, vector=True):
    """Creates a volcano plot for two conditions .

    Args:
        OmicScope (OmicScope object): OmicScope experiment
        pvalue (float, optional): p-value threshold. Defaults to 0.05.
        bcol (str, optional): color for density plot. Defaults to 'darkcyan'.
        non_regulated (str, optional): Proteins not differentially regulated.
         Defaults to '#606060'.
        up_regulated (str, optional): Proteins up-regulated in relation
        to Control group. Defaults to '#E4001B'.
        down_regulated (str, optional): Proteins down-regulated in relation
        to Control group. Defaults to '#6194BC'.
        save (str, optional): Path to save figure. Defaults to ''.
        dpi (int, optional): figure resolution. Defaults to 300.
        vector (bool, optional): Save figure in as vector (.svg). Defaults to
        True.
    """
    plt.style.use('default')
    plt.rcParams["figure.dpi"] = dpi
    OmicScope = copy.copy(OmicScope)
    FoldChange_cutoff = OmicScope.FoldChange_cutoff
    # Definitions for the axes
    df_initial = OmicScope.quant_data
    fc = df_initial['log2(fc)']
    max_fc = max([x for x in fc if x < max(fc)])
    min_fc = min([x for x in fc if x > min(fc)])
    fc = fc.replace([np.inf], max_fc + 1)
    fc = fc.replace([-np.inf], min_fc - 1)
    pval = df_initial['-log10(p)']
    max_pval = max([x for x in pval if x < max(pval)])
    pval = pval.replace([np.inf], max_pval + 1)
    df_initial['-log10(p)'] = pval
    df_initial['log2(fc)'] = fc
    # Defining colors for dots
    col = []
    comparison = []
    for i, j in zip(fc, pval):
        if j < -np.log10(pvalue):
            col.append(non_regulated)
            comparison.append('non-regulated')
        else:
            if i > FoldChange_cutoff:
                col.append(up_regulated)
                comparison.append('up-regulated')
            elif i < -FoldChange_cutoff:
                col.append(down_regulated)
                comparison.append('down-regulated')
            else:
                col.append(non_regulated)
                comparison.append('non-regulated')
    col, comparison = pd.Series(col), pd.Series(comparison)
    df = pd.DataFrame(zip(pval, fc, col, comparison))
    df.columns = ['pval', 'fc', 'col', 'Regulation']
    # annotation
    if len(Proteins) > 0:
        ls = pd.DataFrame(Proteins)
        ls.columns = ['gene_name']
        ls_final = ls.merge(df_initial)
        ls_final = ls_final[['gene_name', '-log10(p)', 'log2(fc)']]
        ls_final = ls_final.sort_values('log2(fc)', ascending=False)
    # plot dimensions
    left, width = 0.1, 0.65
    bottom, height = 0.1, 0.65
    spacing = 0.02
    rect_scatter = [left, bottom, width, height]
    rect_histx = [left, bottom + height + spacing, width, 0.2]
    rect_histy = [left + width + spacing, bottom, 0.2, height]
    # Plot
    plt.style.use('bmh')
    plt.figure(figsize=(8, 8))
    ax_scatter = plt.axes(rect_scatter)
    # Scatter plot
    sns.scatterplot(df.fc, df.pval, alpha=0.5, linewidth=0.5,
                    hue=df.Regulation,
                    palette=list(df.col.drop_duplicates().dropna()))
    plt.xlabel("log2( FC)")
    plt.ylabel("-log10(p)")
    ax_scatter.tick_params(direction='in', top=True, right=True)
    plt.grid(b=None)
    ax_scatter.plot(alpha=0.5)
    # Density Plot in x-axis (upper)
    ax_histx = plt.axes(rect_histx)
    plt.ylabel("Density")
    plt.title(label=OmicScope.experimental[0] + ' - ' + OmicScope.ctrl, loc='left')
    ax_histx.tick_params(direction='in', labelbottom=False)
    ax_histx.set_facecolor('white')
    ax_histx.grid(b=None)
    sns.kdeplot(fc, shade=True, color=bcol, alpha=0.8, edgecolor='black')
    sns.despine(bottom=True, top=True)
    # Density plot in y axis (right)
    ax_histy = plt.axes(rect_histy)
    ax_histy.tick_params(direction='in', labelleft=False)
    ax_histy.set_facecolor('white')
    ax_histy.grid(b=None)
    sns.kdeplot(pval, shade=True, color=bcol, vertical=True, alpha=0.8, edgecolor='black')
    sns.despine(top=True, left=True)
    plt.xlabel("Density")
    ax_scatter.set_facecolor('white')
    # Annotation positions
    if len(Proteins) > 0:
        from adjustText import adjust_text
        texts = []
        for a, b, c in zip(ls_final['log2(fc)'], ls_final['-log10(p)'],
                           ls_final['gene_name']):
            texts.append(ax_scatter.text(a, b, c, size=8))
            adjust_text(texts, ax=ax_scatter, force_points=0.25, force_text=0.25,
                        expand_points=(1.5, 1.5), expand_text=(1.5, 1.5),
                        arrowprops=dict(arrowstyle="-", color='black', lw=0.5))
    ax_scatter.axhline(y=-np.log10(0.05), color='gray', linestyle=':')

    # Fold change cutoff
    if FoldChange_cutoff != 0:
        ax_scatter.axvline(x=-FoldChange_cutoff,
                           color='gray', linestyle=':')
        ax_scatter.axvline(x=FoldChange_cutoff,
                           color='gray', linestyle=':')
    else:
        ax_scatter.axvline(x=FoldChange_cutoff,
                           color='gray', linestyle=':')
    # Figure limits
    limh = round(fc.max(), 2)
    liml = round(fc.min(), 2)
    limp = round(pval.max() + 0.5, 0)
    ax_scatter.set_xlim((liml - ((limh - liml) * 0.10),
                         limh + ((limh - liml) * 0.10)))
    ax_scatter.set_ylim((0, limp))
    ax_histx.set_xlim(ax_scatter.get_xlim())
    ax_histy.set_ylim(ax_scatter.get_ylim())
    # save figure and how to save
    if save != '':
        if vector == True:
            plt.savefig(save + 'volcano.svg')
        else:
            plt.savefig(save + 'volcano.png', dpi=dpi)
    plt.show()
    plt.show(block=True)


def volcano(OmicScope, *Proteins,
            pvalue=0.05, bcol='#962558', palette='viridis',
                        non_regulated='#606060', up_regulated='#E4001B', down_regulated='#6194BC',
                        save='', dpi=300, vector=True):
    """Creates volcano plot.

    Args:
        OmicScope (OmicScope object): OmicScope Experiment
        pvalue (float, optional): p-value threshold. Defaults to 0.05.
        bcol (str, optional): Density plot color. Defaults to '#962558'.
        palette (str, optional): Palette for Multiconditions volcano plot.
         Defaults to 'viridis'.
        non_regulated (str, optional): Color of non-differentially regulated
         proteins. Defaults to '#606060'.
        up_regulated (str, optional): Color of up-regulated proteins for volcano
        with 2 conditions. Defaults to '#E4001B'.
        down_regulated (str, optional): Color of down-regulated proteins for volcano
        with 2 conditions. Defaults to '#6194BC'.
        save (str, optional): Path to save figure. Defaults to ''.
        dpi (int, optional): . Resolution to save figure. Defaults to 300.
        vector (bool, optional): Save figure in as vector (.svg). Defaults to
        True.
    """
    OmicScope = copy.copy(OmicScope)
    if len(OmicScope.Conditions) == 2:
        volcano_2cond(OmicScope, *Proteins, pvalue=pvalue, bcol=bcol,
                    non_regulated=non_regulated, up_regulated=up_regulated,
                    down_regulated=down_regulated,
                    save=save, dpi=dpi, vector=vector)
    if len(OmicScope.Conditions) > 2:
        volcano_Multicond(OmicScope=OmicScope, *Proteins,
                          pvalue=pvalue, palette=palette, bcol=bcol,
                          save='', dpi=dpi, vector=vector)



def volcano_qvalue(OmicScope, color='darkcyan', palette='viridis',
                   save='', vector=True, dpi=300,):
    """Show distribution of p-adjusted in a Volcano plot

    Args:
        OmicScope (OmicScope object): OmicScope Experiment
        color (str, optional): color of density plot. Defaults to 'darkcyan'.
        palette (str, optional): Color of q-value distribution.
        Defaults to 'viridis'.
        save (str, optional): Path to save figure. Defaults to ''.
        dpi (int, optional): figure resolution. Defaults to 300.
        vector (bool, optional): Save figure in as vector (.svg). Defaults to
        True.
    """

    # Volcano and histogram
    # definitions for the axes
    plt.style.use('default')
    plt.rcParams["figure.dpi"] = dpi
    OmicScope = copy.copy(OmicScope)
    # Definitions for the axes
    df_initial = OmicScope.quant_data
    fc = df_initial['log2(fc)']
    max_fc = max([x for x in fc if x < max(fc)])
    min_fc = min([x for x in fc if x > min(fc)])
    fc = fc.replace([np.inf], max_fc + 1)
    fc = fc.replace([-np.inf], min_fc - 1)
    pval = df_initial['-log10(p)']
    max_pval = max([x for x in pval if x < max(pval)])
    pval = pval.replace([np.inf], max_pval + 1)
    df_initial['-log10(p)'] = pval
    df_initial['log2(fc)'] = fc
    # dimensions of figure
    left, width = 0.1, 0.65
    bottom, height = 0.1, 0.65
    spacing = 0.02
    rect_scatter = [left, bottom, width, height]
    rect_histx = [left, bottom + height + spacing, width, 0.2]
    # Plot Scatter
    plt.style.use('bmh')
    fig = plt.figure(figsize=(8, 8))
    ax_scatter = plt.axes(rect_scatter)
    plt.xlabel("log2( FC)")
    plt.ylabel("-log10(p)")
    ax_scatter.tick_params(direction='in', top=True)
    plt.grid(b=None)
    ax_scatter.plot(alpha=0.5)
    ax_histx = plt.axes(rect_histx)
    plt.ylabel("Density")
    plt.title(label=OmicScope.experimental[0] + ' - ' + OmicScope.ctrl, loc='left')
    ax_histx.tick_params(direction='in', labelbottom=False)
    ax_histx.set_facecolor('white')
    ax_histx.grid(b=None)
    # Plot Kdes
    sns.kdeplot(fc, shade=True, color=color, alpha=0.8, edgecolor='black')

    plt.xlabel("Density")
    ax_scatter.scatter(fc, pval, c=df_initial['pAdjusted'], cmap=plt.cm.get_cmap(palette), alpha=0.5)

    ax_scatter.set_facecolor('white')
    sns.despine()
    ax_scatter.axhline(-np.log10(0.05), c='black', linestyle='--', linewidth=0.7)
    ax_scatter.axvline(0, c='black', linestyle='--', linewidth=0.7)
    limh = round(fc.max(), 0)
    liml = round(fc.min(), 0)
    limp = round(pval.max() + 0.5, 0)
    ax_scatter.set_xlim((liml - 0.5, limh))
    ax_scatter.set_ylim((0, limp))
    ax_histx.set_xlim(ax_scatter.get_xlim())
    # Palette for q-values
    sm = plt.cm.ScalarMappable(cmap=palette,
                           norm=plt.Normalize(vmin=df_initial['pAdjusted'].min(),
                                              vmax=df_initial['pAdjusted'].max()))
    cbar = plt.colorbar(sm, cax=fig.add_axes([0.8, 0.1, 0.03, 0.65]))
    cbar.set_label('p-Adjusted')
    if save != '':
        if vector == True:
            plt.savefig(save + 'volcano_qvalue.svg')
        else:
            plt.savefig(save + 'volcano_qvalue.png', dpi=dpi)
    plt.show()


def heatmap(OmicScope, *Proteins, pvalue=0.05, c_cluster=True,
            palette='RdYlBu_r', line=0.01, color_groups='tab20',
            save='', dpi=300, vector=True):
    """ Heatmap

    Args:
        OmicScope (OmicScope object): OmicScope Experiment
        pvalue (float, optional): P-value threshold. Defaults to 0.05.
        c_cluster (bool, optional): Applies Hierarchical clustering for
        columns. Defaults to True.
        color_groups (str, optional): Palette for group colors.
        Defaults to 'tab20'.
        palette (str, optional): Palette for protein abundance. Defaults to 'RdYlBu_r'.
        line (float, optional): Line width. Defaults to 0.01.
        save (str, optional): Path to save figure. Defaults to ''.
        dpi (int, optional): figure resolution. Defaults to 300.
        vector (bool, optional): Save figure in as vector (.svg). Defaults to
        True.
    """
    plt.style.use('default')
    plt.rcParams["figure.dpi"] = dpi
    OmicScope = copy.copy(OmicScope)
    FoldChange_cutoff = OmicScope.FoldChange_cutoff
    df = OmicScope.quant_data
    Conditions = OmicScope.Conditions
    # Creating Heatmap Matrix
    heatmap = df[df.loc[:, 'pvalue'] <= pvalue]
    heatmap = heatmap.loc[(heatmap['log2(fc)'] <= -FoldChange_cutoff)
                           | (heatmap['log2(fc)'] >= FoldChange_cutoff)]
    heatmap = heatmap.dropna()
    # Filtering for specific proteins
    if len(Proteins) > 0:
        heatmap = heatmap[heatmap['gene_name'].isin(Proteins)]
    heatmap = heatmap.set_index('gene_name')
    heatmap = heatmap.loc[:, heatmap.columns.str.contains('\.')]
    # Log2 transform
    heatmap = np.log2(heatmap).replace([-np.inf], int(0))
    colnames = heatmap.columns.str.split('.')
    Col = []
    for lists in colnames:
        for i, c in enumerate(lists):
            if i == 1:
                Col.append(c)
    heatmap.columns = Col
    # Creating matrix for group colors
    ngroup = len(Conditions)
    pal = sns.color_palette(palette=color_groups, as_cmap=False, n_colors=ngroup)
    dic = {}
    for C, c in zip(Conditions, pal):
        dic.update({C: c})
    replacer = dic.get
    colcolors = [replacer(n, n) for n in Col]
    # Title
    title = 'Heatmap - ' + OmicScope.ctrl + ' vs ' + '-'.join(OmicScope.experimental)
    # Plot
    sns.clustermap(heatmap,
              cmap=palette, z_score=0, linewidths=line, linecolor='black', col_colors=colcolors,
              col_cluster=c_cluster,
              figsize=(14, 14), center=0).fig.suptitle(title, y=1.02, size=30)
    # Save
    if save != '':
        if vector == True:
            plt.savefig(save + 'heatmap.svg')
        else:
            plt.savefig(save + 'heatmap.png', dpi=dpi)
    plt.show()


def correlation(OmicScope, *Proteins, pvalue=1.0,
            Method='pearson', palette='RdYlBu_r', line=0.005,
            color_groups='tab20',
            save='', dpi=300, vector=True):
    """Pairwise correlation plot for samples.

    Args:
        OmicScope (OmicScope object): OmicScope Experiment.
        pvalue (float, optional): p-value threshold. Defaults to 1.0.
        Method (str, optional): Method of correlation. Defaults to 'pearson'.
        palette (str, optional): Palette for R-distribution. Defaults to 'RdYlBu_r'.
        line (float, optional): Line width. Defaults to 0.005.
        color_groups (str, optional): Color of each group. Defaults to 'tab20'.
        save (str, optional): Path to save figure. Defaults to ''.
        dpi (int, optional): figure resolution. Defaults to 300.
        vector (bool, optional): Save figure in as vector (.svg). Defaults to
        True.
    """
    plt.style.use('default')
    plt.rcParams["figure.dpi"] = dpi
    OmicScope = copy.copy(OmicScope)
    FoldChange_cutoff = OmicScope.FoldChange_cutoff
    df = OmicScope.quant_data
    Conditions = OmicScope.Conditions
    # Selecting Matrix for correlation
    pearson = df[df.loc[:, 'pvalue'] <= pvalue]
    pearson = pearson.loc[(pearson['log2(fc)'] <= -FoldChange_cutoff)
                           | (pearson['log2(fc)'] >= FoldChange_cutoff)]
    pearson = pearson.dropna()
    # Filtering for specific proteins
    if len(Proteins) > 0:
        pearson = pearson[pearson['gene_name'].isin(Proteins)]
    pearson = pearson.set_index('gene_name')
    pearson = pearson.loc[:, pearson.columns.str.contains('\.')]
    # log2 transform
    pearson = np.log2(pearson).replace([-np.inf], int(0))
    # Performing Pearson's Correlation
    corr_matrix = pearson.corr(method=Method)
    # Creating matrix for group colors
    colnames = corr_matrix.columns.str.split('.')
    Col = []
    for lists in colnames:
        for i, c in enumerate(lists):
            if i == 1:
                Col.append(c)
    corr_matrix.columns = Col
    ngroup = len(Conditions)
    pal = sns.color_palette(palette=color_groups, as_cmap=False, n_colors=ngroup)
    dic = {}
    for C, c in zip(Conditions, pal):
        dic.update({C: c})
    replacer = dic.get
    colcolors = [replacer(n, n) for n in Col]
    # Title
    title = 'Heatmap - ' + OmicScope.ctrl + ' vs ' + '-'.join(OmicScope.experimental)
    # Plot
    sns.clustermap(corr_matrix,
                    xticklabels=corr_matrix.columns, row_colors=colcolors,
                    yticklabels=corr_matrix.columns, col_colors=colcolors,
                    cmap=palette, linewidths=line, linecolor='black').fig.suptitle(title, y=1.02, size=30)
    if save != '':
        if vector == True:
            plt.savefig(save + 'pearson.svg')
        else:
            plt.savefig(save + 'pearson.png', dpi=dpi)
    plt.show()
    plt.show(block=True)


def DynamicRange(OmicScope, *Proteins, color='#565059',
                protein_color='orange', max_min=False,
                 min_color='#18ab75', max_color='#ab4e18', dpi=300, save = '',
                 vector=True):

    """Dynamic range plot

    Args:
        OmicScope (OmicScope object): OmicScope Experiment
        mean_color (str, optional): Color for each dot (mean abundance).
        Defaults to '#565059'.
        protein_color (str, optional): Color of specific proteins (Args).
        Defaults to 'orange'.
        max_min (bool, optional): Plot the maximum and minimum abundance
        value for each protein. Defaults to False.
        min_color (str, optional): Color of minimum values. Defaults to '#1daec7'.
        max_color (str, optional): Color of maximum values. Defaults to '#f7463d'.
        save (str, optional): Path to save figure. Defaults to ''.
        dpi (int, optional): figure resolution. Defaults to 300.
        vector (bool, optional): Save figure in as vector (.svg). Defaults to
        True.
    """

    plt.style.use('default')
    plt.rcParams["figure.dpi"] = dpi
    OmicScope = copy.copy(OmicScope)
    df = OmicScope.quant_data
    df_initial = df
    # Dictionary for Accessions
    accession = dict(zip(df.Accession, df.gene_name))
    df = df.set_index('Accession')
    df = df.loc[:, df.columns.str.contains('\.')]
    df = np.log10(df).transpose()
    # Getting Mean, Max and Min values for each protein
    df = df.describe().transpose()
    df = df.dropna()
    df = df.reset_index()
    # Applying Dictionary to get gene name
    df['gene_name'] = df.Accession.replace(accession)
    # Ranking entities
    df['rank'] = df['mean'].rank(method='first')
    # Return variation for each protein
    ax_scatter = plt.axes()
    if max_min == True:
        plt.scatter(y=df['rank'], x=df['min'],
                    alpha=0.7, s=2, c=min_color)
        plt.scatter(y=df['rank'], x=df['max'],
                    alpha=0.7, s=2, c=max_color)
    # Plot mean
    plt.scatter(y=df['rank'], x=df['mean'],
                c=color, s=10, alpha = 0.5,
                linewidths=0.5)
    # Highlight specific proteins
    if len(Proteins) > 0:
        df = df[df.gene_name.isin(Proteins)]
        plt.scatter(y=df['rank'], x=df['mean'],
            c=protein_color, s=10, alpha = 1, edgecolors='black', 
            linewidths=0.5)
        ls_final = df
        ls_final = ls_final[['gene_name', 'rank', 'mean']]
        from adjustText import adjust_text
        texts = []
        for a, b, c in zip(ls_final['mean'], ls_final['rank'],
                           ls_final['gene_name']):
            texts.append(ax_scatter.text(a, b, c, size=8))
            adjust_text(texts, ax=ax_scatter, force_points=0.25, force_text=0.25,
                        expand_points=(1.5, 1.5), expand_text=(1.5, 1.5),
                        arrowprops=dict(arrowstyle="-", color='black', lw=0.5))
    plt.grid(b=False)
    plt.xlabel('log10(Abundance)')
    plt.ylabel('Rank')
    plt.title('Dynamic Range')
    if save != '':
        if vector == True:
            plt.savefig(save + 'DynamicRange.svg')
        else:
            plt.savefig(save + 'DynamicRange.png', dpi=dpi)
    sns.despine()
    plt.show()


def pca(OmicScope, pvalue=1.00, scree_color = '#900C3F',
        marks=False, palette='tab20', FoldChange_cutoff=0,
        save='', dpi=300, vector=True):
    """ Perform Principal Component Analysis.

    Args:
        OmicScope (OmicScope object): OmicScope experiment
        pvalue (float, optional): p-value threshold. Defaults to 1.00.
        scree_color (str, optional): Color of Scree plot. Defaults to '#900C3F'.
        marks (bool, optional): Insert group annotation. Defaults to False.
        palette (str, optional): Palette for groups. Defaults to 'tab20'.
        FoldChange_cutoff (int, optional): Fold change threshold. Defaults to 0.
        save (str, optional): Path to save figure. Defaults to ''.
        dpi (int, optional): figure resolution. Defaults to 300.
        vector (bool, optional): Save figure in as vector (.svg). Defaults to
        True.
    """
    plt.style.use('default')
    plt.rcParams["figure.dpi"] = dpi
    OmicScope = copy.copy(OmicScope)
    df = OmicScope.quant_data
    FoldChange_cutoff = OmicScope.FoldChange_cutoff
    # Filtering P-value and Fold Change
    df = df[df['pvalue'] < pvalue]
    if len(OmicScope.Conditions) == 2:
        df = df.loc[(df['log2(fc)'] <= -FoldChange_cutoff) | (df['log2(fc)'] >= FoldChange_cutoff)]
    df = df.loc[:, df.columns.str.contains('\.')]
    samples = df.columns
    # Getting Conditions
    Conditions = OmicScope.Conditions
    group = []
    for i in Conditions:
        ncond = df.columns.str.contains(i).sum()
        nlist = list(itertools.repeat(i, ncond))
        group.extend(nlist)
    # Center and Scale data
    scaled_data = preprocessing.scale(df.T)
    pca = PCA()  # PCA object
    pca.fit(scaled_data)  
     # get PCA coordinates for scaled_data
    pca_data = pca.transform(scaled_data) 
    # Scree plot
    per_var = np.round(pca.explained_variance_ratio_ * 100, decimals=1)
    labels = ['PC' + str(x) for x in range(1, len(per_var) + 1)]
    fig, (ax1, ax2) = plt.subplots(1, 2)
    fig.set_figwidth(16)
    fig.set_figheight(7)
    ax1.bar(x=range(1, len(per_var) + 1), height=per_var, tick_label=labels,
            color=scree_color, edgecolor="black", linewidth=1)
    ax1.set(ylabel='Percentage of Explained Variance',
            xlabel='Principal Component', title='Scree plot')
    ax1.tick_params(labelrotation=45)
    sns.despine()
    ax1.grid(b=False)
    # PC1 vs PC2 plot
    pca_df = pd.DataFrame(pca_data, index=samples, columns=labels)
    sns.scatterplot(x="PC1", y="PC2", data=pca_df, hue=list(pca_df.index.str.split('\.').str[1]), palette=palette,
                    edgecolor='black', linewidth=1, s=100, alpha=0.7)
    plt.title('Principal Component Analysis ' + '(pvalue=' + str(pvalue) + ')')
    plt.xlabel('PC1 - {0}%'.format(per_var[0]))
    plt.ylabel('PC2 - {0}%'.format(per_var[1]))
    plt.grid(b=False)
    sns.despine()
    #Annotate samples in PCA plot
    if marks == True:
        for sample in pca_df.index:
            plt.annotate(sample, (pca_df.PC1.loc[sample], pca_df.PC2.loc[sample]))
    if save != '':
        if vector == True:
            plt.savefig(save + 'pca.svg')
        else:
            plt.savefig(save + 'pca.png', dpi=dpi)
    plt.show()


def bar_protein(OmicScope, *Proteins, logscale=True,
                palette='Spectral', save='', dpi=300,
                vector=True):
    """Bar plot to show protein abundance in each condition

    Args:
        OmicScope (OmicScope object): OmicScope Experiment
        logscale (bool, optional): Apply abundance log-transformed.
        Defaults to True.
        palette (str, optional): Palette for groups. Defaults to 'Spectral'.
        save (str, optional): Path to save figure. Defaults to ''.
        dpi (int, optional): figure resolution. Defaults to 300.
        vector (bool, optional): Save figure in as vector (.svg). Defaults to
        True.
    """
    plt.rcParams['figure.dpi']=dpi
    df = copy.copy(OmicScope.quant_data)
    # Proteins to plot
    df = df[df['gene_name'].isin(Proteins)]
    # Get conditions
    ctrl = [copy.copy(OmicScope.ctrl)]
    conditions = copy.copy(OmicScope.Conditions)
    conditions.remove(ctrl[0])
    # Get protein abundance for each condition 
    df = df.set_index('gene_name')
    df = df.iloc[:,df.columns.str.contains('\.')]
    df = df.melt(ignore_index=False)
    df = df.reset_index()
    df[['Sample', 'Condition']] = df['variable'].str.split('.', expand=True)
    df = df[['Sample', 'Condition', 'gene_name', 'value']]
    # Apply log transformation
    if logscale == True:
        df['value'] = np.log2(df['value'])
        df['value'] = df['value'].replace(-np.inf, np.nan)
    # Size of figure
    sns.set(rc={'figure.figsize': (1.5*len(Proteins),5)})
    custom_params = {"axes.spines.right": False, "axes.spines.top": False}
    sns.set_theme(style="ticks", rc=custom_params)
    # Plot
    if len(Proteins) == 1:
        sns.barplot(x='Condition', y='value',
                   data=df, errwidth=1, capsize=0.07,
                   palette=palette, order=ctrl + conditions,
                   edgecolor='black', linewidth=1, dodge=False)
    else:
        sns.barplot(x='gene_name', y='value', hue='Condition',
                    data=df, errwidth=1, capsize=0.07,
                    palette=palette,
                    edgecolor='black', linewidth=1)
        plt.legend(bbox_to_anchor=(1.0, 1), loc=2, borderaxespad=0.)
    sns.despine()
    plt.title('Abundance - ' + ' and '.join(Proteins))
    plt.xlabel('')
    plt.ylabel('log2(Abundance)')
    if save != '':
        if vector == True:
            plt.savefig(save + 'barplot_' + '_'.join(Proteins) + '.svg')
        else:
            plt.savefig(save + 'barplot_' + '_'.join(Proteins) + '.png', dpi=dpi)
    plt.show()

def boxplot_protein(OmicScope, *Proteins, logscale=True,
                    palette='Spectral',
                    save='', dpi=300, vector=True):
    """Boxplot to show protein abundance in each condition

    Args:
        OmicScope (OmicScope object): OmicScope Experiment
        logscale (bool, optional): Abundance log-transformed. Defaults to True.
        palette (str, optional): Palette for conditions. Defaults to 'Spectral'.
        save (str, optional): Path to save figure. Defaults to ''.
        dpi (int, optional): figure resolution. Defaults to 300.
        vector (bool, optional): Save figure in as vector (.svg). Defaults to
        True.
    """

    plt.rcParams['figure.dpi']=dpi
    df = copy.copy(OmicScope.quant_data)
    # Proteins to plot
    df = df[df['gene_name'].isin(Proteins)]
    # Get conditions
    ctrl = [copy.copy(OmicScope.ctrl)]
    conditions = copy.copy(OmicScope.Conditions)
    conditions.remove(ctrl[0])
    # Get protein abundance for each condition 
    df = df.set_index('gene_name')
    df = df.iloc[:,df.columns.str.contains('\.')]
    df = df.melt(ignore_index=False)
    df = df.reset_index()
    df[['Sample', 'Condition']] = df['variable'].str.split('.', expand=True)
    df = df[['Sample', 'Condition', 'gene_name', 'value']]
    # Apply log transformation
    if logscale == True:
        df['value'] = np.log2(df['value'])
        df['value'] = df['value'].replace(-np.inf, np.nan)
    # Size of figure
    sns.set(rc={'figure.figsize': (1.5*len(Proteins),5)})
    custom_params = {"axes.spines.right": False, "axes.spines.top": False}
    sns.set_theme(style="ticks", rc=custom_params)
    # Plot
    if len(Proteins) == 1:
        sns.boxplot(x='Condition', y='value',
                    data=df,
                    palette=palette, linewidth=1)
    else:
        sns.boxplot(x='gene_name', y='value', hue='Condition',
                    data=df,
                    palette=palette, linewidth=1)
        plt.legend(bbox_to_anchor=(1.0, 1), loc=2, borderaxespad=0.)
    sns.despine()
    plt.title('Abundance - ' + ' and '.join(Proteins))
    plt.xlabel('')
    plt.ylabel('log2(Abundance)')
    if save != '':
        if vector == True:
            plt.savefig(save + 'boxplot_' + '_'.join(Proteins) + '.svg')
        else:
            plt.savefig(save + 'boxplot_' + '_'.join(Proteins) + '.png', dpi=dpi)
    plt.show()
    plt.show(block = True)


def MAplot(OmicScope,
           pvalue=0.05, non_regulated='#606060', up_regulated='#E4001B',
           down_regulated='#6194BC', FoldChange_cutoff = 0,
                       save='', dpi=300, vector=True):
    """MA plot

    Args:
        OmicScope (OmicScope object): OmicScope Experiment
        pvalue (float, optional): p-value threshold. Defaults to 0.05.
        non_regulated (str, optional): color for non-regulated proteins.
        Defaults to '#606060'.
        up_regulated (str, optional): color for up-regulated proteins.
        Defaults to '#E4001B'.
        down_regulated (str, optional): color for down-regulated proteins.
        Defaults to '#6194BC'.
        FoldChange_cutoff (int, optional): Foldchange threshold. Defaults to 0.
        save (str, optional): Path to save figure. Defaults to ''.
        dpi (int, optional): figure resolution. Defaults to 300.
        vector (bool, optional): Save figure in as vector (.svg). Defaults to
        True.
    """
    df = copy.copy(OmicScope.quant_data)
    df['TotalMean'] = np.log2(df['TotalMean'])
    df['TotalMean'] = df['TotalMean'].replace(-np.inf, 0.01)
    # Defining axis
    y = df['-log10(p)']
    x = df['log2(fc)']
    # Defining colors
    col = np.where(y > -np.log10(pvalue), np.where(x >= -FoldChange_cutoff,
                    np.where(x < FoldChange_cutoff, non_regulated, up_regulated),
                    down_regulated), non_regulated)
    regulation = np.where(y > -np.log10(pvalue), np.where(x >= -FoldChange_cutoff,
                         np.where(x < FoldChange_cutoff, 'non-regulated',
                         'up-regulated'), 'down-regulated'), 'non-regulated')
    df['col'] = col
    df['Regulation'] = regulation
    #Plot
    sns.set_style("whitegrid")
    sns.scatterplot(x='TotalMean', y='log2(fc)', data=df, hue='Regulation',
                    palette=list(df.col.drop_duplicates()))
    sns.despine()
    plt.axhline(y=0, color='gray', linestyle=':')
    plt.grid(b=False)
    plt.xlabel('log2(Mean)')
    plt.title('MA plot')
    if save != '':
        if vector == True:
            plt.savefig(save + 'MAPlot.svg')
        else:
            plt.savefig(save + 'MAPlot.png', dpi=dpi)
    plt.show(block=True)