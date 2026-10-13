"""retro-agent: an AI retrospective & summary assistant.

The core engine (config, schemas, llm, rag, connectors, agent) depends only on
the Python standard library so it can be imported and tested without installing
anything. FastAPI/uvicorn/redis are optional extras used only for serving.
"""

__version__ = "0.1.0"
