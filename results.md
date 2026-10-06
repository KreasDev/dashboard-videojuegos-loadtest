# Load-test results — maximum stable load (local lab)

Fixed parameters: `--concurrency 40 --duration 20 --timeout 2`. Variable: `--rps`.
Date: 2026-10-06. All targets `127.0.0.1` (via the nginx+Fail2Ban proxy).

**Temporary, reversible change for the capacity phase:** `172.25.0.1` (the host's
IP as seen inside Docker) was added at **runtime only** to `ignoreip` on the three
HTTP jails (`fail2ban-client set <jail> addignoreip 172.25.0.1`) so Fail2Ban would
not ban the benchmark traffic. `jail.local` on disk was never modified. It was
removed afterwards (`delignoreip`) and verified. Fail2Ban protection itself was
already demonstrated in an earlier phase.

"Stable" = script completes + HTTP 200 right after + container `Up` + no restart +
error rate < 1% + no crash/OOM in logs + service not degraded to unavailable.

## Frontend — `http://127.0.0.1:5173/` (dvj-frontend)

| Servicio | RPS | Concurrency | Duración | Total | Éxitos | Fallos | Error % | Throughput | Health post | Restart | Estable |
|----------|-----|-------------|----------|-------|--------|--------|---------|------------|-------------|---------|---------|
| Frontend | 20  | 40 | 20 | 400  | 400  | 0 | 0.0% | 20.0 req/s  | 200 | 0 | ✅ |
| Frontend | 50  | 40 | 20 | 999  | 999  | 0 | 0.0% | 49.9 req/s  | 200 | 0 | ✅ |
| Frontend | 100 | 40 | 20 | 1996 | 1996 | 0 | 0.0% | 99.8 req/s  | 200 | 0 | ✅ |
| Frontend | 150 | 40 | 20 | 2990 | 2990 | 0 | 0.0% | 149.5 req/s | 200 | 0 | ✅ |
| Frontend | 200 | 40 | 20 | 3992 | 3992 | 0 | 0.0% | 199.5 req/s | 200 | 0 | ✅ |
| Frontend | 300 | 40 | 20 | 5982 | 5982 | 0 | 0.0% | 299.1 req/s | 200 | 0 | ✅ |
| Frontend | 400 | 40 | 20 | 7967 | 7967 | 0 | 0.0% | 398.3 req/s | 200 | 0 | ✅ |
| Frontend | 500 | 40 | 20 | 9953 | 9953 | 0 | 0.0% | 497.5 req/s | 200 | 0 | ✅ |
| Frontend | 500 (conf.1) | 40 | 20 | 9948 | 9948 | 0 | 0.0% | 497.1 req/s | 200 | 0 | ✅ |
| Frontend | 500 (conf.2) | 40 | 20 | 9938 | 9938 | 0 | 0.0% | 496.4 req/s | 200 | 0 | ✅ |

## Backend — `http://127.0.0.1:3000/api/health` (dvj-backend)

| Servicio | RPS | Concurrency | Duración | Total | Éxitos | Fallos | Error % | Throughput | Health post | Restart | Estable |
|----------|-----|-------------|----------|-------|--------|--------|---------|------------|-------------|---------|---------|
| Backend | 20  | 40 | 20 | 400  | 400  | 0 | 0.0% | 20.0 req/s  | 200 | 0 | ✅ |
| Backend | 50  | 40 | 20 | 997  | 997  | 0 | 0.0% | 49.8 req/s  | 200 | 0 | ✅ |
| Backend | 100 | 40 | 20 | 1997 | 1997 | 0 | 0.0% | 99.8 req/s  | 200 | 0 | ✅ |
| Backend | 150 | 40 | 20 | 2992 | 2992 | 0 | 0.0% | 149.5 req/s | 200 | 0 | ✅ |
| Backend | 200 | 40 | 20 | 3989 | 3989 | 0 | 0.0% | 199.4 req/s | 200 | 0 | ✅ |
| Backend | 300 | 40 | 20 | 5985 | 5985 | 0 | 0.0% | 299.1 req/s | 200 | 0 | ✅ |
| Backend | 400 | 40 | 20 | 7940 | 7940 | 0 | 0.0% | 395.8 req/s | 200 | 0 | ✅ |
| Backend | 500 | 40 | 20 | 9756 | 9756 | 0 | 0.0% | 487.6 req/s | 200 | 0 | ✅ |
| Backend | 500 (conf.1) | 40 | 20 | 9910 | 9910 | 0 | 0.0% | 495.2 req/s | 200 | 0 | ✅ |
| Backend | 500 (conf.2) | 40 | 20 | 9914 | 9914 | 0 | 0.0% | 495.1 req/s | 200 | 0 | ✅ |

