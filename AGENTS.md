# Agent instructions for openapi-python

This project is a Python tool for generating typed Python API clients from OpenAPI specs.
The two primary goals of the project are:

1. Developer ergonomics: attempt to mimic the type safety and flexibility of use provided by [openapi-typescript](https://openapi-ts.dev/) as much as possible.
2. Simplicity and extendability: keep the architecture simple, and make sure users have the necessary interfaces to extend functionality freely.

## General guidelines for writing code
1. Rule #0: Every line of code we write is one we have to maintain, which we don't have time for. The amount of code needs to be small, and the code that we do write needs to be simple and readable, rather than optimal and clever. Write simple, reusable functions. Use existing libraries instead of hand-rolling our own implementations. Go online to verify we're using the latest packages in the right way if you're in doubt. Prefer simple, direct execution paths. Avoid duct-tape solutions when a clear API contract can handle the flow directly, even if the contract requires changes elsewhere. If we can re-write a module of our code to improve the readability or reduce the total lines of code, we should always do this. Always review your changes and adjust to Rule #0, but only once the first draft is finished so you can review in full context of the codebase.
2. Rule #1: Always run `prek run --all-files` to verify that changes are good. Work is not finished before `prek` passes without errors.
3. Rule #2: This project is about typing, and so tests are not unit tests; tests are static type analysis of exemplary scenarios between an OpenAPI spec and the resulting generated client. When introducing a new feature or fixing a bug, add a new contract test under `./tests/contract` or extend an existing one.