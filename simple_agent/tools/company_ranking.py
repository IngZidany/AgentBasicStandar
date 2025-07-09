from pydantic import BaseModel, Field
import re
import logging
from typing import Dict, List, Optional, Any, ClassVar

from .base import SimpleTool

# Configurar logging
logger = logging.getLogger(__name__)

class CompanyRankingInput(BaseModel):
    """
    Modelo para la entrada de la herramienta de ranking de empresas.
    """
    query: str = Field(
        ..., 
        description="Consulta sobre ranking de empresas"
    )

class CompanyRankingTool(SimpleTool):
    """
    Herramienta para proporcionar información sobre rankings empresariales.
    """
    name: str = Field(default="company_ranking", description="Nombre de la herramienta")
    description: str = Field(
        default="Proporciona información sobre rankings de empresas top por inversión, ingresos, valor de mercado o número de empleados",
        description="Descripción de la herramienta"
    )
    args_schema: ClassVar[type] = CompanyRankingInput
    
    # Datos simulados de rankings empresariales (para demostración)
    COMPANY_RANKINGS: Dict[str, List[Dict[str, str]]] = {
        "inversión": [
            {"rank": 1, "name": "Grupo Romero", "investment": "USD 1,250 millones", "sector": "Diversificado"},
            {"rank": 2, "name": "Grupo Breca", "investment": "USD 980 millones", "sector": "Minería/Banca"},
            {"rank": 3, "name": "Grupo Intercorp", "investment": "USD 830 millones", "sector": "Retail/Banca"},
            {"rank": 4, "name": "Southern Peru Copper", "investment": "USD 750 millones", "sector": "Minería"},
            {"rank": 5, "name": "Alicorp", "investment": "USD 620 millones", "sector": "Consumo masivo"}
        ],
        "ingresos": [
            {"rank": 1, "name": "Petroperú", "revenue": "USD 4,800 millones", "sector": "Energía"},
            {"rank": 2, "name": "Southern Peru Copper", "revenue": "USD 3,900 millones", "sector": "Minería"},
            {"rank": 3, "name": "Grupo Romero", "revenue": "USD 3,200 millones", "sector": "Diversificado"},
            {"rank": 4, "name": "Grupo Intercorp", "revenue": "USD 2,950 millones", "sector": "Retail/Banca"},
            {"rank": 5, "name": "Glencore Perú", "revenue": "USD 2,700 millones", "sector": "Minería"}
        ],
        "valor de mercado": [
            {"rank": 1, "name": "Credicorp", "market_value": "USD 12,500 millones", "sector": "Banca"},
            {"rank": 2, "name": "Southern Peru Copper", "market_value": "USD 9,800 millones", "sector": "Minería"},
            {"rank": 3, "name": "Grupo Intercorp", "market_value": "USD 5,200 millones", "sector": "Retail/Banca"},
            {"rank": 4, "name": "Buenaventura", "market_value": "USD 2,800 millones", "sector": "Minería"},
            {"rank": 5, "name": "InRetail", "market_value": "USD 2,300 millones", "sector": "Retail"}
        ],
        "empleados": [
            {"rank": 1, "name": "Grupo Intercorp", "employees": "90,000+", "sector": "Retail/Banca"},
            {"rank": 2, "name": "Grupo Romero", "employees": "75,000+", "sector": "Diversificado"},
            {"rank": 3, "name": "Grupo Breca", "employees": "45,000+", "sector": "Diversificado"},
            {"rank": 4, "name": "Grupo Gloria", "employees": "35,000+", "sector": "Alimentos"},
            {"rank": 5, "name": "Grupo AJE", "employees": "20,000+", "sector": "Bebidas"}
        ]
    }
    
    def run(self, input_str: str) -> str:
        """
        Proporciona información sobre rankings de empresas.
        """
        try:
            logger.info(f"Recibida consulta: {input_str}")
            
            # Detectar solicitudes múltiples
            if self._contains_multiple_rankings(input_str):
                logger.info("Detectada solicitud múltiple de rankings")
                return self._process_multiple_rankings(input_str)
            
            # Verificación directa para inversión (alta prioridad)
            if self._is_investment_query(input_str):
                logger.info("Detectada consulta específica sobre ranking por inversión")
                return self._format_ranking_data("inversión", self.COMPANY_RANKINGS["inversión"])
            
            # Verificación directa para empleados
            if self._is_employees_query(input_str):
                logger.info("Detectada consulta sobre ranking por empleados")
                return self._format_ranking_data("empleados", self.COMPANY_RANKINGS["empleados"])
            
            # Verificación directa para ingresos
            if self._is_revenue_query(input_str):
                logger.info("Detectada consulta sobre ranking por ingresos")
                return self._format_ranking_data("ingresos", self.COMPANY_RANKINGS["ingresos"])
            
            # Verificación directa para valor de mercado
            if self._is_market_value_query(input_str):
                logger.info("Detectada consulta sobre ranking por valor de mercado")
                return self._format_ranking_data("valor de mercado", self.COMPANY_RANKINGS["valor de mercado"])
            
            # Continuar con el proceso normal para otros tipos de rankings
            ranking_type = self._extract_ranking_type(input_str)
            
            if not ranking_type:
                # Si no se especifica un tipo, devolver información general
                return self._get_general_ranking_info()
                
            # Obtener datos del ranking específico
            if ranking_type in self.COMPANY_RANKINGS:
                return self._format_ranking_data(ranking_type, self.COMPANY_RANKINGS[ranking_type])
            else:
                similar_types = self._find_similar_ranking_types(ranking_type)
                if similar_types:
                    result = f"No encontré información específica sobre '{ranking_type}', pero puedo ofrecerte ranking por {', '.join(similar_types)}.\n\n"
                    # Mostrar el primer ranking similar
                    return result + self._format_ranking_data(similar_types[0], self.COMPANY_RANKINGS[similar_types[0]])
                else:
                    return f"No encontré información sobre rankings de empresas por '{ranking_type}'. Puedo ofrecerte información sobre empresas por inversión, ingresos, valor de mercado o número de empleados."
                
        except Exception as e:
            logger.error(f"Error en herramienta de ranking: {str(e)}")
            return "No pude obtener la información de rankings empresariales solicitada."
    
    def _is_investment_query(self, text: str) -> bool:
        """
        Determina si la consulta es específicamente sobre inversión.
        """
        text_lower = text.lower()
        
        # Patrones específicos para inversión
        investment_patterns = [
            r'(inversion|inversión|inverten|invierten|inversi)',
            r'(ranking|clasificación|top|mejor).*?(inver)',
            r'empresa.*?(inver)',
            r'(inver).*?(empresa)',
            r'por inversion',
            r'de inversion'
        ]
        
        # Si cualquiera de los patrones coincide, es una consulta de inversión
        for pattern in investment_patterns:
            if re.search(pattern, text_lower):
                return True
                
        return False
    
    def _is_employees_query(self, text: str) -> bool:
        """
        Determina si la consulta es específicamente sobre número de empleados.
        """
        text_lower = text.lower()
        
        # Patrones específicos para empleados
        patterns = [
            r'(empleado|empleados|trabaj|personal)',
            r'(ranking|clasificación|top|mejor).*?(empleado|personal|trabaj)',
            r'empresa.*?(empleado|personal|trabaj)',
            r'(empleado|personal|trabaj).*?(empresa)'
        ]
        
        # Si cualquiera de los patrones coincide
        for pattern in patterns:
            if re.search(pattern, text_lower):
                return True
                
        return False
    
    def _is_revenue_query(self, text: str) -> bool:
        """
        Determina si la consulta es específicamente sobre ingresos.
        """
        text_lower = text.lower()
        
        # Patrones específicos para ingresos
        patterns = [
            r'(ingreso|ingresos|factura|venta|beneficio|ganancias)',
            r'(ranking|clasificación|top|mejor).*?(ingreso|factura|venta|ganancias)',
            r'empresa.*?(ingreso|factura|venta|ganancias)',
            r'(ingreso|factura|venta|ganancias).*?(empresa)'
        ]
        
        # Si cualquiera de los patrones coincide
        for pattern in patterns:
            if re.search(pattern, text_lower):
                return True
                
        return False
    
    def _is_market_value_query(self, text: str) -> bool:
        """
        Determina si la consulta es específicamente sobre valor de mercado.
        """
        text_lower = text.lower()
        
        # Patrones específicos para valor de mercado
        patterns = [
            r'(valor|mercado|capitalización|capital|bolsa)',
            r'(ranking|clasificación|top|mejor).*?(valor|mercado|capitalización)',
            r'empresa.*?(valor|mercado|capitalización)',
            r'(valor|mercado|capitalización).*?(empresa)'
        ]
        
        # Si cualquiera de los patrones coincide
        for pattern in patterns:
            if re.search(pattern, text_lower):
                return True
                
        return False
    
    def _contains_multiple_rankings(self, text: str) -> bool:
        """
        Detecta si el mensaje contiene solicitudes de múltiples rankings.
        """
        text_lower = text.lower()
        
        # Patrones para detectar múltiples rankings
        patterns = [
            r'(inversion|inversión).*?(ingreso|factura)',
            r'(ingreso|factura).*?(inversion|inversión)',
            r'(empleado|personal).*?(ingreso|inversion)',
            r'(.*?)(y|e) (.*?)(?:ranking|por|sobre)',
            r'(dos|ambos|múltiples|varios) (ranking|tipo)'
        ]
        
        # Verificar si hay al menos un patrón que coincida
        for pattern in patterns:
            if re.search(pattern, text_lower):
                return True
                
        # Contar menciones de categorías diferentes
        categories = ["inversión", "ingreso", "valor", "empleado"]
        mentions = sum(1 for cat in categories if cat in text_lower)
        
        return mentions > 1
    
    def _process_multiple_rankings(self, text: str) -> str:
        """
        Procesa y devuelve información para múltiples rankings.
        """
        result = "Aquí te presento la información de múltiples rankings que solicitaste:\n\n"
        
        # Verificar cada tipo de ranking
        if self._is_investment_query(text):
            result += "--- RANKING POR INVERSIÓN ---\n"
            result += self._format_ranking_data("inversión", self.COMPANY_RANKINGS["inversión"]) + "\n\n"
            
        if self._is_revenue_query(text):
            result += "--- RANKING POR INGRESOS ---\n"
            result += self._format_ranking_data("ingresos", self.COMPANY_RANKINGS["ingresos"]) + "\n\n"
            
        if self._is_market_value_query(text):
            result += "--- RANKING POR VALOR DE MERCADO ---\n"
            result += self._format_ranking_data("valor de mercado", self.COMPANY_RANKINGS["valor de mercado"]) + "\n\n"
            
        if self._is_employees_query(text):
            result += "--- RANKING POR NÚMERO DE EMPLEADOS ---\n"
            result += self._format_ranking_data("empleados", self.COMPANY_RANKINGS["empleados"])
        
        # Si no se detectó ningún ranking específico, mostrar los dos más comunes
        if result == "Aquí te presento la información de múltiples rankings que solicitaste:\n\n":
            result += "--- RANKING POR INVERSIÓN ---\n"
            result += self._format_ranking_data("inversión", self.COMPANY_RANKINGS["inversión"]) + "\n\n"
            
            result += "--- RANKING POR INGRESOS ---\n"
            result += self._format_ranking_data("ingresos", self.COMPANY_RANKINGS["ingresos"])
        
        return result
    
    def _extract_ranking_type(self, text: str) -> str:
        """
        Extrae el tipo de ranking mencionado en el texto.
        """
        # Convertir a minúsculas para facilitar coincidencias
        text_lower = text.lower()
        
        # Buscar menciones directas de tipos de ranking
        for ranking_type in self.COMPANY_RANKINGS.keys():
            if ranking_type in text_lower:
                return ranking_type
                
        # Patrones para detectar solicitudes de ranking
        patterns = [
            r'empresas (?:con (?:mayor|más))?\s+(\w+)',  # "empresas con mayor inversión"
            r'ranking (?:de|por)\s+(\w+)',              # "ranking por ingresos"
            r'top (?:empresas|compañías) (?:en|por)\s+(\w+)',  # "top empresas en valor de mercado"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text_lower)
            if match:
                type_mention = match.group(1)
                # Mapear menciones comunes a nuestros tipos de ranking
                type_mapping = {
                    'inversiones': 'inversión',
                    'invierte': 'inversión',
                    'invierten': 'inversión',
                    'ingreso': 'ingresos',
                    'ganancias': 'ingresos',
                    'facturación': 'ingresos',
                    'valor': 'valor de mercado',
                    'capitalización': 'valor de mercado',
                    'empleos': 'empleados',
                    'trabajadores': 'empleados',
                    'personal': 'empleados'
                }
                
                if type_mention in type_mapping:
                    return type_mapping[type_mention]
                
                # Verificar similitud con nuestros tipos conocidos
                for known_type in self.COMPANY_RANKINGS.keys():
                    if type_mention in known_type or known_type in type_mention:
                        return known_type
        
        # Si no encuentra un tipo específico
        return ""
    
    def _find_similar_ranking_types(self, query: str) -> list:
        """
        Encuentra tipos de ranking similares al solicitado.
        """
        query = query.lower()
        similar_types = []
        
        # Mapeo de palabras relacionadas a tipos de ranking
        type_groups = {
            'inversión': ['inversión', 'invertir', 'inversionistas', 'capital'],
            'ingresos': ['ingresos', 'ventas', 'facturación', 'ganancias', 'beneficios'],
            'valor de mercado': ['valor', 'capitalización', 'bolsa', 'acciones', 'mercado'],
            'empleados': ['empleados', 'trabajadores', 'personal', 'plantilla', 'empleo']
        }
        
        # Buscar coincidencias en los grupos
        for ranking_type, related_words in type_groups.items():
            for word in related_words:
                if word in query:
                    similar_types.append(ranking_type)
                    break
        
        # Si no hay coincidencias específicas, devolver todos los tipos disponibles
        if not similar_types:
            return list(self.COMPANY_RANKINGS.keys())
            
        return similar_types
    
    def _get_general_ranking_info(self) -> str:
        """
        Proporciona información general sobre los rankings disponibles.
        """
        result = "Puedo ofrecerte información sobre los siguientes rankings empresariales en Perú:\n\n"
        
        result += "1. Ranking por inversión: Las empresas con mayor inversión en Perú\n"
        result += "2. Ranking por ingresos: Las empresas con mayores ingresos anuales\n"
        result += "3. Ranking por valor de mercado: Las empresas con mayor capitalización bursátil\n"
        result += "4. Ranking por empleados: Las empresas que generan más empleo\n\n"
        
        result += "¿Sobre cuál te gustaría obtener más información?"
        
        return result
    
    def _format_ranking_data(self, ranking_type: str, data: list) -> str:
        """
        Formatea los datos de ranking en un texto legible.
        """
        result = f"TOP 5 EMPRESAS PERUANAS POR {ranking_type.upper()}:\n\n"
        
        for company in data:
            result += f"{company['rank']}. {company['name']}\n"
            
            # Añadir la métrica correspondiente según el tipo de ranking
            if ranking_type == "inversión":
                result += f"   Inversión estimada: {company['investment']}\n"
            elif ranking_type == "ingresos":
                result += f"   Ingresos anuales: {company['revenue']}\n"
            elif ranking_type == "valor de mercado":
                result += f"   Valor de mercado: {company['market_value']}\n"
            elif ranking_type == "empleados":
                result += f"   Número de empleados: {company['employees']}\n"
                
            result += f"   Sector: {company['sector']}\n\n"
            
        result += "Nota: Datos simulados con fines demostrativos. Las cifras reales pueden variar."
        
        return result