# SimpleAgent - Asistente Virtual Empresarial 🤖

SimpleAgent es un asistente conversacional inteligente especializado en información empresarial y temporal. Desarrollado con LangGraph y LangChain, este agente utiliza modelos avanzados de Gemini para proporcionar respuestas precisas y contextuales a consultas sobre rankings empresariales, fechas, horas y zonas horarias.

## 🚀 Características Principales

- **Motor Conversacional Avanzado**: Utiliza LangGraph para gestionar flujos complejos de conversación con estado y memoria.
- **Detección Inteligente de Intenciones**: Identifica automáticamente cuándo usar herramientas específicas basado en el contexto de la consulta.
- **Procesamiento de Solicitudes Múltiples**: Capacidad para detectar y responder a varias solicitudes en un solo mensaje.
- **Herramientas Especializadas**:
  - 📊 **Company Ranking**: Proporciona datos sobre empresas top por inversión, ingresos, valor de mercado y empleados.
  - 📅 **DateTime**: Ofrece información precisa sobre fechas, horas, zonas horarias y días festivos.
- **Interfaz Web Intuitiva**: Implementada con Streamlit, ofrece una experiencia de chat fluida y atractiva.

## 📋 Estructura del Proyecto

```
simple_agent/
├── agent/
│   ├── conversation.py     # Lógica principal del agente conversacional
│   └── state.py            # Definición del estado de conversación
├── tools/
│   ├── base.py             # Clase base para herramientas
│   ├── company_ranking.py  # Herramienta para rankings empresariales
│   └── datetime_tool.py    # Herramienta para información temporal
├── utils/
│   └── prompts.py          # Prompts del sistema para el agente
└── app.py                  # Aplicación Streamlit para la interfaz de usuario
```

## 🛠️ Tecnologías Utilizadas

- **LangGraph**: Para la creación de flujos de estado en conversaciones complejas
- **LangChain**: Framework para aplicaciones basadas en LLMs
- **Google Vertex AI (Gemini)**: Modelo de lenguaje avanzado
- **Streamlit**: Framework para la interfaz de usuario web
- **Python**: Lenguaje de programación principal

## 🔧 Instalación y Configuración

### Prerrequisitos

- Python 3.8+
- Cuenta en Google Cloud con acceso a Vertex AI

### Instalación

1. Clona el repositorio:
   ```bash
   git clone ttps://github.com/JSandovalCH/LanggraphTraining.git
   cd simple_agent
   ```

2. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
   ```

3. Configura las variables de entorno:
   Crea un archivo `.env` en la raíz del proyecto con:
   ```
   PROJECT_ID=tu-proyecto-gcp
   REGION=tu-region-gcp
   ```

### Ejecución

Inicia la aplicación con:

```bash
streamlit run app.py
```

## 🧠 Cómo Funciona

### Flujo de Conversación

1. **Procesamiento de Entrada**: El agente recibe el mensaje del usuario y analiza su contenido.
2. **Selección de Herramienta**: Determina si debe utilizar alguna herramienta específica.
3. **Ejecución de Herramienta**: Si es necesario, ejecuta la herramienta seleccionada.
4. **Generación de Respuesta**: Genera una respuesta basada en el contexto y los resultados de las herramientas.

### Manejo de Solicitudes Múltiples

El agente puede identificar cuando un usuario solicita varios tipos de información en un solo mensaje (ej. "Dame el ranking de empresas por inversión y también la hora actual en Madrid").

### Memoria y Contexto

Mantiene el contexto de la conversación por sesión, permitiendo referencias a mensajes anteriores.

## 📝 Ejemplo de Uso

```
Usuario: ¿Qué empresas tienen mayor inversión en Perú?

Asistente: 
TOP 5 EMPRESAS PERUANAS POR INVERSIÓN:

1. Grupo Romero
   Inversión estimada: USD 1,250 millones
   Sector: Diversificado

2. Grupo Breca
   Inversión estimada: USD 980 millones
   Sector: Minería/Banca

[...]

Usuario: ¿Podrías decirme qué día es hoy y también los próximos feriados?

Asistente:
Fecha: Domingo 13 de abril de 2025
Hora: 15:30:45 (UTC-5, hora de Perú)

Próximos días festivos:
1. Día del Trabajo - 01 de mayo (en 18 días)
2. Día de San Pedro y San Pablo - 29 de junio (en 77 días)
[...]
```

## 🔍 Capacidades de Detección

El agente utiliza patrones sofisticados para detectar intenciones:

- **Rankings Empresariales**: Identifica menciones de "empresas", "ranking", "inversión", "ingresos", etc.
- **Consultas Temporales**: Reconoce referencias a "fecha", "hora", "feriado", "zona horaria", etc.

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor, sigue estos pasos:

1. Haz fork del proyecto
2. Crea una rama para tu funcionalidad (`git checkout -b feature/amazing-feature`)
3. Realiza tus cambios
4. Haz commit de tus cambios (`git commit -m 'Add some amazing feature'`)
5. Empuja a la rama (`git push origin feature/amazing-feature`)
6. Abre un Pull Request

## 📄 Licencia

Este proyecto está licenciado bajo [especificar licencia] - ver el archivo LICENSE.md para más detalles.

## 📞 Contacto

Joshua Sandoval - [jssandoval.ch@gmail.com]

URL del Proyecto: [https://github.com/JSandovalCH/LanggraphTraining/simple_agent](https://github.com/JSandovalCH/LanggraphTraining/simple_agent)
