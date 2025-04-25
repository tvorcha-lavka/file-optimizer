# File Optimizer Microservice

This microservice processes and optimizes image files in various formats.
It receives a task from another microservice, builds a working directory from provided keys,
iterates through all image files, and performs optimization.
The microservice uses the Celery **prefork** pool to process tasks in parallel.

---

## Technology

The microservice utilizes the following technologies:
- **Python 3.11+**
- **Celery** — to accomplish tasks with prefork concurrency.
- **Pillow** — to work with images.
- **Pillow-heif** — to handle HEIF/HEIC image formats.
- **Pydantic** — for data validation.

---

## Project structure

``` plaintext
file-optimizer-py3.11
│
├── .env                  # Environment variables
├── .env.example          # Environment variables example
│
├── Makefile              # Commands for managing
├── pyproject.toml        # Project configuration
│
├── docker                # Configuration for Docker
├── scripts               # Scripts for launching a microservice
│
├── src                   # Source code
│   ├── core              # Basic logic and configuration
│   ├── processors        # Logic for upload processing
│   └── tasks             # Celery tasks
│
└── tests                 # Tests
```

---

## Docker

The microservice uses Docker to package all dependencies and run.
The following files are available for working with Docker Compose:

- **docker-compose.yml** — main configuration file.
- **docker-compose.dev.yml** — configuration file for development.
- **docker-compose.test.yml** — configuration file for testing.
- **docker-compose.rabbitmq.yml** — configuration file for RabbitMQ.

---

## Important files
- **entrypoint.sh** — main script for launching the microservice in production mode.
- **entrypoint.py** — main script for launching the microservice in development mode.
- **task_optimize_images** — tasks to optimize image files.

---

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/tvorcha-lavka/file-optimizer.git
   cd file-optimizer
   ```

2. Install Poetry dependencies:

   ```bash
   poetry install --no-root
   ```

3. Create an `.env` file based on the example:

   ```bash
   cp .env.example .env
   ```
   
4. Set environment variables in `.env` if necessary.

---

## Launch
### Local launch

To run the microservice locally, use commands from the Makefile that automate the use of Docker Compose:

- Build an image:

  ```bash
  make build
  ```
  
- Start services:

  ```bash
  make up
  ```

- To stop services:

  ```bash
  make stop
  ```

- Rebuild (if new dependencies are introduced):

  ```bash
  make rebuild
  ```

---

## Testing

1. Make sure that the `ENV_STATE=development` flag is set in the `.env` file.

2. Build an image for testing:

    ```bash
    make build
    ```

3. Use one of the following commands to run the tests:

   - To run all tests:

     ```bash
     make pytest
     ```

   - To run all tests with coverage:

     ```bash
     make pytest-cov
     ```

---

## License

This project is licensed under the [MIT License](./LICENSE).
