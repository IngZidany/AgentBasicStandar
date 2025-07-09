from typing import List, Dict, TypedDict, Optional, Union, Any
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage

class ConversationState(TypedDict):
    """
    Estado de la conversación del agente.
    """
    # Historial de mensajes
    messages: List[Union[HumanMessage, AIMessage, BaseMessage]]
    
    # Contexto actual de la conversación
    context: Dict[str, Any]
    
    # Resultados de herramientas
    tool_results: Dict[str, str]
    
    # Estado de ejecución del grafo
    next_step: str

def create_initial_state() -> ConversationState:
    """
    Crea un estado inicial para la conversación.
    """
    return {
        "messages": [],
        "context": {},
        "tool_results": {},
        "next_step": "process_input"
    }