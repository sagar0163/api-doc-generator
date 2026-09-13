"""Backward-compatible CLI wrapper for `serve.py`."""

from apidocgen.serve import main, generate_swagger_index, serve, SwaggerUIHandler

if __name__ == "__main__":
    main()