import dask
import dask_cudf
import dask.dataframe as dd


def test_read_csv(tmp_path):
    df = dask.datasets.timeseries(dtypes={"x": int, "y": int}, freq="120s").reset_index(
        drop=True
    )
    df.to_csv(tmp_path / "data-*.csv", index=False)

    df2 = dask_cudf.read_csv(tmp_path / "*.csv")
    dd.assert_eq(df, df2)


def test_read_csv_w_bytes(tmp_path):
    df = dask.datasets.timeseries(dtypes={"x": int, "y": int}, freq="120s").reset_index(
        drop=True
    )
    df.to_csv(tmp_path / "data-*.csv", index=False)

    df2 = dask_cudf.read_csv(tmp_path / "*.csv", chunksize="1 kiB")
    assert df2.npartitions > df.npartitions

    dd.assert_eq(df, df2)
