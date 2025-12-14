# Callan Monitor Script

## Descripción
Script en Python para el diagnóstico automático de CDUs (Callans) mediante SSH.
Verifica el estado de salud del equipo mediante la consulta directa de sensores
usando command line (CLI) y genera un reporte en texto con
fecha y hora.

## Características
- Conexión SSH automatizada
- Lectura de sensores de temperatura
- Verificación de estado de salud
- Generación de reportes en formato TXT
- Manejo de credenciales mediante variables de entorno
- JSONs para lista de IPs, escalable a múltiples equipos
