"""
Utility functions for "Data Mining for Business Analytics: Concepts, Techniques, and
Applications in Python"

(c) 2019-2023 Galit Shmueli, Peter C. Bruce, Peter Gedeck
"""

import io
import os
from tempfile import TemporaryDirectory
from typing import Any, Optional

import jax.numpy as np
import matplotlib.pylab as plt
import polars as pl
from polars import DataFrame, Series
from sklearn.tree import export_graphviz


try:
    import graphviz
    HAS_GRAPHVIZ = True
except ImportError:
    HAS_GRAPHVIZ = False

try:
    from IPython.display import Image
    HAS_IMAGE = True
except ImportError:
    HAS_IMAGE = False


def lift_chart(
    predicted: Series, *, title: str = 'Decile Lift Chart',
    label_bars: bool = True, ax: Any = None, figsize: Any = None) -> Any:
    """ Create a lift chart using predicted values

    Input:
        predictions: must be sorted by probability
        ax (optional): axis for matplotlib graph
        title (optional): set to None to suppress title
        label_bars (optional): set to False to avoid mean response labels on bar chart
    """
    # group the sorted predictions into 10 roughly equal groups and calculate the mean
    name = predicted.name
    mean_percentile = (
        predicted
        .qcut(10)
        .drop('break_point')  # type: ignore
        .groupby('category')
        .agg(pl.col(name).mean())
        .select(name)
    )
    # divide by the mean prediction to get the mean response
    mean_response = mean_percentile / predicted.mean()  # type: ignore

    fig, ax = plt.subplots(figsize=figsize)
    ax.bar(mean_response, color='C0')
    ax.set_ylim(0, 1.12 * mean_response.max() if label_bars else None)
    ax.set_xlabel("Percentile")
    ax.set_ylabel("Lift")
    if title:
        ax.set_title(title)

    if label_bars:
        for p in ax.patches:
            ax.annotate(f'{p.get_height():.1f}', (p.get_x(), p.get_height() + 0.1))
    return ax


def gains_chart(gains: Series, color: str = 'C0', label: Optional[str] = None,
                ax: Any = None, figsize: Any = None) -> Any:
    """ Create a gains chart using predicted values

    Input:
        gains: must be sorted by probability
        color (optional): color of graph
        ax (optional): axis for matplotlib graph
        figsize (optional): size of matplotlib graph
    """
    n_total = len(gains)  # number of records
    n_actual = gains.sum()  # number of desired records

    # get cumulative sum of gains and convert to percentage
    cum_gains = pl.concat([Series([0]), gains.cumsum()])  # Note the additional 0 at the front
    gains_df = DataFrame({'records': list(range(len(gains) + 1)), 'cum_gains': cum_gains})

    fig, ax = plt.subplots(figsize=figsize)
    ax.plot(gains_df['records'], gains_df['cum_gains'], color=color, label=label,
            legend=False)

    # Add line for random gain
    ax.plot([0, n_total], [0, n_actual], linestyle='--', color='k')
    ax.set_xlabel('# records')
    ax.set_ylabel('# cumulative gains')
    return ax


def plot_decision_tree(
    decision_tree: Any, *, feature_names: Optional[list[str]] = None,
    class_names: Optional[list[str]] = None, impurity: bool = False,
    label: str = 'root', max_depth: Optional[int] = None, rotate: bool = False,
    pdf_file: Optional[os.PathLike] = None) -> Any:
    """ Create a plot of the scikit-learn decision tree and show in the Jupyter notebook

    Input:
        decision_tree: scikit-learn decision tree
        feature_names (optional): variable names
        class_names (optional): class names, only relevant for classification trees
        impurity (optional): show node impurity
        label (optional): only show labels at the root
        max_depth (optional): limit
        rotate (optional): rotate the layout of the graph
        pdf_file (optional): provide pathname to create a PDF file of the graph
    """
    if not HAS_GRAPHVIZ:
        return 'You need to install graphviz to visualize decision trees'
    if not HAS_IMAGE and not pdf_file:
        return 'You need to install Image and/or graphviz to visualize decision trees'
    if class_names is not None:
        class_names = [str(s) for s in class_names]  # convert to strings
    dot_data = io.StringIO()
    export_graphviz(decision_tree, feature_names=feature_names, class_names=class_names, impurity=impurity,
                    label=label, out_file=dot_data, filled=True, rounded=True, special_characters=True,
                    max_depth=max_depth, rotate=rotate)
    graph = graphviz.Source(dot_data.getvalue())
    with TemporaryDirectory() as tempdir:
        if pdf_file is not None:
            graph.render('dot', directory=tempdir, format='pdf', outfile=pdf_file)
        if HAS_IMAGE:
            return Image(graph.render('dot', directory=tempdir, format='png'))
        return None

# Taken from scikit-learn documentation


def text_decision_tree(decision_tree: Any, indent: str = '  ', *,
                       as_ratio: bool = True) -> str:
    """ Create a text representation of the scikit-learn decision tree

    Input:
        decision_tree: scikit-learn decision tree
        as_ratio: show the composition of the leaf nodes as ratio (default) instead of counts
        indent: indentation (default two spaces)
    """
    n_nodes = decision_tree.tree_.node_count
    children_left = decision_tree.tree_.children_left
    children_right = decision_tree.tree_.children_right
    feature = decision_tree.tree_.feature
    threshold = decision_tree.tree_.threshold
    node_value = decision_tree.tree_.value

    node_depth = np.zeros(shape=n_nodes, dtype=np.int32)
    is_leaves = np.zeros(shape=n_nodes, dtype=bool)
    stack = [(0, -1)]  # seed is the root node id and its parent depth
    while len(stack) > 0:
        node_id, parent_depth = stack.pop()
        node_depth[node_id] = parent_depth + 1
        # If we have a test node
        if children_left[node_id] != children_right[node_id]:
            stack.append((children_left[node_id], parent_depth + 1))
            stack.append((children_right[node_id], parent_depth + 1))
        else:
            is_leaves[node_id] = True

    rep = []
    for i in range(n_nodes):
        common = f'{node_depth[i] * indent}node={i}'
        if is_leaves[i]:
            value = node_value[i]
            if as_ratio:
                value = [[round(vi / sum(v), 3) for vi in v] for v in value]
            rep.append(f'{common} leaf node: {value}')
        else:
            rule = f'{children_left[i]} if {feature[i]} <= {threshold[i]} else to node {children_right[i]}'
            rep.append(f'{common} test node: go to node {rule}')
    return '\n'.join(rep)
