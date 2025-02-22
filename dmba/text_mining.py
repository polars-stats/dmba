"""
Utility functions for "Data Mining for Business Analytics: Concepts, Techniques, and
Applications in Python"

(c) 2019-2023 Galit Shmueli, Peter C. Bruce, Peter Gedeck
"""

from polars import DataFrame
from jax.experimental import sparse
from sklearn.feature_extraction.text import CountVectorizer


def print_term_document_matrix(
        count_vect: CountVectorizer,  # noqa: ARG001
        counts: sparse.BCOO) -> None:
    """ Print term-document matrix created by the CountVectorizer
    Input:
        count_vect: scikit-learn Count vectorizer
        counts: term-document matrix returned by transform method of counter vectorizer
    """
    shape = counts.shape
    columns = [f'S{i}' for i in range(1, shape[0] + 1)]
    print(DataFrame(data=counts.todense().transpose(), schema=columns))
