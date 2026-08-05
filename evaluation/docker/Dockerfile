# Skill-Use-Bench base image
#
# Sandbox image for running the two supported harnesses (Claude Code CLI and
# Codex CLI) against a single skill / task. No internal gateway or proxy is
# installed: agents talk to the official Anthropic / OpenAI endpoints
# directly via ANTHROPIC_API_KEY / OPENAI_API_KEY forwarded from the host.
#
# Build:
#   cd Skill-Use-Bench
#   docker build -t skill-use-bench:latest -f evaluation/docker/Dockerfile .

FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    NPM_CONFIG_PREFIX=/usr/local

# System packages needed by the harnesses and by common task-level tools
# (pdftk-java for PDF form fill, pandoc for docx, poppler-utils for
# pdftoppm/pdftotext, git for VCS-oriented skills, ripgrep for search).
RUN apt-get update && apt-get install -y --no-install-recommends \
        bash \
        ca-certificates \
        curl \
        git \
        gnupg \
        jq \
        nodejs \
        npm \
        pandoc \
        pdftk-java \
        poppler-utils \
        ripgrep \
        tini \
        unzip \
        wget \
    && rm -rf /var/lib/apt/lists/*

# Python packages: keep the ones actually used by tasks and by the scoring
# scripts (openai for the LLM-judge client). Nothing gateway related.
RUN pip install --no-cache-dir \
        requests \
        urllib3 \
        openai \
        pypdf \
        pdfplumber \
        reportlab \
        pandas \
        matplotlib \
        sphinx \
        sphinx-rtd-theme

# Agent CLIs. Pin Claude Code to the same version used in the paper;
# Codex CLI is pinned by its own package resolution.
RUN npm install -g @anthropic-ai/claude-code@2.1.74 @openai/codex \
    && npm cache clean --force \
    && claude --version \
    && codex --version

WORKDIR /workspace/skill-use-bench

# tini as PID 1 so signal propagation and Ctrl+C behave.
ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["bash"]
