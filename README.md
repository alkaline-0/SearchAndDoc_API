# SearchAndDoc_API

A backend API for a Discord app that enhances server search and leverages Large Language Models (LLMs) to generate documentation from project information discussed in Discord channels.

---

## Features

- **Advanced Search**: Enhanced, context-aware search capabilities for Discord servers.
- **Automated Documentation**: Uses LLMs to generate documentation based on channel discussions.
- **REST API**: Exposes endpoints for integration and automation.
- **Modular Design**: Clean separation of concerns for maintainability and extensibility.

---

## Tech Stack

- **Python 3.9+**
- **FastAPI** – Modern, high-performance web framework for APIs
- **Uvicorn** – Lightning-fast ASGI server for FastAPI
- **Pytest** – Robust testing framework
- **pre-commit** – Code formatting and linting hooks
- **pyenv** – Python version and virtual environment management
- **uv** – Fast dependency management with `pyproject.toml`
- **LLM Integration** – For generating documentation (see code for details)
- **Solr** – Search engine backend

---

## Server Architecture

The repo uses a **Monolothic** server architecture

## System architecture
The system follows an **MVC-inspired** software architecture, structured for APIs (no front-end views)

![alt text](https://github.com/alkaline-0/SearchAndDoc_API/blob/main/diagram.png?raw=true)


- **Routers**:
  - Receive and validate HTTP requests.
  - Delegate processing to the appropriate service layer.
  - Located in the `routers/` directory.

- **Models**:
  - Define Pydantic schemas for request/response validation.
  - Provide data models for interacting with service layers and the database.
  - Located in the `models/` directory.

- **Service Layers**:
  - Contain business logic for search, indexing, and documentation generation.
  - Orchestrate communication between models, database, and LLMs.
  - Located in the `services/` directory.

- **Factory Functions**:
  - Manage creation and configuration of database connections and clients.
  - Ensure efficient and reusable connection handling.
  - Located in the `services/` and `utils/` directories.

- **Database (Solr)**:
  - Stores and indexes Discord messages and metadata.
  - Supports advanced search queries and retrieval.

---

## Requirements

- Python >= 3.9
- [pyenv](https://github.com/pyenv/pyenv) (recommended)
- [uv](https://docs.astral.sh/uv/) (for dependency management)
- Running [Solr](https://solr.apache.org/) instance (see `db/config/solr_config.py` for configuration)

---

## Setup

1. **Install Python 3.9.20 with pyenv**
```shell
CONFIGURE_OPTS="--with-openssl=/opt/Homebrew/Cellar/openssl@3/3.4.1" pyenv install -v 3.9.20
```

2. **Set Local Python Version**
```shell
pyenv local 3.9.20
```

3. **Create and Activate a Virtual Environment**
```shell
pyenv virtualenv 3.9.20 <virtual_env_name>
pyenv activate <virtual_env_name>
```

4. **Install Project Dependencies**
```shell
pip install uv
uv sync
```


---

## Development

### Run Pre-Commit Hooks

Format and lint code before committing:

```shell
pre-commit run -a
```

### Run Tests

Execute all tests with:
```shell
python3 -m pytest
````

### Run the Server
Start the FastAPI server with:
```shell
uvicorn main:app --reload
```


- The API will be available at [http://127.0.0.1:8000](http://127.0.0.1:8000)
- Interactive API docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## Project Structure
.
├── main.py # FastAPI application entrypoint
├── routers/ # API routers (endpoints)
├── services/ # Core business logic and integrations
├── models/ # Pydantic models and data schemas
├── utils/ # Utility functions and helpers
├── db/ # Database configs and connection factories
├── tests/ # Automated tests
├── pyproject.toml # Project metadata and dependencies
└── README.md
