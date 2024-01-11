# aiopulse

A Python library for asynchronous HTTP request processing. It provides a simple and efficient way to generate payloads from user input, build and process request queues in parallel, as well parsing and transforming responses.

# Features

-   Asynchronous HTTP request queue processing
-   Extensible request-building API, including input validation (with `pydantic`) and transformation
-   Customizable response processing and transformation
-   Generate/populate new request data from previous responses (request chaining)
-   Automatic serialization of input schemas and responses

# Installation

You can install aiopulse using pip:

```bash
pip install aiopulse
```

# Usage

```python
from aiopulse import Aiopulse
```
