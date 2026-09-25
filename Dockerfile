FROM python:3.13-slim

# gcc/g++ are required by triton 3.8, which JIT-compiles its C driver on first use
# (a slim image without a compiler silently falls back to CPU in fla).
RUN apt-get update \
 && apt-get install -y --no-install-recommends ca-certificates curl gcc g++ make \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# torch first (CUDA 12.8 blob, sm_120/Blackwell kernels), then the fused-Qwen3.5 deps.
# triton/fla are pinned with --no-deps so they override torch's transitive triton==3.4.0
# pin without the pip resolver fighting over it (matches the kev Modal image pins).
RUN pip install --no-cache-dir torch==2.8.0 \
 && pip install --no-cache-dir --no-deps triton==3.8.0 flash-linear-attention==0.5.2 fla-core==0.5.2 einops

# The kev serving package is vendored under ./kev-src: a snapshot of the kev monorepo
# (https://github.com/jaredpalmer/kev) holding pyproject.toml, README.md, LICENSE and kev/.
# Refreshing it is a one-liner, see README "Refreshing the vendored kev package".
COPY kev-src/ ./kev-src/
RUN pip install --no-cache-dir "./kev-src[serve]"

# The [serve] resolution downgrades triton to torch's pin (3.4.0); the fused Qwen3.5
# path needs >= 3.7.1, so re-apply the pinned build after every resolver run.
RUN pip install --no-cache-dir --no-deps triton==3.8.0

ENV HF_HOME=/root/.cache/huggingface \
    KEV_RUN=jaredpalmer/kev-4b \
    KEV_HOST=0.0.0.0 \
    KEV_PORT=8008

EXPOSE 8008

CMD ["sh", "-c", "exec python -m kev.serve --run \"$KEV_RUN\" --host \"$KEV_HOST\" --port \"$KEV_PORT\""]