# SearchAndDoc_API

A backend API for a Discord app that generates documents throuh providing a discord channel id, a topic, and a date period. The project leverages Large Language Models (LLMs) to rewrite the messages into content suitable for documentation through filtering Discord channels and selecting only relevant information.

## Table of Contents

- [Features](#features)
- [Tech stack](#tech-stack)
- [Architecture](#server-architecture)
- [Installation](#installation)
- [Usecases](#use-cases)
- [Design Patterns](#design-patterns-and-diagrams)
- [Quality Attributes](#quality-attributes)

---

## Features

- Create Solr Collection
- Index data in solr collection
- Perform semantic search which selects the messages realted to a topic and provides a document with the rewritten messages in markdown.

---

## Tech Stack

- **Python 3.9+**
- **FastAPI** – Modern, high-performance web framework for APIs
- **Uvicorn** – Lightning-fast ASGI server for FastAPI
- **Solr** – Search engine backend

---

## Server Architecture

The repo uses a **Monolothic** server architecture

### System architecture

The system follows an **MVC-inspired** software architecture, structured for APIs (no front-end views)

![alt text](https://github.com/alkaline-0/SearchAndDoc_API/blob/main/diagrams/diagram.png?raw=true)

- **Routers**:

  - Receive and validate HTTP requests.
  - Delegate processing to the appropriate service layer.
  - Located in the `routers/` directory.

- **Service Layers**:

  - Handles the business workflow.
  - Orchestrate communication between routes, models, and LLMs.
  - Located in the `services/` directory.

- **Models**:

  - Define Pydantic schemas and provide data models for interacting with data service layers and the database.
  - validates the objects based on the business rules, then passes them to the data service layer which will format them to go into the database.
  - Located in the `models/` directory.

- **Infrastructure Layer**:

  - Manage creation and configuration of database connections and clients.
  - Ensure efficient and reusable connection handling.
  - Located in the `db/infrastructure` directory.

- **Data Service Layers**:

  - Orchisterates complex workflow with data access layer
  - Ensures Separation of concerns and abstraction.
  - Located in the `db/services` directory.

- **Data access Layers**:

  - Encapsulates the logic for interacting with the Solr database.
  - Performs CRUD operations on database level.

- **Database (Solr)**:
  - Stores and indexes Discord messages and metadata.
  - Supports advanced search queries and retrieval.

### Project Structure

.
|── app/ # FastAPI application entrypoint

|── routers/ # API routers (endpoints)

|── services/ # Service layers

|── models/ # Pydantic models and data schemas

|── utils/ # Utility functions and helpers

|── db/ # Database configs and connection factories

|── tests/ # Automated tests

|── pyproject.toml # Project metadata and dependencies

|── README.md

---

## Installation

### Requirements

- Python >= 3.9
- FastAPI and uvicorn
- [uv](https://docs.astral.sh/uv/) (for dependency management)
- Docker

### Setup

1. **Install Python 3.9.20 with uv**

```shell
uv python install 3.9
```

2. **Create and Activate a Virtual Environment**

```shell
uv venv
source .venv/bin/activate
```

3. **Install Project Dependencies**

```shell
uv sync
```

4. **Create .env file from .env.example**

```shell
populate the values in the .env file
to setup auth for solr make sure to edit solr-config.sh with the password you will use in docker
and make sure to have a groq api key
```

5. **Start docker containers**

```shell
docker-compose up -d
```

6. ** Run the uvicorn server**

```shell
 ./.venv/bin/uvicorn app.main:create_app --factory --host 0.0.0.0 --port 3001 --reload
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
python -m pytest
```

### Deployment

- The API is available at [http://35.204.26.63:3001](http://35.204.26.63:3001)
- Interactive API docs: [http://35.204.26.63:3001/docs](http://35.204.26.63:3001/docs)

---

## Use cases:

This project provides a backend for managing, indexing, and searching Discord messages and related documents using Solr. Below are the main use cases currently supported:

### Implemented Use Cases (User-Facing)

- Create Collection

  - Users can create new Solr collections to organize and store documents.

  - Endpoint: POST /create-collection

  - Status: ✅ Implemented

- Index Documents

  - Users can index (add) new documents/messages into a specified Solr collection for later retrieval and search.

  - Endpoint: POST /index-data

  - Status: ✅ Implemented

- Create document

  - Users can create a document out of the indexed discord messages through specifying a topic.
  - Users can create a document out of the indexed discord messages in a specified time period through specifying a topic and a start-date and end-date.

  - Endpoint POST /create-document

  - Status: ✅ Implemented

### Internal/Admin Use Cases

- Delete Collection

  - Admins can delete existing Solr collections for maintenance or cleanup purposes.

  - Status: ✅ Implemented (admin/internal use only)

### Planned/Not Yet Implemented

- White listing urls of servers that can communicate with this api.
- rate limiting.
- caching.

---

## Design Patterns and diagrams:

1. Behavioral:

- STRATEGY PATTERN:
  - used in semantic search service layer (db/services/semantic_search_service.py) by injecting reranker strategy and retreiever strategy. This allows plugging in different algorithms without having coupling between semantic search service and the implementation of the algorithms
    ![alt text](https://github.com/alkaline-0/SearchAndDoc_API/blob/main/diagrams/strategy_pattern.png?raw=true)
  - By injecting SolrHttpClientInterface (an abstraction over the actual request logic), it enables different strategies for sending HTTP requests.
  - By providing a specific algorithm (sentence encoding) for transforming sentences, this allows different implementations of strategy pattern in sentece encoding.
- TEMPLATE pattern:
  - SemanticSearchServiceInterface (abstract class) defines the overall method signature. SemanticSearchService implements these abstract methods, customizing the logic specific to semantic search using retrieval and reranking strategies.
- COMMAND Pattern:
  Each service function encapsulates a single action (services called by the routers.)

2. Creational:

- FACTORY pattern:
  - The factory manages the instantiation of different components needed to interact with Apache Solr and perform search/indexing tasks.
    ![alt text](https://github.com/alkaline-0/SearchAndDoc_API/blob/main/diagrams/factory_pattern.png?raw=true)
    ![alt text](https://github.com/alkaline-0/SearchAndDoc_API/blob/main/diagrams/factory_pattern.png?raw=true)

3. Structural:

- FACADE pattern:
  - Semantic Search Model simplifies the interaction with the semantic_search_service_obj by providing a single method (semantic_search) that internally handles the query validation and delegates the actual search logic to the underlying search service.
- ADAPTER pattern:
  - SentenceTransformerInterface adapts a third-party transformer model to be used in the application.

---

## Quality Attributes:

✅ 1. Performance

- Heavy indexing is offloaded to a separate process via multiprocessing, which avoids blocking the main application thread.
- Lazy evaluation / short-circuiting: For example, semantic search checks early for valid query length and skips unnecessary processing if the input is invalid.
- Lightweight, asynchronous endpoints: FastAPI endpoints are non-blocking (async), supporting high-throughput with low latency.
- Soft commits for fast indexing and defer persistence using background tasks.

✅ 2. Scalability

- Modular, interface-driven design:
  - Services like SolrCollectionModel, IndexingCollectionModel, and SemanticSearchModel are abstracted from implementation via interfaces (e.g., SentenceTransformerInterface), making it easy to swap in scalable backends (e.g., cloud-based ML services or distributed search engines).
- Horizontal task delegation:
  - Indexing workloads can be parallelized or distributed due to isolated worker functions (\_index_data_worker).
- Decoupling of API and logic layers:
  - FastAPI routes only orchestrate services—they don’t embed logic, enabling future scaling into microservices if needed.

✅ 3. Maintainability

- Clear separation of concerns:
  - Controllers (routes), models, services, and configurations are well-separated.
- Use of design patterns:
  - Strategy, Template, and Adapter patterns are employed to cleanly separate variable logic.
- Dependency injection:
  - Components like Logger and configuration objects (SolrConfig, MLConfig) are injected, making testing and substitution easier.
