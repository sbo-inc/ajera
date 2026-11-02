"""
Database reads described without performing them.

One module per domain, mirroring `ajera.operations`. Each function builds a
`Query`: the parameterised statement and the parser that validates the rows
into the existing schema models. Nothing in this package performs I/O.

Internal to the package; the public surface is `AjeraOdbc`.
"""
