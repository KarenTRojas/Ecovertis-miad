# Ecovertis · Manual de instalación y despliegue — borrador verificable
**Autor de la sección de infraestructura:** Luis Enrique Martínez Mendoza  
**Estado:** API FastAPI verificada en EC2 + Docker. Integración Dash/Compose aún pendiente.

## 1. Arquitectura
- Fuente: repositorio `KarenTRojas/Ecovertis-miad`.
- API: FastAPI con cuatro modelos `.joblib` (Ridge/Random Forest para ingresos y OPEX ajustado); endpoint HTTP `/pronosticar`.
- Tablero: Dash. Integración HTTP con API por variable de entorno `ECO_API_URL` (pendiente de validación conjunta).
- EC2: `Ecovertis_Entrega_Final`, Ubuntu Server 24.04.5 LTS, t2.medium (2 vCPU, 4 GiB), 29 GB aprox., us-east-1. La IP pública puede cambiar tras reiniciar la instancia.
- Imagen de API: Dockerfile.api, imagen `ecovertis-api:v1`, contenedor `ecovertis-api`, puerto 8001.

## 2. Requisitos
Servidor Linux x86_64, Git, Docker Engine y una instancia con capacidad suficiente. En el servidor de pruebas se verificó Docker Engine 29.1.3 con `hello-world` y 3,4 GiB de memoria disponibles antes del despliegue.

## 3. Obtener el código
Usar una revisión integrada y comprobada en GitHub; durante la construcción inicial se trabajó en `feature/api-docker-luis`:

```bash
git clone --branch feature/api-docker-luis --single-branch https://github.com/KarenTRojas/Ecovertis-miad.git
cd Ecovertis-miad
ls -lh modelos_guardados/
ls -lh resultados/analisis_mensual_parques.csv
```

El repositorio debe incluir los cuatro modelos `.joblib` y el CSV de análisis mensual. El archivo Excel original está versionado mediante DVC y su recuperación puede requerir la fuente o la caché; **la API de inferencia utiliza el CSV**.

## 4. Construir y ejecutar FastAPI
```bash
sudo docker build -f Dockerfile.api -t ecovertis-api:v1 .
sudo docker run -d --name ecovertis-api --restart unless-stopped -p 8001:8001 ecovertis-api:v1
sudo docker ps
curl -i http://127.0.0.1:8001/health
```
Respuesta esperada al diagnóstico:
```json
{"estado":"ok","modelos":4,"datos":"disponibles"}
```

Consultar `/docs` por HTTP en la IP pública vigente de EC2. Debe verificarse `POST /pronosticar` con una solicitud real antes de dar el servicio por aprobado.

## 5. Evidencia técnica ya conseguida
Se comprobó desde el navegador externo `POST /pronosticar` para Acacías, ingresos, Random Forest con HTTP 200. Valores en COP:
- Octubre 2026: 2.307.288.349,46
- Noviembre 2026: 2.165.004.246,45
- Diciembre 2026: 2.170.453.853,73

Estos valores son exploratorios y resultan de predicción recursiva, no presupuestos autorizados ni pronósticos por proyecto.

## 6. Redes y seguridad
En el laboratorio se abrió temporalmente TCP 8001 para comprobar conectividad externa. No dejar SSH 22 accesible a `0.0.0.0/0` fuera de una sesión de administración: restringir o cerrar la regla cuando no se use. El HTTP de pruebas no cifra tráfico; no publicar datos privados ni tratarlo como despliegue de producción. La instancia no tiene dominio ni HTTPS configurado.

## 7. Pendientes que deben completar la versión final
- Integración de Dash con la API y pruebas con interfaz.
- Empaquetamiento de Dash y orquestación de ambos servicios (Compose si está disponible en EC2).
- Puerto externo 8050 y su regla temporal de seguridad.
- Capturas de integración funcional, guía de usuario y video.
- Confirmar requisitos exactos de cada imagen y registrar el commit/revisión desplegado.

## 8. Detención sin pérdida de recursos
La guía académica pide **dejar la instancia detenida, no terminada**. Desde EC2: Instancias > seleccionar `Ecovertis_Entrega_Final` > Estado de la instancia > Detener instancia. Al reanudar, comprobar nueva IP pública. El disco EBS y las imágenes locales Docker permanecen, salvo acciones explícitas de borrado; el contenedor se configuró con `--restart unless-stopped`.

No borrar el repositorio, ni los modelos, ni el volumen EBS. Los recursos detenidos aún pueden generar algunos cargos (por ejemplo, almacenamiento).
