import streamlit as st
import os
import uuid
import logging
from dotenv import load_dotenv
from agent.conversation import ConversationalAgent
from tools.company_ranking import CompanyRankingTool
from tools.datetime_tool import DateTimeTool

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuración de la página de Streamlit
st.set_page_config(
    page_title="Asistente IA",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Estilos CSS personalizados - versión corregida para mostrar correctamente los mensajes
st.markdown("""
<style>
    /* Fondo principal */
    .stApp {
        background-color: #171923;
        color: white;
    }
    
    /* Título principal */
    .title-container {
        background: linear-gradient(90deg, #4299E1 0%, #38B2AC 100%);
        padding: 12px 20px;
        border-radius: 8px;
        text-align: center;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .title-container h1 {
        color: white;
        font-size: 24px;
        font-weight: 600;
        margin: 0;
    }
    
    /* Contenedor del chat */
    .chat-container {
        display: flex;
        flex-direction: column;
        gap: 15px;
        margin-bottom: 80px; /* Espacio para el input */
        padding-bottom: 20px;
    }
    
    /* Mensajes */
    .chat-message {
        display: flex;
        align-items: flex-start;
        padding: 15px;
        border-radius: 10px;
        max-width: 80%;
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
    }
    
    .chat-message.user {
        background-color: #2D3748;
        margin-left: auto;
        border-bottom-right-radius: 2px;
    }
    
    .chat-message.bot {
        background-color: #1A202C;
        margin-right: auto;
        border-bottom-left-radius: 2px;
    }
    
    .chat-message .avatar {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        margin-right: 12px;
        border: 2px solid #4FD1C5;
    }
    
    .chat-message.user .avatar {
        border-color: #3182CE;
    }
    
    .chat-message .message {
        color: #E2E8F0;
        line-height: 1.5;
    }
    
    /* Input del usuario - fijo en la parte inferior */
    .input-area {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background-color: #1A202C;
        padding: 15px 25% 15px 25%;
        z-index: 1000;
        box-shadow: 0 -4px 10px rgba(0, 0, 0, 0.2);
    }
    
    /* Estilizar el input */
    .stTextInput > div > div > input {
        background-color: #2D3748 !important;
        color: white !important;
        border: 1px solid #4A5568 !important;
        border-radius: 20px !important;
        padding: 10px 20px !important;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #4299E1 !important;
        box-shadow: 0 0 0 1px #4299E1 !important;
    }
    
    .stTextInput > div > div > input::placeholder {
        color: #A0AEC0 !important;
    }
    
    /* Ocultar elementos innecesarios de Streamlit */
    #MainMenu, footer, header {
        visibility: hidden;
    }
    
    /* Animación para el mensaje de "pensando" */
    @keyframes thinking {
        0% { content: "."; }
        33% { content: ".."; }
        66% { content: "..."; }
    }
    
    .thinking-animation::after {
        content: "...";
        animation: thinking 1.5s infinite;
    }
    
    /* Hacer que el contenido principal no se solape con el input fijo */
    .main-content {
        padding-bottom: 80px;
    }
    
    /* Ajustes para pantallas más pequeñas */
    @media (max-width: 992px) {
        .input-area {
            padding: 15px 10% 15px 10%;
        }
        
        .chat-message {
            max-width: 90%;
        }
    }
</style>
""", unsafe_allow_html=True)

def process_user_input():
    """Procesa el input del usuario cuando se envía un mensaje."""
    user_input = st.session_state.user_input
    
    if user_input:
        logger.info(f"Nuevo mensaje del usuario: {user_input}")
        
        # Añadir mensaje del usuario al historial visual
        st.session_state.message_history.append({"role": "user", "content": user_input})
        
        # Asegurar que tenemos un session_id para el usuario actual
        if "session_id" not in st.session_state:
            st.session_state.session_id = str(uuid.uuid4())
            logger.info(f"Creado nuevo session_id: {st.session_state.session_id}")
        
        # Procesar mensaje con el agente
        with st.spinner("Pensando..."):
            try:
                logger.info(f"Enviando mensaje al agente con session_id: {st.session_state.session_id}")
                response = st.session_state.agent.process_message(
                    message=user_input, 
                    session_id=st.session_state.session_id
                )
                logger.info(f"Respuesta recibida del agente: {response[:100]}...")
                
                # Añadir respuesta del asistente al historial visual
                st.session_state.message_history.append({"role": "assistant", "content": response})
            except Exception as e:
                logger.error(f"Error al procesar mensaje: {str(e)}")
                error_msg = f"Lo siento, ocurrió un error al procesar tu mensaje: {str(e)}"
                st.session_state.message_history.append({"role": "assistant", "content": error_msg})
        
        # Limpiar el input
        st.session_state.user_input = ""

def main():
    # Cargar variables de entorno
    load_dotenv()
    
    # Configuración desde variables de entorno
    project_id = os.getenv('PROJECT_ID')
    location = os.getenv('REGION')
    logger.info(f"Configuración cargada: PROJECT_ID={project_id}, REGION={location}")
    
    # Título centrado con mejor diseño
    st.markdown('<div class="title-container"><h1>💬 Asistente Virtual Empresarial</h1></div>', unsafe_allow_html=True)
    
    # Inicializar el estado de la sesión si no existe
    if "message_history" not in st.session_state:
        logger.info("Inicializando historial de mensajes")
        st.session_state.message_history = []
    
    if "agent" not in st.session_state:
        logger.info("Inicializando agente conversacional")
        # Crear herramientas
        tools = [
            CompanyRankingTool(),
            DateTimeTool()
        ]
        
        # Inicializar el agente
        try:
            st.session_state.agent = ConversationalAgent(
                project_id=project_id,
                location=location,
                tools=tools
            )
            logger.info("Agente inicializado correctamente")
            
            # Mensaje inicial de bienvenida
            welcome_message = """¡Hola! Soy tu asistente virtual empresarial. 

Puedo ayudarte con:
• Información sobre rankings de empresas peruanas
• Fechas, horas y zonas horarias
• Días festivos en Perú

¿En qué puedo ayudarte hoy?"""
            st.session_state.message_history.append({"role": "assistant", "content": welcome_message})
        except Exception as e:
            logger.error(f"Error al inicializar el agente: {str(e)}")
            st.error(f"Error al inicializar el agente: {str(e)}")
            st.session_state.message_history.append({"role": "assistant", "content": "Hubo un problema al iniciar el asistente. Por favor, verifica la configuración y vuelve a intentarlo."})
    
    # Contenedor principal para el chat (con clase para manejar el espaciado)
    with st.container():
        st.markdown('<div class="main-content">', unsafe_allow_html=True)
        
        # Contenedor del chat
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        
        # Mostrar mensajes del historial
        for message in st.session_state.message_history:
            if message["role"] == "user":
                display_user_message(message["content"])
            else:
                display_assistant_message(message["content"])
        
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Input fijo en la parte inferior
    st.markdown('<div class="input-area">', unsafe_allow_html=True)
    st.text_input(
        label="Escribe tu mensaje aquí",
        label_visibility="collapsed",
        value="",
        placeholder="Escribe tu mensaje aquí...",
        key="user_input",
        on_change=process_user_input
    )
    st.markdown('</div>', unsafe_allow_html=True)

def display_user_message(message):
    """Muestra un mensaje del usuario en la interfaz."""
    message_html = message.replace('\n', '<br>')
    st.markdown(
        f'<div class="chat-message user">'
        f'<img src="https://api.dicebear.com/7.x/personas/svg?seed=User" class="avatar">'
        f'<div class="message">{message_html}</div>'
        f'</div>', 
        unsafe_allow_html=True
    )

def display_assistant_message(message):
    """Muestra un mensaje del asistente en la interfaz."""
    message_html = message.replace('\n', '<br>')
    st.markdown(
        f'<div class="chat-message bot">'
        f'<img src="https://api.dicebear.com/7.x/bottts/svg?seed=Felix" class="avatar">'
        f'<div class="message">{message_html}</div>'
        f'</div>', 
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()