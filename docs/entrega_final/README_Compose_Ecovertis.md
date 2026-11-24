# Ecovertis — ejecución integrada con Docker Compose

**Estado al 24/11/2026:** código de orquestación preparado, **todavía no validado conjuntamente en EC2**. FastAPI sí fue desplegada y probada por separado en AWS con un pronóstico HTTP 200. La integración de Dash con la API es trabajo pendiente de Karen.

## Archivos de infraestructura
- `compose.yaml`: API y tablero, red interna automática, healthchecks y arranque ordenado.
- `Dockerfile.api`: existente del primer PR; **no se modifica**.
- `Dockerfile.dash`: contenedor para el tablero original.
- `requirements_dash.txt`: dependencias del tablero, sin MLflow ni bibliotecas de entrenamiento.
- `.dockerignore`: evita empaquetar materiales locales y documentación innecesaria.

## Cómo funciona la conexión
`tablero` se conecta a `http://api:8001` mediante `ECO_API_URL`, **no a la IP pública de EC2**. Dentro de la red de Compose, `api` es el nombre DNS del servicio. Esto permite que cambiar la IP pública no afecte la conexión entre contenedores.

**Acción a completar por Karen:** su implementación de `tablero_ecovertis.py` debe leer `os.getenv("ECO_API_URL", "http://127.0.0.1:8001")` y consultar `POST /pronosticar` con `requests`, utilizando el contrato `CONTRATO_API_PARA_KAREN.md`. Mientras esa integración no exista, el tablero se iniciará con las predicciones del CSV de la segunda entrega.

## Preparación en Ubuntu / EC2
En la raíz del repositorio, con Docker Engine instalado:

```bash
sudo docker compose version
```

Si el subcomando no está disponible, **verificar primero** qué paquete Compose V2 ofrece Ubuntu; suele estar disponible mediante `sudo apt install docker-compose-v2`. No usar el antiguo `docker-compose` v1.

## Arranque de ambos contenedores

**Atención al primer despliegue:** en la EC2 actual ya existe un contenedor independiente llamado `ecovertis-api` creado con `docker run` y que ocupa el puerto 8001. **Antes** de ejecutar Compose, detenerlo y retirarlo (esto no elimina la imagen ni los modelos):

```bash
sudo docker stop ecovertis-api
sudo docker rm ecovertis-api
```

Si el contenedor anterior no existe, no hace falta ese paso.

```bash
sudo docker compose -f compose.yaml config
sudo docker compose -f compose.yaml up --build -d
sudo docker compose -f compose.yaml ps
```

Verificar desde la propia instancia:

```bash
curl -i http://127.0.0.1:8001/health
curl -I http://127.0.0.1:8050/
```

Diagnóstico de errores:

```bash
sudo docker compose -f compose.yaml logs --tail=100 api
sudo docker compose -f compose.yaml logs --tail=100 tablero
```

## Acceso desde el navegador
- API: `http://IP_PUBLICA_ACTUAL:8001/docs`
- Dash: `http://IP_PUBLICA_ACTUAL:8050/`

En EC2 habilitar temporalmente TCP 8050 en el grupo de seguridad si se requiere acceso externo. El puerto 8001 ya se utilizó en las pruebas previas. Abrir puertos públicos implica riesgos y HTTP no tiene cifrado; **es solo para pruebas académicas con datos simulados**. No dejar el puerto 22 abierto a todo internet fuera de las sesiones administrativas.

## Parada y continuación

```bash
sudo docker compose -f compose.yaml down
```

`down` detiene y elimina los contenedores, pero no borra las imágenes, código ni volúmenes persistentes. Para cumplir la guía, **detener la instancia EC2 desde AWS sin terminarla** al concluir las pruebas. La IP pública puede cambiar después de reiniciar.

## Pruebas pendientes antes de afirmar que está terminada
1. Construcción simultánea de los contenedores en EC2.
2. Navegación de Dash desde el puerto 8050.
3. Demostración del uso de la API por parte de Dash (no solo archivos CSV).
4. Pruebas de ingresos y OPEX, errores de conexión y validación de unidades COP/M COP.
5. Capturas para informe, presentación y video; actualización de documentos por ambos integrantes.

## Colaboración
Luis: cambios de Docker Compose e infraestructura en `feature/compose-final-luis`.
Karen: integración visual de Dash y manual de usuario en `feature/dash-api-karen` desde `master` actualizado. No atribuir commits que no hayan realizado efectivamente.
