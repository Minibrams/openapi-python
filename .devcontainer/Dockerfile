FROM ubuntu:24.04

WORKDIR /code

RUN apt-get update -y && apt-get install curl wget git zip -y
RUN apt-get update \
  && apt-get install -y --no-install-recommends \
  libatomic1 \
  build-essential \
  pkg-config \
  zlib1g-dev \
  libxml2-dev \
  libxslt1-dev \
  libxmlsec1-dev \
  libxmlsec1-openssl \
  && rm -rf /var/lib/apt/lists/*

# API dev
COPY --from=ghcr.io/astral-sh/uv:0.10.12 /uv /uvx /bin/

COPY pyproject.toml .python-version README.md ./
RUN uv sync

ENV PATH="/code/.venv/bin:$PATH"
ENV PYTHONPATH=/code

RUN uv tool install prek
ENV PATH="/root/.local/bin:$PATH"

# LLMs
RUN curl -fsSL https://bun.com/install | bash
ENV PATH="/root/.bun/bin:$PATH"
RUN bun install -g @openai/codex

# Code
COPY . .

# Git
RUN prek install
