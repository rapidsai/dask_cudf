from functools import partial

import numpy as np
import pytest

import cudf as gd
import dask_cudf as dgd
import dask.dataframe as dd

param_nrows = [5, 10, 50, 100]


@pytest.mark.parametrize("left_nrows", param_nrows)
@pytest.mark.parametrize("right_nrows", param_nrows)
@pytest.mark.parametrize("left_nkeys", [4, 5])
@pytest.mark.parametrize("right_nkeys", [4, 5])
def test_join_inner(left_nrows, right_nrows, left_nkeys, right_nkeys):
    chunksize = 50

    np.random.seed(0)

    # cuDF
    left = gd.DataFrame(
        {
            "x": np.random.randint(0, left_nkeys, size=left_nrows),
            "a": np.arange(left_nrows),
        }.items()
    )
    right = gd.DataFrame(
        {
            "x": np.random.randint(0, right_nkeys, size=right_nrows),
            "a": 1000 * np.arange(right_nrows),
        }.items()
    )

    expect = left.set_index("x").join(
        right.set_index("x"), how="inner", sort=True, lsuffix="l", rsuffix="r"
    )

    # dask_cudf
    left = dgd.from_cudf(left, chunksize=chunksize)
    right = dgd.from_cudf(right, chunksize=chunksize)

    joined = left.set_index("x").join(
        right.set_index("x"), how="inner", lsuffix="l", rsuffix="r"
    )

    dd.assert_eq(expect, joined)

    # Check rows in each groups
    expect_rows = {}
    got_rows = {}

    def gather(df, grows):
        grows[df["index"].values[0]] = (set(df.al), set(df.ar))

    expect.to_pandas().reset_index().groupby("index").apply(
        partial(gather, grows=expect_rows)
    )

    expect.to_pandas().reset_index().groupby("index").apply(
        partial(gather, grows=got_rows)
    )

    assert got_rows == expect_rows


@pytest.mark.parametrize("left_nrows", param_nrows)
@pytest.mark.parametrize("right_nrows", param_nrows)
@pytest.mark.parametrize("left_nkeys", [4, 5])
@pytest.mark.parametrize("right_nkeys", [4, 5])
@pytest.mark.parametrize("how", ["left", "right"])
def test_join_left(left_nrows, right_nrows, left_nkeys, right_nkeys, how):
    chunksize = 50

    np.random.seed(0)

    # cuDF
    left = gd.DataFrame(
        {
            "x": np.random.randint(0, left_nkeys, size=left_nrows),
            "a": np.arange(left_nrows, dtype=np.float64),
        }.items()
    )
    right = gd.DataFrame(
        {
            "x": np.random.randint(0, right_nkeys, size=right_nrows),
            "a": 1000 * np.arange(right_nrows, dtype=np.float64),
        }.items()
    )

    expect = left.set_index("x").join(
        right.set_index("x"), how=how, sort=True, lsuffix="l", rsuffix="r"
    )

    # dask_cudf
    left = dgd.from_cudf(left, chunksize=chunksize)
    right = dgd.from_cudf(right, chunksize=chunksize)

    joined = left.set_index("x").join(
        right.set_index("x"), how=how, lsuffix="l", rsuffix="r"
    )
    dd.assert_eq(expect, joined)


@pytest.mark.parametrize("left_nrows", param_nrows)
@pytest.mark.parametrize("right_nrows", param_nrows)
@pytest.mark.parametrize("left_nkeys", [4, 5])
@pytest.mark.parametrize("right_nkeys", [4, 5])
def test_merge_left(left_nrows, right_nrows, left_nkeys, right_nkeys, how="left"):
    chunksize = 3

    np.random.seed(0)

    left = gd.DataFrame(
        {
            "x": np.random.randint(0, left_nkeys, size=left_nrows),
            "y": np.random.randint(0, left_nkeys, size=left_nrows),
            "a": np.arange(left_nrows, dtype=np.float64),
        }.items()
    )
    right = gd.DataFrame(
        {
            "x": np.random.randint(0, right_nkeys, size=right_nrows),
            "y": np.random.randint(0, right_nkeys, size=right_nrows),
            "a": 1000 * np.arange(right_nrows, dtype=np.float64),
        }.items()
    )

    expect = left.merge(right, on=("x", "y"), how=how)
    expect = (
        expect.to_pandas().sort_values(["x", "y", "a_x", "a_y"]).reset_index(drop=True)
    )

    # dask_cudf
    left = dgd.from_cudf(left, chunksize=chunksize)
    right = dgd.from_cudf(right, chunksize=chunksize)

    joined = left.merge(right, on=("x", "y"), how=how)

    got = joined.compute().to_pandas()  # TODO: remove this
    got = got.sort_values(["x", "y", "a_x", "a_y"]).reset_index(drop=True)

    dd.assert_eq(expect, got)


@pytest.mark.parametrize("left_nrows", [2, 5])
@pytest.mark.parametrize("right_nrows", [5, 10])
@pytest.mark.parametrize("left_nkeys", [4])
@pytest.mark.parametrize("right_nkeys", [4])
def test_merge_1col_left(left_nrows, right_nrows, left_nkeys, right_nkeys, how="left"):
    chunksize = 3

    np.random.seed(0)

    left = gd.DataFrame(
        {
            "x": np.random.randint(0, left_nkeys, size=left_nrows),
            "a": np.arange(left_nrows, dtype=np.float64),
        }.items()
    )
    right = gd.DataFrame(
        {
            "x": np.random.randint(0, right_nkeys, size=right_nrows),
            "a": 1000 * np.arange(right_nrows, dtype=np.float64),
        }.items()
    )

    expect = left.merge(right, on=["x"], how=how)
    expect = expect.to_pandas().sort_values(["x", "a_x", "a_y"]).reset_index(drop=True)

    # dask_cudf
    left = dgd.from_cudf(left, chunksize=chunksize)
    right = dgd.from_cudf(right, chunksize=chunksize)

    joined = left.merge(right, on=["x"], how=how)

    got = joined.compute().to_pandas()  # TODO: remove this
    got = got.sort_values(["x", "a_x", "a_y"]).reset_index(drop=True)

    dd.assert_eq(got, expect)
