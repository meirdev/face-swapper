FROM --platform=arm64 python:3.11.4-bullseye

RUN apt update && apt install -y libgl1-mesa-glx

ENV PATH="/root/.local/bin:$PATH"

RUN curl -sSL https://install.python-poetry.org | python3 - \
    && poetry config virtualenvs.in-project true
