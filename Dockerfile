FROM python:3.13-slim@sha256:7c61056e61ac89e852de05f3dc6fa51a6dd2181797bceed46aa725dd7cb2cd3b

# Triton compiles its CUDA driver at runtime; retain the compiler toolchain.
RUN apt-get update \
 && apt-get install -y --no-install-recommends ca-certificates gcc g++ make \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app
# Exact package versions captured from the existing local serving image.
# --no-deps preserves the deliberate Torch 2.8 / Triton 3.8 combination.
COPY requirements-serving.lock ./
RUN pip install --no-cache-dir --no-deps -r requirements-serving.lock
COPY kev-src/ ./kev-src/
RUN pip install --no-cache-dir --no-deps --no-build-isolation "./kev-src[serve]"

ENV HF_HOME=/root/.cache/huggingface \
    KEV_RUN=jaredpalmer/kev-4b \
    KEV_HOST=0.0.0.0 \
    KEV_PORT=8008
EXPOSE 8008
CMD ["sh", "-c", "exec python -m kev.serve --run \"$KEV_RUN\" --host \"$KEV_HOST\" --port \"$KEV_PORT\""]
