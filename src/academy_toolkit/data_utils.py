# data_utils.py
"""Utility functions for data analysis."""

import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt



def get_enhanced_info(df, sort_by="Fill Rate (%)", ascending=False, verbose=False):
    """
    Generates a detailed column summary for a DataFrame.

    Args:
        df (pd.DataFrame): The DataFrame to analyze.
        sort_by (str): Column to sort the summary by.
        ascending (bool): Sort order.
        verbose (bool): If True, prints additional statistics.

    Returns:
        pd.DataFrame: A DataFrame containing the column summary.
    """
    if df.empty:
        return pd.DataFrame(columns=["Column", "Non-Null", "Fill Rate (%)", "Unique Count", "Dtype"])

    if verbose:
        print(f"Analyzing {len(df)} rows across {len(df.columns)} columns")

    # Calculate metrics
    non_null = df.notna().sum().rename("Non-Null")
    fill_rate = df.notna().mean().mul(100).round(2).rename("Fill Rate (%)")
    unique_counts = df.nunique().rename("Unique Count")
    dtypes = df.dtypes.rename("Dtype")

    # Combine into summary
    summary_df = (pd.concat([non_null, fill_rate, unique_counts, dtypes], axis=1)
                    .rename_axis("Column")
                    .reset_index())

    # Sort if requested
    if sort_by and sort_by in summary_df.columns:
        summary_df = summary_df.sort_values(by=sort_by, ascending=ascending)
    elif sort_by and sort_by not in summary_df.columns:
        print(f"Warning: Column '{sort_by}' not found. Returning unsorted.")

    if verbose:
        missing_cols = (summary_df['Fill Rate (%)'] < 100).sum()
        print(f"Found {missing_cols} columns with missing values")

    return summary_df[["Column", "Non-Null", "Fill Rate (%)", "Unique Count", "Dtype"]]



def get_duplicates_in_subset(df, columns_to_check, sort_results=True, verbose=False):
    """
    Finds and returns duplicate rows based on a subset of columns.

    Args:
        df (pd.DataFrame): The DataFrame to check.
        columns_to_check (list): Columns that define a duplicate.
        sort_results (bool): If True, sorts the results.
        verbose (bool): If True, prints the number of duplicates found.

    Returns:
        pd.DataFrame or None: The duplicate rows DataFrame, or None if none found.
    """
    duplicates_mask = df.duplicated(subset=columns_to_check, keep=False)
    duplicate_rows = df[duplicates_mask]

    if duplicate_rows.empty:
        print("✓ No duplicates found")
        return None

    if verbose:
        print(f"Found {len(duplicate_rows)} duplicate rows ({duplicate_rows.groupby(columns_to_check).ngroups} groups)")

    return duplicate_rows.sort_values(by=columns_to_check) if sort_results else duplicate_rows



def get_highly_correlated_features(data, method="pearson", threshold=0.7, return_pairs=False):
    """
    Identifies highly correlated columns exceeding a given threshold.

    Args:
        data (pd.DataFrame): DataFrame containing numeric data.
        method (str): Correlation method ('pearson' or 'spearman').
        threshold (float): Absolute correlation threshold for a strong correlation.
        return_pairs (bool): If True, returns correlated pairs instead of column list.

    Returns:
        list: Columns to drop, or list of correlated pairs.
    """
    corr_matrix = data.corr(method=method)

    # Upper triangular matrix (avoids duplicates)
    upper_triangle = corr_matrix.where(
        np.triu(
            np.ones_like(corr_matrix, dtype=bool),
            k=1
        )
    )

    hc_indicators = [col for col in upper_triangle.columns if (upper_triangle[col].abs() > threshold).any()]

    if return_pairs:
        hc_pairs = [
            (upper_triangle.index[i], col, upper_triangle.iloc[i,j])
            for i, col in enumerate(upper_triangle.columns)
            for j in range(i)
            if abs(upper_triangle.iloc[i,j]) > threshold
        ]
        return hc_pairs
    return hc_indicators


