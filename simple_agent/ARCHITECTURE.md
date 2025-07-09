# Arquitectura del SimpleAgent

Este documento describe la arquitectura del SimpleAgent basado en LangGraph y cómo cada componente funciona e interactúa con los demás.

## 1. Visión General

SimpleAgent implementa una arquitectura conversacional basada en grafos donde cada nodo representa una fase específica en el ciclo de procesamiento de conversaciones. Utiliza LangGraph para la gestión del flujo de estados y LangChain para la integración de herramientas especializadas.

### Flujo Básico

```mermaid
graph LR
    Usuario[Usuario] --> Entrada[Procesamiento\nde Entrada]
    Entrada --> Selección[Selección de\nHerramienta]
    Selección -->|Herramienta\nNecesaria| Ejecución[Ejecución de\nHerramienta]
    Selección -->|Sin Herramienta| Respuesta[Generación de\nRespuesta]
    Ejecución --> Respuesta
    Respuesta --> Usuario
    
    classDef usuario fill:#E1F5FE,stroke:#0288D1,stroke-width:2px;
    classDef proceso fill:#E8F5E9,stroke:#2E7D32,stroke-width:2px;
    classDef decision fill:#FFF3E0,stroke:#EF6C00,stroke-width:2px;
    
    class Usuario usuario;
    class Entrada,Ejecución,Respuesta proceso;
    class Selección decision;
```

## 2. Componentes Principales

### 2.1 Estado de Conversación `ConversationState`

El objeto de estado funciona como la memoria de trabajo para el agente, manteniendo toda la información relevante durante el ciclo de vida de la conversación.

```mermaid
classDiagram
    class ConversationState {
        + messages: List[BaseMessage]
        + context: Dict[str, Any]
        + tool_results: Dict[str, str]
        + next_step: str
    }
```

**Componentes del Estado:**
- **messages**: Historial completo de mensajes (humano y AI)
- **context**: Información contextual sobre la conversación actual
- **tool_results**: Resultados de las ejecuciones de herramientas
- **next_step**: Indicador del siguiente paso en el flujo de ejecución

### 2.2 Arquitectura del Grafo de Estados

El grafo de estados implementa la lógica de flujo principal del agente:

```mermaid
stateDiagram-v2
    [*] --> process_input
    process_input --> select_tool
    select_tool --> should_use_tool
    
    state should_use_tool <<choice>>
    should_use_tool --> execute_tool: true
    should_use_tool --> generate_response: false
    
    execute_tool --> generate_response
    generate_response --> [*]
```

### 2.3 Herramientas Especializadas

El agente utiliza herramientas modulares para realizar tareas específicas.

```mermaid
classDiagram
    BaseTool <|-- SimpleTool
    SimpleTool <|-- CompanyRankingTool
    SimpleTool <|-- DateTimeTool
    
    class BaseTool {
        +name: str
        +description: str
        +_run(input_value: str): str
        +_arun(input_value: str): str
    }
    
    class SimpleTool {
        +name: str
        +description: str
        +args_schema: Type[BaseModel]
        +_run(input_value: str): str
        +_arun(input_value: str): str
        +run(input_str: str): str
    }
    
    class CompanyRankingTool {
        +name: str = "company_ranking"
        +description: str
        +COMPANY_RANKINGS: Dict
        +run(input_str: str): str
        -_extract_ranking_type(text: str): str
        -_format_ranking_data(ranking_type: str, data: list): str
    }
    
    class DateTimeTool {
        +name: str = "datetime"
        +description: str
        +PERU_CITIES: Dict
        +INTERNATIONAL_TIMEZONES: Dict
        +PERU_HOLIDAYS: Dict
        +run(input_str: str): str
        -_get_current_datetime(): str
        -_get_holiday_info(): str
    }
```

### 2.4 Manejo de Solicitudes Múltiples

Una característica avanzada del SimpleAgent es la capacidad de procesar múltiples solicitudes en un solo mensaje:

```mermaid
graph TD
    Input[Mensaje Usuario] --> Detector[Detector de\nMúltiples Solicitudes]
    Detector -->|Múltiples| Split[División en\nSolicitudes Individuales]
    Detector -->|Individual| Normal[Procesamiento\nNormal]
    
    Split --> Process1[Procesar\nSolicitud 1]
    Split --> Process2[Procesar\nSolicitud 2]
    Split --> ProcessN[Procesar\nSolicitud N]
    
    Process1 --> Combine[Combinación de\nResultados]
    Process2 --> Combine
    ProcessN --> Combine
    
    Combine --> Response[Respuesta\nUnificada]
    Normal --> SingleResponse[Respuesta\nÚnica]
    
    classDef proceso fill:#E8F5E9,stroke:#2E7D32,stroke-width:2px;
    classDef decision fill:#FFF3E0,stroke:#EF6C00,stroke-width:2px;
    classDef respuesta fill:#E1F5FE,stroke:#0288D1,stroke-width:2px;
    
    class Input,Normal,Process1,Process2,ProcessN proceso;
    class Detector,Split decision;
    class Combine,Response,SingleResponse respuesta;
```

