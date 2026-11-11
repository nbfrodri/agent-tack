# Rust crates

[blessed.rs](https://blessed.rs) is the community's curated list by need: consult it for a need without a row here. Names are crates.

| Need | Default | Alternatives | Notes |
| --- | --- | --- | --- |
| Async runtime | `tokio` | | |
| HTTP server | `axum` | | Built on `tower` middleware |
| HTTP client | `reqwest` | | |
| Serialisation | `serde` | | With `serde_json`, `toml` and the format crates |
| CLI | `clap` | | |
| Errors in applications | `anyhow` | | |
| Errors in libraries | `thiserror` | | |
| SQL | `sqlx` | `diesel`, `sea-orm` | sqlx checks queries at compile time without an ORM |
| Logging and tracing | `tracing` | | |
| Terminal applications | `ratatui` | | |
| Data parallelism | `rayon` | | |
| Iterator helpers | `itertools` | | |
| Dates and times | `jiff` | `chrono` | chrono where dependencies already use it |
| Snapshot tests | `insta` | | |
| Property-based tests | `proptest` | | |
| Benchmarks | `criterion` | | |
| Desktop applications | `tauri` | | |
