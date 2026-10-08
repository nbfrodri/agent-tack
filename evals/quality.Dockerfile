FROM ubuntu:24.04@sha256:534baea6a22c03a63003dbc8dbe78fe34bc0d7e595d9a9dc9834884ff530eb55
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates git python3 nodejs npm ripgrep procps \
    && rm -rf /var/lib/apt/lists/*
RUN npm install --global @openai/codex@0.160.1
RUN useradd --create-home --uid 1001 --shell /bin/bash dev
USER dev
WORKDIR /home/dev
