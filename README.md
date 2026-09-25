# Kev server in Docker

Serve a released Kev checkpoint as a System One endpoint from Windows (or any host with
Docker + an NVIDIA GPU), launched from the Docker Desktop GUI or `docker compose`.
No WSL shell, no portproxy, no firewall script — Docker Desktop publishes the port on
the host's LAN interface automatically.

The kev Python package itself is vendored under `kev-src/` (Apache-2.0, see `kev-src/LICENSE`),
so this repo builds a fully self-contained image — no other checkout needed.

## Prerequisites

- Docker Desktop for Windows (or Linux/Mac Docker Engine) with NVIDIA GPU passthrough.
  On Windows: **WSL 2 backend** (default) + the GPU toggle in `Settings > Resources`;
  `nvidia-smi` must see your card.
- NVIDIA driver on the host (RTX 5090 needs 615.x or newer for Blackwell sm_120).

## Quickstart

```powershell
Copy-Item .env.example .env      # pick a model in .env, e.g. KEV_MODEL=kev-4b
docker compose up -d --build
```

First run downloads the checkpoint into the named volume `kev-hf-cache`
(~9 GB for kev-4b); later starts reuse it. Watch progress with
`docker compose logs -f`.

Verify:

```powershell
curl http://localhost:8008/v1/models
curl http://<your-lan-ip>:8008/v1/models
```

Point agents at `KEV_API_BASE_URL=http://<your-lan-ip>:8008`.

## Model selection

`KEV_MODEL` in `.env` maps to `jaredpalmer/<KEV_MODEL>`:

| KEV_MODEL  | VRAM            | Notes                                  |
| ---------- | --------------- | -------------------------------------- |
| `kev-0.8b` | ~3 GB           | fastest, lowest accuracy               |
| `kev-4b`   | ~20 GB          | the laptop default (round-10)          |
| `kev-9b`   | ~30 GB          | too big for a 24 GB laptop, use remote |

`KEV_PORT` is the host-side port (`8008`). `KEV_API_KEY` (optional) turns on bearer auth.

## Day-to-day

```powershell
docker compose up -d          # start (also on Docker Desktop launch, restart: unless-stopped)
docker compose stop           # stop without removing the HF cache
docker compose down           # stop + remove container (cache volume survives)
docker compose logs -f        # follow the serve log
docker compose up -d --build  # after a new release or a kev-src refresh
```

The container publishes on the host's `0.0.0.0:<KEV_PORT>` directly, so nothing else is
needed for LAN reachability. (If you previously had a `wsl-lan-setup.ps1` portproxy on the
same port, delete it once: `netsh interface portproxy delete v4tov4 listenaddress=0.0.0.0
listenport=<KEV_PORT>` — otherwise two things fight over the port.)

## Refreshing the vendored kev package

`kev-src/` mirrors `pyproject.toml`, `README.md`, `LICENSE` and the `kev/` package from
https://github.com/jaredpalmer/kev. Note the one deliberate local change: `kev/serve.py`
carries a `--host` flag (upstream hardcodes loopback). Refresh with:

```bash
FROM_CLONE=/path/to/jaredpalmer/kev
cp -r "$FROM_CLONE/pyproject.toml" "$FROM_CLONE/README.md" "$FROM_CLONE/LICENSE" kev-src/
rsync -a --delete "$FROM_CLONE/kev/" kev-src/kev/
# re-apply the --host serve patch if it is not yet upstream, then:
docker compose up -d --build
```

## Troubleshooting

- **GPU not detected in the container**: `docker run --rm --gpus all <image> nvidia-smi`.
  Re-check the Docker Desktop GPU setting; the compose file reserves `capabilities: [gpu]`.
- **Port already in use**: an old portproxy / another server holds `<KEV_PORT>` — see above.
- **Slow first start**: cold start compiles Triton kernels (~1 min), then loads the model;
  the health check has a 5-minute `start_period`.
- **Container stuck unhealthy**: `docker compose logs kev`; a wrong `KEV_MODEL` is the usual
  cause (empty `KEV_RUN` -> bad Hub id).
- **No GPU in triton/fla despite a working `nvidia-smi`**: the image needs a C compiler for
  triton 3.8's JIT driver. Rebuild with the gcc/g++ packages (they are in the Dockerfile).

## License

MIT for this repo (see `LICENSE`). The vendored `kev-src/` package is Apache-2.0
(`kev-src/LICENSE`), copyright its respective authors.