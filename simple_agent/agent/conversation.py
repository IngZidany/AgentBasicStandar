from typing import List, Dict, Any, Optional
import logging
import re
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from .state import ConversationState, create_initial_state
from utils.prompts import SYSTEM_PROMPT

# Configurar logging básico
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ConversationalAgent:
    """
    Agente conversacional mejorado con LangGraph y memoria.
    """
    
    def __init__(self, 
                 project_id: str = None,
                 location: str = None,
                 tools: List = None,
                 model_name: str = "gemini-1.5-pro"):
        """
        Inicializa el agente conversacional.
        """
        self.project_id = project_id
        self.location = location
        self.tools = tools or []
        
        # Inicializar el modelo LLM
        self.llm = init_chat_model(
            model_name, 
            model_provider="google_vertexai",
            temperature=0.2
        )
        
        # Inicializar memoria
        self.memory = MemorySaver()
        
        # Crear y compilar el grafo de estados
        self.workflow = self._create_workflow()
        logger.info(f"Agente inicializado con {len(self.tools)} herramientas")
        
        # Diccionario para almacenar el contexto de la conversación por sesión
        self.conversation_contexts = {}
        
    def process_message(self, message: str, session_id: str = "default") -> str:
        """
        Procesa un mensaje del usuario y devuelve una respuesta, manteniendo
        el contexto de la conversación para cada sesión.
        """
        try:
            # Configuración para el checkpointer
            config = {"configurable": {"thread_id": session_id}}
            
            # Crear o recuperar el historial de mensajes para esta sesión
            if session_id not in self.conversation_contexts:
                self.conversation_contexts[session_id] = []
            
            # Añadir el nuevo mensaje a la lista
            human_msg = HumanMessage(content=message)
            
            # Pre-análisis para detectar solicitudes múltiples
            multi_requests = self._detect_multiple_requests(message)
            if multi_requests:
                logger.info(f"Detectadas múltiples solicitudes: {multi_requests}")
                # Procesar cada solicitud por separado y combinar resultados
                results = self._process_multiple_requests(multi_requests, session_id)
                return results
            
            # Construir el input con el historial actualizado
            state_input = {
                "messages": [human_msg]
            }
            
            # Ejecutar el workflow con checkpointing
            final_state = self.workflow.invoke(state_input, config)
            
            # Extraer la respuesta del agente
            messages = final_state.get("messages", [])
            
            # Obtener el último mensaje del agente
            for msg in reversed(messages):
                if isinstance(msg, AIMessage):
                    # Guardar el mensaje en el contexto
                    self.conversation_contexts[session_id].append(human_msg)
                    self.conversation_contexts[session_id].append(msg)
                    return msg.content
            
            # Si no hay respuesta del agente
            return "Lo siento, no pude procesar tu mensaje."
            
        except Exception as e:
            logger.error(f"Error al procesar mensaje: {str(e)}")
            return f"Lo siento, ocurrió un error: {str(e)}"
    
    def _detect_multiple_requests(self, message: str) -> List[str]:
        """
        Detecta si el mensaje contiene múltiples solicitudes separadas.
        Retorna una lista de solicitudes si las encuentra, o una lista vacía si no.
        """
        # Patrones para detectar solicitudes múltiples
        patterns = [
            # "quiero saber X y también Y"
            r'(quiero|necesito|me gustaría) (?:saber|conocer|ver) (?:sobre)? (el|la|los|las) (.+?) (?:y también|y|además) (?:sobre)? (el|la|los|las) (.+)',
            # "me interesan X, Y, y Z"
            r'me (?:interesa|interesan) (?:.*?)(,|y| tanto| dos:?) (.+)',
            # "dame información de X y Y"
            r'(?:dame|proporciona|muestra) (?:información|datos|detalles) (?:de|sobre|acerca de) (.+?) (?:y|,) (.+)'
        ]
        
        # Buscar coincidencias en el mensaje
        for pattern in patterns:
            if re.search(pattern, message, re.IGNORECASE):
                # Analizar más a fondo para extraer solicitudes específicas
                return self._extract_specific_requests(message)
        
        # Si no se detecta un patrón claro de múltiples solicitudes
        return []
    
    def _extract_specific_requests(self, message: str) -> List[str]:
        """
        Extrae solicitudes específicas del mensaje del usuario.
        """
        # Palabras clave para categorías comunes
        categories = {
            "rankings": ["ranking", "empresas", "inversión", "ingresos", "valor", "mercado", "empleados"],
            "datetime": ["fecha", "hora", "día", "festivo", "feriado", "zona horaria"]
        }
        
        # Lista para almacenar solicitudes identificadas
        requests = []
        
        # Verificar si hay mención de rankings
        if any(keyword in message.lower() for keyword in categories["rankings"]):
            # Buscar tipos específicos de rankings
            ranking_types = ["inversión", "ingresos", "valor de mercado", "empleados"]
            for r_type in ranking_types:
                if r_type in message.lower() or self._has_synonym(message.lower(), r_type):
                    requests.append(f"ranking por {r_type}")
        
        # Verificar si hay mención de fecha/hora
        if any(keyword in message.lower() for keyword in categories["datetime"]):
            if "festivo" in message.lower() or "feriado" in message.lower():
                requests.append("días festivos")
            if "fecha" in message.lower() or "día" in message.lower() or "hoy" in message.lower():
                requests.append("fecha actual")
            if "hora" in message.lower():
                requests.append("hora actual")
        
        return requests
    
    def _has_synonym(self, text: str, concept: str) -> bool:
        """
        Verifica si el texto contiene algún sinónimo del concepto.
        """
        synonyms = {
            "inversión": ["invertir", "invierte", "invierten", "inversiones", "capital"],
            "ingresos": ["ingreso", "ganancias", "facturación", "ventas", "beneficios"],
            "valor de mercado": ["valor", "capitalización", "bolsa", "mercado", "acciones"],
            "empleados": ["empleado", "trabajadores", "trabajador", "personal", "plantilla"]
        }
        
        if concept in synonyms:
            return any(syn in text for syn in synonyms[concept])
        return False
    
    def _process_multiple_requests(self, requests: List[str], session_id: str) -> str:
        """
        Procesa múltiples solicitudes y combina los resultados en una sola respuesta.
        """
        results = {}
        
        for request in requests:
            logger.info(f"Procesando solicitud individual: {request}")
            
            # Preparar mensaje adaptado para cada solicitud
            if "ranking" in request:
                # Extraer el tipo de ranking
                r_type = request.replace("ranking por ", "")
                message = f"dame el ranking de empresas por {r_type}"
                
                # Forzar el uso de la herramienta company_ranking
                tool_results = self._force_tool_execution("company_ranking", message)
                results[request] = tool_results
                
            elif "festivo" in request or "feriado" in request:
                message = "dime los próximos días festivos"
                
                # Forzar el uso de la herramienta datetime
                tool_results = self._force_tool_execution("datetime", message)
                results[request] = tool_results
                
            elif "fecha" in request:
                message = "qué fecha es hoy"
                
                # Forzar el uso de la herramienta datetime
                tool_results = self._force_tool_execution("datetime", message)
                results[request] = tool_results
                
            elif "hora" in request:
                message = "qué hora es ahora"
                
                # Forzar el uso de la herramienta datetime
                tool_results = self._force_tool_execution("datetime", message)
                results[request] = tool_results
        
        # Combinar resultados en una sola respuesta
        response = self._generate_combined_response(results)
        return response
    
    def _force_tool_execution(self, tool_name: str, query: str) -> str:
        """
        Fuerza la ejecución de una herramienta específica.
        """
        try:
            # Buscar la herramienta por nombre
            tool = next((t for t in self.tools if t.name.lower() == tool_name.lower()), None)
            
            if tool:
                logger.info(f"Forzando ejecución de herramienta: {tool_name}")
                result = tool.run(query)
                logger.info(f"Resultado obtenido de la herramienta {tool_name}")
                return result
            else:
                logger.warning(f"Herramienta no encontrada: {tool_name}")
                return f"No se encontró la herramienta {tool_name}"
                
        except Exception as e:
            logger.error(f"Error ejecutando herramienta {tool_name}: {str(e)}")
            return f"Error al ejecutar la herramienta {tool_name}: {str(e)}"
    
    def _generate_combined_response(self, results: Dict[str, str]) -> str:
        """
        Genera una respuesta combinada basada en los resultados de múltiples solicitudes.
        """
        # Construir un prompt para el LLM para generar una respuesta combinada
        prompt = f"""{SYSTEM_PROMPT}

El usuario ha solicitado múltiples tipos de información. He obtenido los siguientes resultados:

"""
        
        for request, result in results.items():
            prompt += f"--- Información sobre {request} ---\n{result}\n\n"
        
        prompt += """
Por favor, genera una respuesta única que combine todos estos resultados de manera coherente y natural.
La respuesta debe fluir bien y no parecer simplemente una lista de resultados pegados juntos.
"""
        
        # Generar respuesta con el LLM
        response = self.llm.invoke(prompt)
        return response.content
    
    def _create_workflow(self) -> StateGraph:
        """
        Crea el grafo de estados para el agente.
        """
        # Crear el grafo con el tipo de estado definido
        workflow = StateGraph(ConversationState)
        
        # Añadir nodos al grafo
        workflow.add_node("process_input", self._process_input)
        workflow.add_node("select_tool", self._select_tool)
        workflow.add_node("execute_tool", self._execute_tool)
        workflow.add_node("generate_response", self._generate_response)
        
        # Definir el flujo entre nodos
        workflow.add_edge("process_input", "select_tool")
        
        # Añadir rutas condicionales
        workflow.add_conditional_edges(
            "select_tool",
            self._should_use_tool,
            {
                True: "execute_tool",
                False: "generate_response"
            }
        )
        
        workflow.add_edge("execute_tool", "generate_response")
        workflow.add_edge("generate_response", END)
        
        # Definir el punto de entrada
        workflow.set_entry_point("process_input")
        
        # Compilar con checkpointing para memoria
        return workflow.compile(checkpointer=self.memory)
    
    def _process_input(self, state: ConversationState) -> ConversationState:
        """
        Procesa la entrada del usuario.
        """
        # Asegurarse de que el estado tenga un contexto inicializado
        if "context" not in state:
            state["context"] = {}
            
        return {
            **state,
            "next_step": "select_tool"
        }
    
    def _select_tool(self, state: ConversationState) -> ConversationState:
        """
        Determina si se debe usar una herramienta y cuál.
        """
        try:
            messages = state["messages"]
            
            # Asegurarse de que el estado tenga un contexto inicializado
            if "context" not in state:
                state = {**state, "context": {}}
                
            if not messages:
                return {**state, "next_step": "generate_response"}
                
            # Obtener el último mensaje del usuario
            last_message = messages[-1].content
            
            # Pre-verificar si el mensaje contiene palabras clave específicas de herramientas
            # Esto ayuda a forzar el uso de herramientas cuando el LLM podría no detectarlas
            tool_to_use = self._pre_check_tools(last_message)
            if tool_to_use:
                logger.info(f"Pre-detección directa de herramienta: {tool_to_use}")
                # Actualizar el contexto con la herramienta seleccionada directamente
                context = state.get("context", {})
                updated_context = {**context, "selected_tool": tool_to_use}
                return {
                    **state,
                    "context": updated_context,
                    "next_step": "execute_tool"
                }
            
            # Si no se pre-detectó una herramienta, continuar con el flujo normal
            # Lista de herramientas disponibles
            tool_descriptions = [f"{tool.name}: {tool.description}" for tool in self.tools]
            
            # Preparar el prompt para determinar si usar una herramienta
            tool_selection_prompt = f"""
            El usuario ha dicho: "{last_message}"
            
            Herramientas disponibles:
            {chr(10).join(tool_descriptions)}
            
            ¿Se debe usar alguna herramienta para responder? Si es así, ¿cuál?
            Responde exactamente con el nombre de la herramienta o "ninguna" si no se necesita ninguna.
            
            RECUERDA:
            - Si el usuario menciona cualquier palabra relacionada con fechas, horas, o días festivos, debes usar la herramienta "datetime".
            - Si el usuario menciona cualquier palabra relacionada con empresas, rankings, inversión, ingresos, o empleados, debes usar la herramienta "company_ranking".
            - NO respondas "ninguna" a menos que estés 100% seguro de que ninguna herramienta es apropiada.
            """
            
            # Consultar al LLM
            response = self.llm.invoke(tool_selection_prompt)
            tool_response = response.content.strip().lower()
            
            # Procesar la respuesta para extraer el nombre de la herramienta
            tool_to_use = "ninguna"
            
            # Lista de nombres de herramientas disponibles
            tool_names = [tool.name.lower() for tool in self.tools]
            
            # Verificar si algún nombre de herramienta está en la respuesta
            for name in tool_names:
                if name in tool_response:
                    tool_to_use = name
                    break
            
            logger.info(f"Herramienta seleccionada: {tool_to_use}")
            
            # Asegurarse de que context esté inicializado
            context = state.get("context", {})
                
            # Actualizar el contexto con la herramienta seleccionada
            updated_context = {
                **context,
                "selected_tool": tool_to_use
            }
            
            return {
                **state,
                "context": updated_context,
                "next_step": "execute_tool" if tool_to_use != "ninguna" else "generate_response"
            }
            
        except Exception as e:
            logger.error(f"Error en select_tool: {str(e)}")
            # Devolver un estado seguro con un contexto vacío
            return {
                **state,
                "context": {"selected_tool": "ninguna"},
                "next_step": "generate_response"  # En caso de error, ir directamente a la respuesta
            }
    
    def _pre_check_tools(self, message: str) -> str:
        """
        Verifica directamente si el mensaje contiene palabras clave para forzar el uso de herramientas.
        Retorna el nombre de la herramienta o una cadena vacía.
        """
        message_lower = message.lower()
        
        # Palabras clave para datetime
        datetime_keywords = [
            "fecha", "día", "hora", "tiempo", "feriado", "festivo", "holiday",
            "zona horaria", "calendario", "reloj", "cuando es", "qué día", "que hora"
        ]
        
        # Palabras clave para company_ranking
        company_keywords = [
            "empresa", "compañía", "ranking", "rank", "clasificación", "top", 
            "mayor", "mejor", "inversión", "ingresos", "valor", "mercado", 
            "empleados", "trabajadores", "personal"
        ]
        
        # Verificar coincidencias para cada herramienta
        if any(keyword in message_lower for keyword in datetime_keywords):
            return "datetime"
        
        if any(keyword in message_lower for keyword in company_keywords):
            return "company_ranking"
        
        return ""
    
    def _should_use_tool(self, state: ConversationState) -> bool:
        """
        Determina si se debe usar una herramienta basado en el contexto.
        """
        # Acceso seguro al contexto
        context = state.get("context", {})
        selected_tool = context.get("selected_tool", "ninguna")
        return selected_tool != "ninguna"
    
    def _execute_tool(self, state: ConversationState) -> ConversationState:
        """
        Ejecuta la herramienta seleccionada.
        """
        # Acceso seguro al contexto
        context = state.get("context", {})
        selected_tool_name = context.get("selected_tool", "ninguna")
        
        messages = state["messages"]
        last_message = messages[-1].content if messages else ""
        
        # Inicialización segura de tool_results si no existe
        tool_results = state.get("tool_results", {}).copy()
        
        try:
            # Buscar la herramienta por nombre
            selected_tool = None
            for tool in self.tools:
                if tool.name.lower() == selected_tool_name.lower():
                    selected_tool = tool
                    break
            
            if selected_tool:
                logger.info(f"Ejecutando herramienta: {selected_tool.name}")
                result = selected_tool.run(last_message)
                tool_results[selected_tool.name] = result
                
                return {
                    **state,
                    "tool_results": tool_results,
                    "next_step": "generate_response"
                }
            else:
                logger.warning(f"No se encontró la herramienta: {selected_tool_name}")
                return {
                    **state,
                    "next_step": "generate_response"
                }
                
        except Exception as e:
            logger.error(f"Error ejecutando herramienta: {str(e)}")
            return {
                **state,
                "next_step": "generate_response"
            }
    
    def _generate_response(self, state: ConversationState) -> ConversationState:
        """
        Genera una respuesta basada en el estado actual.
        """
        try:
            messages = state["messages"]
            # Acceso seguro a tool_results
            tool_results = state.get("tool_results", {})
            
            # Construir el contexto para el LLM
            history = "\n".join([f"Usuario: {msg.content}" if isinstance(msg, HumanMessage) else f"Asistente: {msg.content}" for msg in messages])
            
            # Añadir resultados de herramientas si hay
            tool_info = ""
            if tool_results:
                tool_info = "Resultados de herramientas:\n"
                for tool_name, result in tool_results.items():
                    tool_info += f"- {tool_name}: {result}\n"
            
            # El prompt final para el LLM
            prompt = f"""{SYSTEM_PROMPT}

Historial de conversación:
{history}

{tool_info}

Por favor, genera una respuesta apropiada para el usuario basada en toda esta información.
Recuerda: 
1. Usa EXACTAMENTE los datos proporcionados por las herramientas, no los inventes ni modifiques.
2. Si las herramientas proporcionan nombres, cifras o datos específicos, úsalos tal cual.
3. Cuando las herramientas devuelven resultados, haz que tu respuesta sea clara y directa.
"""
            
            # Generar respuesta con el LLM
            response = self.llm.invoke(prompt)
            
            # Actualizar el estado con la respuesta
            new_messages = messages + [AIMessage(content=response.content)]
            
            return {
                **state,
                "messages": new_messages,
                "next_step": "complete"
            }
            
        except Exception as e:
            logger.error(f"Error generando respuesta: {str(e)}")
            # Añadir un mensaje de error como respuesta
            error_response = "Lo siento, tuve un problema al generar una respuesta. Por favor, intenta nuevamente."
            new_messages = messages + [AIMessage(content=error_response)]
            
            return {
                **state,
                "messages": new_messages,
                "next_step": "complete"
            }