# Prueba de carga controlada - Dashboard Videojuegos

## Objetivo

Determinar, de forma reproducible y controlada, la carga máxima estable que
soportan los tres servicios HTTP del dashboard (frontend, backend, FastAPI)
protegidos con Fail2Ban, usando una versión adaptada del script de carga
proporcionado en el laboratorio.

## Alcance

Solo **localhost, loopback (127.0.0.1 / ::1), rangos privados RFC1918 y la red
Docker local autorizada**. El script rechaza cualquier destino externo. No se
prueban sistemas de terceros.

## Servicios evaluados

| Servicio | Host      | Puerto | Endpoint       |
|----------|-----------|--------|----------------|
| Frontend | 127.0.0.1 | 5173   | `/`            |
| Backend  | 127.0.0.1 | 3000   | `/api/health`  |
| FastAPI  | 127.0.0.1 | 8000   | `/health`      |

Todos pasan por el proxy nginx + Fail2Ban del repo `ldap-jwt-api`
(`security-stack/`).

## Modificación realizada al script

**Original** (material del laboratorio):
- targets hardcodeados (`TARGETS = ("victim-protected", "victim-unprotected")`);
- intensidad configurada mediante variables de entorno
  (`CONCURRENCY`, `REQUESTS_PER_SECOND`, `DURATION`).

**Nuevo**:
- `host` posicional y `port` posicional;
- `--path`, `--concurrency`, `--rps`, `--duration`, `--timeout`;
- guard de laboratorio que rechaza destinos no locales/privados;
- resumen final con totales, % de error, duración real y throughput.

El **motor** (workers + rate limiter + conteo) se conservó sin cambios.

## Uso

```
python flood.py HOST PORT [opciones]
```

## Parámetros

| Parámetro       | Significado                                   | Default | Máximo |
|-----------------|-----------------------------------------------|---------|--------|
| `host`          | Host objetivo (solo local/privado)            | —       | —      |
| `port`          | Puerto TCP                                     | —       | 65535  |
| `--path`        | Ruta de la petición                            | `/`     | —      |
| `--concurrency` | Workers simultáneos                            | 40      | 500    |
| `--rps`         | Ritmo máximo agregado de inicio de solicitudes | 50      | 500    |
| `--duration`    | Duración de la prueba (s)                       | 20      | 300    |
| `--timeout`     | Timeout por petición (s)                        | 2       | 60     |

## Restricciones de seguridad

El script resuelve el host y **aborta** si alguna dirección no es loopback o
RFC1918 privada (`10/8`, `172.16/12`, `192.168/16`). No existe opción para
desactivar esta protección. Ejemplos rechazados: `8.8.8.8`, `example.com`.

## Metodología

1. **Baseline**: arrancar en 20 RPS (`concurrency=40`, `duration=20`, `timeout=2`).
2. **Incremento progresivo de RPS**: 20 → 50 → 100 → 150 → 200 → 300 → 400 → 500.
3. Tras **cada** ejecución: health check HTTP, `docker compose ps`, restart count,
   error rate y throughput.
4. Una ejecución es **estable** solo si: el script completa su duración, el
   servicio responde 200 justo después, el contenedor sigue `Up` sin reinicios,
   el error rate < 1% y no hay crash/OOM.
5. **Confirmación**: el candidato a máximo estable se repite ≥ 2 veces más.

Para la medición se varió principalmente `--rps` (y, de ser necesario,
`--concurrency`), manteniendo `duration=20`, `timeout=2`, `concurrency=40`.

## Interacción con Fail2Ban

Los jails HTTP tienen umbrales bajos (100/60/40 por 10 s), que banearían la IP
del host antes de alcanzar el límite real del servicio. Para medir **capacidad**
(no la protección, ya validada por separado):

- se añadió temporalmente `172.25.0.1` a `ignoreip`, **solo en runtime**
  (`fail2ban-client set <jail> addignoreip 172.25.0.1`);
- **nunca** se desactivó Fail2Ban ni se modificó `jail.local` en disco;
- al terminar se restauró (`delignoreip`) y se verificó.

El ban HTTP (y el de LDAPS) ya había sido validado por separado.

## Resultados

| Servicio | Máximo estable | Primer inestable | Error | Reinicios |
|----------|----------------|------------------|-------|-----------|
| Frontend | 500 RPS | No encontrado dentro del límite | 0% | 0 |
| Backend  | 500 RPS | No encontrado dentro del límite | 0% | 0 |
| FastAPI  | 500 RPS | No encontrado dentro del límite | 0% | 0 |

Detalle completo por ejecución en [`results.md`](results.md).

## Interpretación

Los tres servicios permanecieron estables hasta **500 RPS, que es el máximo
permitido por el script de laboratorio. No se encontró un punto de caída dentro
del rango permitido.** El throughput real (~488–497 req/s) está limitado por el
propio generador de carga, no por saturación de los servicios (son triviales:
archivo estático / `{"status":"ok"}` tras nginx en loopback). No se afirma un
punto de caída porque no se probó por encima de 500 RPS.

## LDAP/LDAPS

El puerto 636 **no** se midió con `flood.py`. Se validó por separado que:
- TLS funciona en 636 (bind correcto exitoso);
- los binds inválidos (err=49) se detectan;
- Fail2Ban (jail `ldap-auth`) banea la IP origen;
- 636 queda bloqueado para esa IP durante el ban;
- el unban restaura el acceso.

No se presenta 636 como un benchmark HTTP.

## Ejemplos (PowerShell)

```powershell
python flood.py 127.0.0.1 5173 --path / --concurrency 2 --rps 2 --duration 3
python flood.py 127.0.0.1 3000 --path /api/health --concurrency 2 --rps 2 --duration 3
python flood.py 127.0.0.1 8000 --path /health --concurrency 2 --rps 2 --duration 3
```

## Conclusiones

El script quedó parametrizado (host/puerto + opciones), con una restricción de
seguridad que impide destinos externos, y se ejecuta fuera de los contenedores
de servicio. La búsqueda incremental mostró que los tres servicios resisten el
máximo de carga permitido por el script (500 RPS) sin degradarse ni reiniciarse,
mientras Fail2Ban permanece activo y restaurado a su configuración normal.