## 3. Flujo de Datos Detallado

### 3.1 Procesamiento de un Mensaje

```mermaid
sequenceDiagram
    participant Usuario
    participant ConversationalAgent as Agente
    participant StateGraph as Grafo
    participant Tools as Herramientas
    participant LLM
    
    Usuario->>Agente: Enviar mensaje
    Note over Agente: Verifica sesión
    
    Agente->>Grafo: Invocar workflow
    Note over Grafo: Inicializa estado
    
    Grafo->>Grafo: process_input
    Grafo->>Grafo: select_tool
    
    Grafo->>LLM: Consulta para selección
    LLM-->>Grafo: Herramienta seleccionada
    
    alt Se necesita herramienta
        Grafo->>Herramientas: execute_tool
        Herramientas-->>Grafo: Resultados
    end
    
    Grafo->>LLM: Generar respuesta
    LLM-->>Grafo: Respuesta generada
    
    Grafo-->>Agente: Estado final
    Agente-->>Usuario: Respuesta
```

### 3.2 Proceso de Detección de Intenciones

El agente utiliza un sistema de detección en capas para identificar con precisión las intenciones del usuario:

```mermaid
graph TD
    Input[Mensaje del Usuario] --> PreCheck[Verificación de\nPatrones Directos]
    PreCheck -->|Coincidencia| DirectTool[Selección Directa\nde Herramienta]
    PreCheck -->|Sin coincidencia| LLM[Consulta al LLM]
    
    LLM --> ToolAnalysis[Análisis de\nNecesidad]
    ToolAnalysis -->|Necesaria| SelectTool[Selección de\nHerramienta]
    ToolAnalysis -->|No necesaria| NoTool[Sin Herramienta]
    
    DirectTool --> ExecTool[Ejecución de\nHerramienta]
    SelectTool --> ExecTool
    
    classDef entrada fill:#E3F2FD,stroke:#1565C0,stroke-width:2px;
    classDef proceso fill:#E8F5E9,stroke:#2E7D32,stroke-width:2px;
    classDef decision fill:#FFF3E0,stroke:#EF6C00,stroke-width:2px;
    classDef accion fill:#F3E5F5,stroke:#7B1FA2,stroke-width:2px;
    
    class Input entrada;
    class PreCheck,LLM,ToolAnalysis proceso;
    class DirectTool,SelectTool,NoTool decision;
    class ExecTool accion;
```

## 4. Interacción entre Componentes

El siguiente diagrama ilustra cómo los componentes interactúan durante una conversación completa:

```mermaid
graph TB
    subgraph "Interfaz de Usuario"
        UI[Streamlit UI]
        Input[Input del Usuario]
        Output[Respuesta]
    end
    
    subgraph "Motor del Agente"
        Agent[ConversationalAgent]
        Workflow[StateGraph]
        Memory[Memoria/Checkpointing]
    end
    
    subgraph "Herramientas"
        CompanyTool[CompanyRankingTool]
        DateTool[DateTimeTool]
    end
    
    subgraph "LLM"
        GeminiLLM[Gemini LLM]
    end
    
    Input -->|Mensaje| UI
    UI -->|process_message| Agent
    
    Agent -->|invoke| Workflow
    Workflow -->|checkpoint| Memory
    Memory -->|recuperar estado| Workflow
    
    Workflow -->|select_tool| GeminiLLM
    GeminiLLM -->|decisión| Workflow
    
    Workflow -->|execute_tool| CompanyTool
    Workflow -->|execute_tool| DateTool
    CompanyTool -->|resultados| Workflow
    DateTool -->|resultados| Workflow
    
    Workflow -->|generate_response| GeminiLLM
    GeminiLLM -->|respuesta| Workflow
    
    Workflow -->|estado final| Agent
    Agent -->|respuesta| UI
    UI -->|mostrar| Output
    
    classDef ui fill:#BBDEFB,stroke:#1976D2,stroke-width:2px;
    classDef agent fill:#C8E6C9,stroke:#388E3C,stroke-width:2px;
    classDef tools fill:#FFE0B2,stroke:#F57C00,stroke-width:2px;
    classDef llm fill:#E1BEE7,stroke:#8E24AA,stroke-width:2px;
    
    class UI,Input,Output ui;
    class Agent,Workflow,Memory agent;
    class CompanyTool,DateTool tools;
    class GeminiLLM llm;
```

## 5. Arquitectura de Sesiones y Memoria

El agente mantiene un contexto para cada sesión de usuario:

