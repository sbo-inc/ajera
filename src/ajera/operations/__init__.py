"""
Transport-agnostic descriptions of every Ajera API call.

Each function here builds an `Operation`: the typed request body, the API
version its session token must be minted at, and the parser that turns the
decoded envelope into the result. Nothing in this package performs I/O, which
is what lets `AjeraClient` and `AsyncAjeraClient` share it rather than each
carrying its own copy of the wire details.

Internal to the package; the public surface is the clients.
"""
