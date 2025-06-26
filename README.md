# Bot Asistente Universitario UGD

Este es un chatbot desarrollado con Rasa para la Universidad Gastón Dachary (UGD) que proporciona información académica y asistencia a estudiantes y futuros alumnos.

## 🎯 Funcionalidades

El bot puede responder consultas sobre:

- **Inscripciones**: Requisitos, plazos, modalidades
- **Cursos de ingreso**: Información sobre cursos nivelatorios
- **Asistencia**: Régimen de asistencia obligatoria
- **Exámenes**: Mesas de examen, recuperatorios, equivalencias
- **Becas**: Sistema de becas y becas por hermanos
- **Servicios**: Biblioteca, laboratorios, deportes
- **Equipamiento tecnológico**: Laboratorios informáticos y telecomunicaciones
- **Intercambios**: Convenios con universidades extranjeras
- **Contactos**: Información de contacto de las sedes
- **Consultas académicas**: Materias cursadas, mesas de examen específicas

## 🛠️ Tecnologías Utilizadas

- **Rasa 3.6.20**: Framework de chatbot
- **Python 3.9**: Lenguaje de programación
- **Supabase**: Base de datos en la nube
- **Docker & Docker Compose**: Containerización
- **httpx**: Cliente HTTP para integraciones

## 📋 Prerrequisitos

- Python 3.9 o superior
- Docker y Docker Compose
- Cuenta en Supabase (para la base de datos)

## 🚀 Instalación y Configuración

### Opción 1: Usando Docker (Recomendado)

1. **Clonar el repositorio**
   ```bash
   git clone <url-del-repositorio>
   cd nuevoBotTesis
   ```

2. **Configurar variables de entorno**
   Crear un archivo `.env` en la raíz del proyecto:
   ```env
   SUPABASE_URL=tu_url_de_supabase
   SUPABASE_KEY=tu_clave_de_supabase
   ```

3. **Levantar los servicios con Docker Compose**
   ```bash
   docker-compose up --build
   ```

   Esto iniciará:
   - **Rasa Server**: En el puerto 5005
   - **Rasa Actions Server**: En el puerto 5055

### Opción 2: Instalación Local

1. **Crear entorno virtual**
   ```bash
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   ```

2. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt
   cd actions
   pip install -r requirements.txt
   cd ..
   ```

3. **Configurar variables de entorno**
   Crear archivo `.env` como se mencionó anteriormente.

4. **Entrenar el modelo**
   ```bash
   rasa train
   ```

5. **Iniciar los servicios**
   
   En una terminal (Rasa Server):
   ```bash
   rasa run --enable-api --cors "*" --port 5005
   ```
   
   En otra terminal (Actions Server):
   ```bash
   cd actions
   python -m rasa_sdk --actions actions --port 5055
   ```

## 🧪 Cómo Probar el Bot

### 1. Usando la API REST

Una vez que los servicios estén corriendo, puedes hacer peticiones POST a la API:

```bash
curl -X POST http://localhost:5005/webhooks/rest/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "sender": "test_user",
    "message": "Hola, ¿cómo estás?"
  }'
```

### 2. Usando el Shell de Rasa

```bash
rasa shell
```

### 3. Usando el Endpoint de Pruebas

```bash
rasa test
```

### 4. Interfaz Web (Opcional)

Para una interfaz web más amigable, puedes usar herramientas como:
- **Rasa Chat Widget**
- **Botfront**
- **Rasa X** (versión community)

## 📁 Estructura del Proyecto

```
nuevoBotTesis/
├── actions/                 # Acciones personalizadas
│   ├── actions.py          # Lógica de acciones
│   ├── requirements.txt    # Dependencias de acciones
│   └── Dockerfile         # Docker para acciones
├── data/                   # Datos de entrenamiento
│   ├── nlu.yml            # Datos de entrenamiento NLU
│   ├── stories.yml        # Historias de conversación
│   └── rules.yml          # Reglas de conversación
├── models/                 # Modelos entrenados
├── tests/                  # Tests del bot
├── results/                # Resultados de evaluación
├── .rasa/                  # Configuración de Rasa
├── config.yml             # Configuración del pipeline
├── credentials.yml        # Credenciales de servicios
├── domain.yml             # Dominio del bot
├── endpoints.yml          # Configuración de endpoints
├── requirements.txt       # Dependencias principales
├── Dockerfile            # Docker principal
├── docker-compose.yml    # Orquestación de servicios
└── README.md             # Este archivo
```

## 🔧 Configuración de Supabase

El bot utiliza Supabase para:
- Consultar materias cursadas por matrícula
- Obtener información de mesas de examen
- Gestionar inscripciones a exámenes

### Tablas requeridas en Supabase:
- `MateriaCursada`: Materias cursadas por estudiantes
- `MesaExamen`: Mesas de examen disponibles
- `Materia`: Catálogo de materias

## 🚨 Solución de Problemas

### Error de conexión a Supabase
- Verificar que las variables `SUPABASE_URL` y `SUPABASE_KEY` estén correctamente configuradas
- Comprobar que la base de datos esté accesible

### Error de puertos ocupados
- Cambiar los puertos en `docker-compose.yml` si 5005 o 5055 están ocupados
- Verificar que no haya otros servicios de Rasa corriendo

### Error de entrenamiento
- Verificar que todos los archivos YAML estén correctamente formateados
- Comprobar que no haya errores de sintaxis en `domain.yml`

## 📊 Monitoreo y Logs

Los logs se pueden ver con:
```bash
# Para Docker
docker-compose logs -f

# Para instalación local
# Los logs aparecen en la consola donde ejecutaste los comandos
```

## 🤝 Contribución

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📝 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## 📞 Contacto

Para consultas sobre el bot o problemas técnicos, contactar al equipo de desarrollo de la UGD.

---

**Nota**: Este bot está diseñado específicamente para la Universidad Gastón Dachary y sus procesos académicos. Para adaptarlo a otra institución, se requerirán modificaciones en el dominio, datos de entrenamiento y acciones personalizadas.