```mermaid
graph LR
    subgraph "Gestión de Sesiones"
        Sessions[Conversation\nContexts]
        SessionA[Session A]
        SessionB[Session B]
        SessionC[Session C]
        
        Sessions --> SessionA
        Sessions --> SessionB
        Sessions --> SessionC
    end
    
    subgraph "Memoria por Sesión"
        SessionA --> HistoryA[Historial\nMensajes A]
        SessionB --> HistoryB[Historial\nMensajes B]
        SessionC --> HistoryC[Historial\nMensajes C]
    end
    
    subgraph "Checkpoint"
        CheckpointA[Checkpoint A]
        CheckpointB[Checkpoint B]
        CheckpointC[Checkpoint C]
        
        HistoryA -.-> CheckpointA
        HistoryB -.-> CheckpointB
        HistoryC -.-> CheckpointC
    end
    
    classDef session fill:#E8EAF6,stroke:#3949AB,stroke-width:2px;
    classDef history fill:#FFF9C4,stroke:#FBC02D,stroke-width:2px;
    classDef checkpoint fill:#FFCCBC,stroke:#E64A19,stroke-width:2px;
    
    class Sessions,SessionA,SessionB,SessionC session;
    class HistoryA,HistoryB,HistoryC history;
    class CheckpointA,CheckpointB,CheckpointC checkpoint;
```

## 6. Extensibilidad

La arquitectura de SimpleAgent está diseñada para ser altamente extensible:

```mermaid
graph TD
    Core[Núcleo del Agente]
    
    Core --> Tools[Herramientas]
    Core --> Nodes[Nodos de Grafo]
    Core --> State[Modelo de Estado]
    Core --> UI[Interfaces]
    
    Tools --> T1[Herramientas\nExistentes]
    Tools --> T2[Nuevas\nHerramientas]
    
    Nodes --> N1[Nodos\nExistentes]
    Nodes --> N2[Nuevos\nNodos]
    
    State --> S1[Campos\nExistentes]
    State --> S2[Nuevos\nCampos]
    
    UI --> U1[Streamlit]
    UI --> U2[Otras\nInterfaces]
    
    classDef core fill:#D1C4E9,stroke:#512DA8,stroke-width:2px;
    classDef modulo fill:#C5CAE9,stroke:#303F9F,stroke-width:2px;
    classDef comp fill:#DCEDC8,stroke:#689F38,stroke-width:2px;
    
    class Core core;
    class Tools,Nodes,State,UI modulo;
    class T1,T2,N1,N2,S1,S2,U1,U2 comp;
```

## 7. Consideraciones para Desarrollo Futuro

### 7.1 Mejoras Potenciales

- **Razonamiento en Cadena (Chain-of-Thought)**: Implementar nodos adicionales para razonamiento paso a paso en consultas complejas.
- **Recuperación de Conocimiento**: Integrar bases de conocimiento externas para mejorar la precisión de las respuestas.
- **Aprendizaje Continuo**: Mecanismos para actualizar y refinar las capacidades del agente basándose en interacciones pasadas.
- **Personalización**: Adaptación del comportamiento del agente según preferencias del usuario.
- **Herramientas Adicionales**: Expandir el conjunto de herramientas para cubrir más dominios.

### 7.2 Arquitectura Futura Propuesta

```mermaid
graph TB
    subgraph "Arquitectura Extendida"
        Core[Núcleo LangGraph]
        
        subgraph "Módulos Cognitivos"
            Reasoning[Razonamiento]
            Planning[Planificación]
            Memory[Memoria a Largo Plazo]
        end
        
        subgraph "Fuentes de Conocimiento"
            VectorDB[Base de Datos Vectorial]
            ExternalAPI[APIs Externas]
            KnowledgeBase[Base de Conocimiento]
        end
        
        subgraph "Herramientas Expandidas"
            FinanceTool[Finanzas]
            NewsTool[Noticias]
            AnalyticsTool[Analítica]
            ExistingTools[Herramientas Actuales]
        end
        
        Core --> Reasoning
        Core --> Planning
        Core --> Memory
        
        Reasoning --> VectorDB
        Planning --> ExternalAPI
        Memory --> KnowledgeBase
        
        VectorDB --> FinanceTool
        ExternalAPI --> NewsTool
        KnowledgeBase --> AnalyticsTool
        KnowledgeBase --> ExistingTools
    end
    
    classDef core fill:#E1BEE7,stroke:#8E24AA,stroke-width:2px;
    classDef modulos fill:#BBDEFB,stroke:#1976D2,stroke-width:2px;
    classDef conocimiento fill:#FFE0B2,stroke:#F57C00,stroke-width:2px;
    classDef herramientas fill:#C8E6C9,stroke:#388E3C,stroke-width:2px;
    
    class Core core;
    class Reasoning,Planning,Memory modulos;
    class VectorDB,ExternalAPI,KnowledgeBase conocimiento;
    class FinanceTool,NewsTool,AnalyticsTool,ExistingTools herramientas;
```