FROM ubuntu:24.04

RUN apt-get update && apt-get install -y --no-install-recommends \
    clang llvm valgrind hyperfine python3 python3-pip python3-venv \
    git ca-certificates make \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY . .

RUN python3 -m venv /venv && /venv/bin/pip install --no-cache-dir \
    pyyaml pydantic pandas numpy scipy matplotlib rich typer pytest pyarrow

ENV PATH="/venv/bin:$PATH"
# fetch benchmarks at build time so the image is self-contained
RUN bash scripts/fetch_benchmarks.sh /app/benchmarks/polybench
ENV POLYBENCH_ROOT=/app/benchmarks/polybench

CMD ["make", "smoke"]