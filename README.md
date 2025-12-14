# Cdu Monitor

Script en Python para el monitoreo de CDUs (Cooling Distribution Units) mediante SSH, consultando
estado de salud y temperaturas de sensores a través de command line.

## Qué hace
- Se conecta vía SSH a múltiples CDUs
- Verifica el estado de salud del equipo
- Consulta sensores de temperatura usando CLI
- Genera reportes en formato TXT con fecha y hora

## Uso
1. Definir las credenciales SSH como variables de entorno
2. Configurar el inventario de IPs en el archivo JSON

## Requisitos
- Python 3
- paramiko


## Notas
Este script fue diseñado para ejecutarse en una red privada
desde computadoras virtuales con acceso directo a la infraestructura.
