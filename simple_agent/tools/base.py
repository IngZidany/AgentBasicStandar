from langchain.tools import BaseTool
import logging
from typing import Optional, Type, Dict, Any
from pydantic import BaseModel, Field

# Configurar logging
logger = logging.getLogger(__name__)

class SimpleTool(BaseTool):
    """
    Clase base simple para herramientas.
    """
    name: str = Field(default="base_tool", description="Nombre de la herramienta")
    description: str = Field(default="Descripción base de la herramienta", description="Descripción de la herramienta")
    args_schema: Optional[Type[BaseModel]] = None
    
    def _run(self, input_value: str) -> str:
        """
        Método que implementa BaseTool.
        """
        try:
            logger.info(f"Ejecutando herramienta {self.name}")
            result = self.run(input_value)
            logger.info(f"Herramienta {self.name} ejecutada con éxito")
            return result
        except Exception as e:
            logger.error(f"Error ejecutando herramienta {self.name}: {str(e)}")
            return f"Error ejecutando {self.name}: {str(e)}"
            
    async def _arun(self, input_value: str) -> str:
        """
        Versión asíncrona para ejecutar la herramienta.
        """
        return self._run(input_value)
        
    def run(self, input_str: str) -> str:
        """
        Método que deben implementar las clases derivadas.
        """
        raise NotImplementedError("Las subclases deben implementar este método")