# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
# 🏗 Builder stage
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

ARG USERNAME=code
ARG USER_UID=1000
ARG USER_GID=$USER_UID
ARG POETRY_FLAGS

ENV PYTHONUNBUFFERED=1
ENV POETRY_VIRTUALENVS_CREATE=false

WORKDIR /src

# 🔧 Create user and group
RUN groupadd --gid $USER_GID $USERNAME && \
    useradd --uid $USER_UID --gid $USER_GID -m $USERNAME -s /bin/bash

# 🔧 Install build dependencies
RUN apt-get update -y && \
    apt-get install -y --no-install-recommends curl build-essential libpq-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 🧰 Install poetry via official installer
RUN curl -sSL https://install.python-poetry.org | python3 - && \
    ln -s /root/.local/bin/poetry /usr/local/bin/poetry

# 📦 Copy dependency files
COPY ../pyproject.toml /src/

# 🔧 Install Poetry dependencies
RUN poetry install --no-root $POETRY_FLAGS && \
    poetry cache clear . --all --no-interaction && \
    rm -rf ~/.cache/pip


# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
# 🧩 Final image
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
FROM python:3.11-slim AS base

ARG USERNAME=code
ENV PYTHONPATH=/src
WORKDIR /src

# 🔁 Copy dependencies from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /etc/group /etc/group
COPY --from=builder /etc/passwd /etc/passwd
COPY --from=builder /home/$USERNAME /home/$USERNAME

# 🧹 Remove poetry from final image
RUN rm -f /usr/local/bin/poetry

# 📁 Copy project source code
COPY ../src /src/
COPY ../pyproject.toml /src/

# 📂 Prepare shared volumes and permissions
RUN mkdir -p /mnt/efs/images && \
    mkdir -p /mnt/efs/logs/file-optimizer && \
    chown -R $USERNAME:$USERNAME /mnt/efs && \
    chmod -R 775 /mnt/efs

# 👤 Switch to internal user
USER $USERNAME