## FastAPI — `http://127.0.0.1:8000/health` (dvj-api)

| Servicio | RPS | Concurrency | Duración | Total | Éxitos | Fallos | Error % | Throughput | Health post | Restart | Estable |
|----------|-----|-------------|----------|-------|--------|--------|---------|------------|-------------|---------|---------|
| FastAPI | 20  | 40 | 20 | 400  | 400  | 0 | 0.0% | 20.0 req/s  | 200 | 0 | ✅ |
| FastAPI | 50  | 40 | 20 | 997  | 997  | 0 | 0.0% | 49.8 req/s  | 200 | 0 | ✅ |
| FastAPI | 100 | 40 | 20 | 1996 | 1996 | 0 | 0.0% | 99.7 req/s  | 200 | 0 | ✅ |
| FastAPI | 150 | 40 | 20 | 2995 | 2995 | 0 | 0.0% | 149.7 req/s | 200 | 0 | ✅ |
| FastAPI | 200 | 40 | 20 | 3992 | 3992 | 0 | 0.0% | 199.5 req/s | 200 | 0 | ✅ |
| FastAPI | 300 | 40 | 20 | 5968 | 5968 | 0 | 0.0% | 298.4 req/s | 200 | 0 | ✅ |
| FastAPI | 400 | 40 | 20 | 7957 | 7957 | 0 | 0.0% | 397.8 req/s | 200 | 0 | ✅ |
| FastAPI | 500 | 40 | 20 | 9943 | 9943 | 0 | 0.0% | 497.0 req/s | 200 | 0 | ✅ |
| FastAPI | 500 (conf.1) | 40 | 20 | 9933 | 9933 | 0 | 0.0% | 495.9 req/s | 200 | 0 | ✅ |
| FastAPI | 500 (conf.2) | 40 | 20 | 9832 | 9832 | 0 | 0.0% | 491.1 req/s | 200 | 0 | ✅ |

## Summary

| Servicio | Máximo estable | Primer inestable | Concurrency usada | Duración | Observaciones |
|----------|----------------|------------------|-------------------|----------|---------------|
| Frontend | 500 RPS (máx permitido por el script) | ninguno encontrado | 40 | 20 s | 0% error, 0 restarts en todo el rango; ~497 req/s reales |
| Backend  | 500 RPS (máx permitido por el script) | ninguno encontrado | 40 | 20 s | 0% error, 0 restarts; ~495 req/s reales |
| FastAPI  | 500 RPS (máx permitido por el script) | ninguno encontrado | 40 | 20 s | 0% error, 0 restarts; ~496 req/s reales |

Ningún servicio presentó un punto de caída dentro del rango permitido por el
script (hasta 500 RPS). No se determinó un punto de caída: **estable hasta el
máximo permitido por el script, 500 RPS.** No se forzó más allá del límite.

El límite observado de throughput real (~495–497 req/s) coincide con el tope de
`--rps 500` del propio generador de carga, no con saturación del servicio: los
tres servicios son triviales (archivo estático / `{"status":"ok"}`) servidos tras
el proxy nginx en loopback, por lo que el cuello de botella es el propio script.

## LDAP/LDAPS (636) — fuera de este benchmark

No se usó `flood.py` contra 636. En una fase previa ya se comprobó por separado:
TLS funciona en 636, binds inválidos (err=49) se detectan, Fail2Ban banea la IP,
636 queda bloqueado para esa IP y el unban restaura el acceso.