def plot_correlation_triangle(data,
                              method="pearson",
                              title="Correlation matrix without redundancy",
                              figsize=(12,10), ax=None, threshold=None):
    """
    Plots a triangular correlation heatmap to visualize feature relationships.

    Args:
        data (pd.DataFrame): Numeric data to analyze.
        method (str): Correlation method ('pearson' or 'spearman').
        title (str): Chart title.
        figsize (tuple): Figure size.
        ax (matplotlib.axes.Axes): Axes to plot on.
        threshold (float): Mask correlations below this absolute value.
    """
    corr_matrix = data.corr(method=method)

    if ax is None:
        plt.figure(figsize=figsize)
        ax = plt.gca()

    if threshold is not None:
        mask_threshold = corr_matrix.round(2).abs() <= threshold
        corr_matrix = corr_matrix.mask(mask_threshold)

    cmap = sns.color_palette("coolwarm", as_cmap=True)
    cmap.set_bad(color="lightgray")

    plt.figure(figsize=figsize)
    sns.heatmap(corr_matrix, ax=ax,
            annot=True, fmt=".2f",
            cmap=cmap,
            mask=np.triu(np.ones_like(corr_matrix, dtype=bool), k=1),
            square=True,
            center=0, vmin=-1, vmax=1,
            linewidths=0.5, linecolor='white',
            cbar=not(threshold)  # not needed in threshold mode
    )

    ax.set_title(title)
    ax.tick_params(axis="x", rotation=90)

    if ax is None:
        plt.show()


def describe_and_displot(data, indicators, descriptions=None):
    """
    Displays a compact figure (chart + stats) for each indicator.

    Args:
        data (pd.DataFrame): DataFrame containing all the data.
        indicators (List[str]): List of indicator codes to analyze.
        descriptions (Optional[Dict[str, str]]): Dictionary of indicator descriptions.
    """
    # Standard float formatting
    float_format = lambda x: f"{x: ,.2f}"

    for indicator in indicators:
        # Prepare title, with description if provided
        title = f"Indicator analysis: {indicator}"
        if descriptions:
            description = descriptions.get(indicator, "")
            if description:
                title = f"{title}\n{description}"

        # Create a figure with one row and two columns
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))

        # COLUMN 1: CHART
        sns.histplot(data=data, x=indicator, kde=True, ax=axes[0])
        axes[0].set_title("Indicator distribution")

        # COLUMN 2: DESCRIPTIVE STATISTICS
        stat_text = data[indicator].describe().to_string(float_format=float_format)
        axes[1].text(x=0.2, y=0.5,
                     s=stat_text,
                     fontfamily="monospace",  # For perfect alignment
                     fontsize=12,
                     va="center_baseline")
        axes[1].axis("off")  # Hide axes for the text block

        # Title and final layout
        fig.suptitle(title, fontsize=14, weight="bold")
        plt.tight_layout(rect=[0, 0, 1, 0.90])  # Leave room for the suptitle
        plt.show()


def report_shape_changes(shape_before, shape_after):
    """
    Prints a report on dimension changes between two DataFrame shapes.

    Args:
        shape_before (tuple): Initial DataFrame shape (e.g. df.shape).
        shape_after (tuple): Final DataFrame shape.
    """
    print(f"Shape before: {shape_before}")
    print(f"Shape after:  {shape_after}")

    rows_diff = shape_before[0] - shape_after[0]
    cols_diff = shape_before[1] - shape_after[1]

    # Row changes
    if rows_diff > 0:
        print(f"  ✂️  Rows removed: {rows_diff}")
    elif rows_diff < 0:
        print(f"  ➕ Rows added: {abs(rows_diff)}")

    if cols_diff > 0:
        print(f"  🗑️  Columns removed: {cols_diff}")
    elif cols_diff < 0:
        print(f"  📊 Columns added: {abs(cols_diff)}")

    if rows_diff == 0 and cols_diff == 0:
        print(f"  🔄 No dimension change")
