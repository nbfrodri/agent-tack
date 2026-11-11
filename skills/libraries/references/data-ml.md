# Data and machine learning libraries (Python)

Follow what the notebook or pipeline already imports: mixing dataframe libraries in one project costs conversions and confusion. Names are PyPI packages.

| Need | Default | Alternatives | Notes |
| --- | --- | --- | --- |
| Dataframes | `polars` | `pandas` | pandas where the surrounding libraries expect it |
| SQL over files and dataframes | `duckdb` | | Reads Parquet and CSV in place |
| Columnar data and Parquet | `pyarrow` | | |
| Arrays and numerics | `numpy`, `scipy` | | |
| Static plots | `matplotlib` | `seaborn` | seaborn for statistical plots; last release 2024-01 |
| Interactive plots | `plotly` | `altair` | |
| Classical machine learning | `scikit-learn` | | |
| Gradient boosting on tables | `xgboost` | `lightgbm` | |
| Deep learning | `torch` | | |
| Pretrained models | `transformers` | | |
| Text embeddings | `sentence-transformers` | | |
| Vector search | `pgvector` | `qdrant-client`, `lancedb` | pgvector when Postgres is already there; LanceDB is embedded |
| SQL transformations in a warehouse | `dbt-core` | | |
| Orchestration | `dagster` | `prefect`, `apache-airflow` | Airflow where the organisation already runs it |
| Data validation | `pandera` | `great-expectations` | Pandera validates dataframes in code; Great Expectations is a larger suite |
| Data apps | `streamlit` | `gradio` | Gradio for model demos |
| Notebooks | `jupyterlab` | `marimo` | marimo notebooks are plain Python files, reactive and diff well in Git |
