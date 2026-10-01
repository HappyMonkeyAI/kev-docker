# Vendored source provenance

The WSL source checkout inspected during this change is jaredpalmer/kev at
73504e51f6ce2ade19c7819d4a5f2d84363cd40f. This is a candidate source revision;
the original vendoring operation did not record its commit, so it is not claimed
as a verified exact origin of this snapshot.

The files committed in kev-src/ are the authoritative source snapshot for builds.
The local serve.py adds --host for container binding. Preserve that change when
updating, record the verified upstream revision, and review the complete source diff.

requirements-serving.lock records package versions from the existing kev-server:local
image on 2026-09-30. Torch 2.8.0 with Triton 3.8.0 intentionally differs from
Torch's dependency metadata. Install the locked list with --no-deps; pip check
will report that known mismatch. Validate changes with actual GPU inference.

The Python base image is digest-pinned. Apt packages are still rolling; this is a package-version
baseline, not a byte-for-byte reproducible image. Package
hashes are follow-up work after validating a fresh GPU build.

The example checkpoint revision is the cached Kev-4B revision inspected locally:
139fdd94f1b6a6ad80cc15e08fcb99cac885a101. Its cached Qwen base revision is
1001bb4d826a52d1f399e183466143f4da7b741b. The checkpoint pin does not independently
pin the base-model lookup performed by Kev; offline validation uses the existing cache.
