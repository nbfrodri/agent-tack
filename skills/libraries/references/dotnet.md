# .NET packages

The platform covers a lot: minimal APIs, dependency injection, configuration, `ILogger`, `HttpClientFactory`, `System.Text.Json`, `System.CommandLine`. Several well-known packages moved to commercial licences, so read the notes. Names are NuGet packages.

| Need | Default | Alternatives | Notes |
| --- | --- | --- | --- |
| ORM | `Microsoft.EntityFrameworkCore` | `Dapper` | Dapper for hand-written SQL |
| Structured logging | `Serilog` | built-in `ILogger` | |
| Retries and circuit breakers | `Polly` | `Microsoft.Extensions.Http.Resilience` | The Microsoft package wraps Polly for `HttpClient` |
| Validation | `FluentValidation` | data annotations | |
| Object mapping | `Riok.Mapperly` | `Mapster`, hand-written | Mapperly generates code at build time. `AutoMapper` is commercial since 2025 |
| Requests and handlers | plain services | `WolverineFx` | `MediatR` is commercial since 2025 |
| Messaging | `WolverineFx` | `MassTransit` | MassTransit 9 is commercial; version 8 stays Apache-2.0 |
| Typed HTTP clients | `Refit` | | |
| Background jobs | `Hangfire.Core` | `Quartz` | Hangfire is LGPL with paid extras; Quartz is Apache-2.0 |
| Tests | `xunit.v3` | NUnit, MSTest | |
| Mocks | `NSubstitute` | | |
| Assertions | `Shouldly` | | `FluentAssertions` 8 and later needs a paid licence for commercial use; 7.x stays Apache-2.0 |
| Snapshot tests | `Verify.Xunit` | | |
| Real dependencies in tests | `Testcontainers` | | |
| Benchmarks | `BenchmarkDotNet` | | |
| Console interfaces | `Spectre.Console` | | |
