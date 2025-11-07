"""
Feature Engineering Toolkit

A toolkit for feature engineering operations.
This module follows the TOOL NODE pattern:
- Contains helper functions for specific operations
- Has ONE entry function with the same name as the module
- Entry function dispatches to appropriate helper based on 'operation' parameter

Usage in notebook:
    # @node_type: tool
    # @node_id: tool_feature_eng
    from toolkits.data_analysis.feature_engineering import feature_engineering

    # feature_engineering is now available in kernel
    # Call like: feature_engineering(df, operation='polynomial_features')
"""

import pandas as pd


# ============ Helper Functions ============

def _polynomial_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create polynomial features from numeric columns

    Args:
        df: Input DataFrame

    Returns:
        DataFrame with polynomial features added
    """
    df_copy = df.copy()

    # Example: create squared age feature
    if 'age' in df_copy.columns:
        df_copy['age_squared'] = df_copy['age'] ** 2
        df_copy['age_cubed'] = df_copy['age'] ** 3

    return df_copy


def _create_bins(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create binned/categorical versions of numeric columns

    Args:
        df: Input DataFrame

    Returns:
        DataFrame with binned features added
    """
    df_copy = df.copy()

    # Example: bin age into groups
    if 'age' in df_copy.columns:
        df_copy['age_group'] = pd.cut(
            df_copy['age'],
            bins=[0, 30, 50, 100],
            labels=['young', 'middle', 'senior']
        )

    return df_copy


def _normalize(df: pd.DataFrame, columns: list = None) -> pd.DataFrame:
    """
    Normalize numeric columns to 0-1 range

    Args:
        df: Input DataFrame
        columns: List of column names to normalize (all numeric if None)

    Returns:
        DataFrame with normalized columns
    """
    df_copy = df.copy()

    if columns is None:
        columns = df_copy.select_dtypes(include=['number']).columns

    for col in columns:
        if col in df_copy.columns:
            min_val = df_copy[col].min()
            max_val = df_copy[col].max()
            df_copy[col] = (df_copy[col] - min_val) / (max_val - min_val)

    return df_copy


# ============ Entry Function (REQUIRED) ============

def feature_engineering(df: pd.DataFrame, operation: str = 'polynomial_features', **kwargs):
    """
    Feature engineering toolkit entry point

    This is the main interface for the feature engineering toolkit.
    It dispatches to specific operations based on the 'operation' parameter.

    Args:
        df: Input DataFrame
        operation: Which operation to perform
            - 'polynomial_features': Create polynomial features
            - 'create_bins': Create binned categorical features
            - 'normalize': Normalize numeric features
        **kwargs: Additional arguments passed to the operation
            - For 'normalize': columns=list of column names

    Returns:
        Processed DataFrame

    Raises:
        ValueError: If operation is not recognized

    Examples:
        >>> # In notebook, after importing this function
        >>> result = feature_engineering(df, operation='polynomial_features')
        >>> result = feature_engineering(df, operation='create_bins')
        >>> result = feature_engineering(df, operation='normalize', columns=['age', 'income'])
    """
    if operation == 'polynomial_features':
        return _polynomial_features(df)

    elif operation == 'create_bins':
        return _create_bins(df)

    elif operation == 'normalize':
        columns = kwargs.get('columns', None)
        return _normalize(df, columns=columns)

    else:
        raise ValueError(
            f"Unknown operation: {operation}\n"
            f"Available operations: polynomial_features, create_bins, normalize"
        )
