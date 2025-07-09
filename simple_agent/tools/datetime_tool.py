from pydantic import BaseModel, Field
import datetime
import pytz
import re
import logging
from typing import Dict, List, Optional, Any, ClassVar

from .base import SimpleTool

# Configurar logging
logger = logging.getLogger(__name__)

class DateTimeInput(BaseModel):
    """
    Modelo para la entrada de la herramienta de fecha y hora.
    """
    query: str = Field(
        ..., 
        description="Consulta sobre fecha y hora"
    )

class DateTimeTool(SimpleTool):
    """
    Herramienta para proporcionar información sobre fecha y hora actual.
    """
    name: str = Field(default="datetime", description="Nombre de la herramienta")
    description: str = Field(
        default="Proporciona información precisa sobre la fecha y hora actual, días festivos, o conversión entre zonas horarias",
        description="Descripción de la herramienta"
    )
    args_schema: ClassVar[type] = DateTimeInput
    
    # Ciudades principales de Perú con sus zonas horarias
    PERU_CITIES: Dict[str, str] = {
        "lima": "America/Lima",
        "arequipa": "America/Lima",
        "trujillo": "America/Lima",
        "chiclayo": "America/Lima",
        "iquitos": "America/Lima",
        "cusco": "America/Lima",
        "piura": "America/Lima",
        "huancayo": "America/Lima",
        "tacna": "America/Lima",
        "pucallpa": "America/Lima"
    }
    
    # Zonas horarias internacionales comunes
    INTERNATIONAL_TIMEZONES: Dict[str, str] = {
        "nueva york": "America/New_York",
        "los angeles": "America/Los_Angeles",
        "madrid": "Europe/Madrid",
        "londres": "Europe/London",
        "parís": "Europe/Paris",
        "berlín": "Europe/Berlin",
        "tokio": "Asia/Tokyo",
        "sydney": "Australia/Sydney",
        "beijing": "Asia/Shanghai",
        "río de janeiro": "America/Sao_Paulo"
    }
    
    # Días festivos en Perú (simplificado para demostración)
    PERU_HOLIDAYS: Dict[str, str] = {
        "01-01": "Año Nuevo",
        "01-04": "Día de la Integración Nacional",
        "04-06": "Jueves Santo",
        "04-07": "Viernes Santo",
        "05-01": "Día del Trabajo",
        "06-29": "Día de San Pedro y San Pablo",
        "07-28": "Día de la Independencia",
        "07-29": "Día de las Fuerzas Armadas",
        "08-30": "Día de Santa Rosa de Lima",
        "10-08": "Combate de Angamos",
        "11-01": "Día de Todos los Santos",
        "12-08": "Día de la Inmaculada Concepción",
        "12-25": "Navidad"
    }
    
    def run(self, input_str: str) -> str:
        """
        Proporciona información sobre fecha y hora actual.
        """
        try:
            # Identificar el tipo de consulta
            if self._is_holiday_query(input_str):
                return self._get_holiday_info()
            elif self._is_timezone_query(input_str):
                return self._get_timezone_info(input_str)
            else:
                # Por defecto, mostrar fecha y hora actual
                return self._get_current_datetime()
                
        except Exception as e:
            logger.error(f"Error en herramienta de fecha/hora: {str(e)}")
            return "No pude obtener la información de fecha y hora solicitada."
    
    def _is_holiday_query(self, text: str) -> bool:
        """
        Determina si la consulta es sobre días festivos.
        """
        holiday_keywords = [
            "feriado", "festivo", "día festivo", "día feriado", 
            "festividad", "celebración", "holiday", "días libres"
        ]
        
        return any(keyword in text.lower() for keyword in holiday_keywords)
    
    def _is_timezone_query(self, text: str) -> bool:
        """
        Determina si la consulta es sobre zonas horarias.
        """
        timezone_keywords = [
            "zona horaria", "hora en", "qué hora es en", "diferencia horaria",
            "timezone", "time zone", "hora local"
        ]
        
        return any(keyword in text.lower() for keyword in timezone_keywords)
    
    def _get_current_datetime(self) -> str:
        """
        Obtiene la fecha y hora actual en Perú.
        """
        # Usar zona horaria de Perú por defecto
        peru_tz = pytz.timezone("America/Lima")
        now = datetime.datetime.now(peru_tz)
        
        # Formatear fecha y hora
        date_str = now.strftime("%A %d de %B de %Y")
        time_str = now.strftime("%H:%M:%S")
        
        # Traducir día y mes al español
        spanish_days = {
            "Monday": "Lunes",
            "Tuesday": "Martes",
            "Wednesday": "Miércoles",
            "Thursday": "Jueves",
            "Friday": "Viernes",
            "Saturday": "Sábado",
            "Sunday": "Domingo"
        }
        
        spanish_months = {
            "January": "enero",
            "February": "febrero",
            "March": "marzo",
            "April": "abril",
            "May": "mayo",
            "June": "junio",
            "July": "julio",
            "August": "agosto",
            "September": "septiembre",
            "October": "octubre",
            "November": "noviembre",
            "December": "diciembre"
        }
        
        for english, spanish in spanish_days.items():
            date_str = date_str.replace(english, spanish)
            
        for english, spanish in spanish_months.items():
            date_str = date_str.replace(english, spanish)
        
        # Verificar si es un día festivo
        month_day = now.strftime("%m-%d")
        holiday = self.PERU_HOLIDAYS.get(month_day)
        holiday_info = f"\nHoy es {holiday}." if holiday else ""
        
        return f"""Fecha y hora actual en Perú:
        
Fecha: {date_str}
Hora: {time_str} (UTC-5, hora de Perú){holiday_info}

Zona horaria: América/Lima (GMT-5)
"""
    
    def _get_holiday_info(self) -> str:
        """
        Obtiene información sobre días festivos en Perú.
        """
        # Obtener fecha actual
        peru_tz = pytz.timezone("America/Lima")
        now = datetime.datetime.now(peru_tz)
        current_date = now.strftime("%m-%d")
        current_month = now.strftime("%m")
        
        # Verificar si hoy es un día festivo
        today_holiday = self.PERU_HOLIDAYS.get(current_date)
        
        # Encontrar próximos días festivos
        upcoming_holidays = []
        for date_str, holiday_name in self.PERU_HOLIDAYS.items():
            month = date_str.split("-")[0]
            day = date_str.split("-")[1]
            
            # Si el mes es posterior al actual o es el mismo mes pero día posterior
            if (month > current_month) or (month == current_month and day > now.strftime("%d")):
                # Crear fecha para este año
                holiday_date = datetime.datetime(now.year, int(month), int(day))
                # Calcular días restantes
                days_remaining = (holiday_date - now.replace(tzinfo=None)).days
                
                upcoming_holidays.append({
                    "name": holiday_name,
                    "date": holiday_date.strftime("%d de %B"),
                    "days_remaining": days_remaining
                })
        
        # Ordenar por proximidad
        upcoming_holidays.sort(key=lambda x: x["days_remaining"])
        
        # Construir respuesta
        result = "DÍAS FESTIVOS EN PERÚ\n\n"
        
        if today_holiday:
            result += f"HOY ES FERIADO: {today_holiday}\n\n"
            
        result += "Próximos días festivos:\n"
        
        for i, holiday in enumerate(upcoming_holidays[:5], 1):
            # Traducir mes al español
            date_str = holiday["date"]
            for english, spanish in {
                "January": "enero",
                "February": "febrero",
                "March": "marzo",
                "April": "abril",
                "May": "mayo",
                "June": "junio",
                "July": "julio",
                "August": "agosto",
                "September": "septiembre",
                "October": "octubre",
                "November": "noviembre",
                "December": "diciembre"
            }.items():
                date_str = date_str.replace(english, spanish)
                
            result += f"{i}. {holiday['name']} - {date_str} "
            result += f"(en {holiday['days_remaining']} días)\n"
            
        result += "\nNota: Esta información puede no incluir feriados regionales o no laborables específicos."
        
        return result
    
    def _get_timezone_info(self, query: str) -> str:
        """
        Obtiene información sobre las zonas horarias mencionadas.
        """
        # Extraer ciudades/países mencionados
        city = self._extract_location(query)
        
        if not city:
            # Si no se menciona una ciudad específica, mostrar información de zonas horarias comunes
            return self._get_multiple_timezones()
            
        # Buscar la zona horaria para la ciudad
        timezone_str = self._get_timezone_for_city(city)
        
        if not timezone_str:
            return f"No pude encontrar información sobre la zona horaria de '{city}'. Puedo proporcionar información sobre ciudades principales de Perú y del mundo."
        
        # Mostrar la hora actual en esa zona horaria
        try:
            timezone = pytz.timezone(timezone_str)
            now = datetime.datetime.now(timezone)
            
            # Formatear fecha y hora
            date_str = now.strftime("%A %d de %B de %Y")
            time_str = now.strftime("%H:%M:%S")
            
            # Traducir día y mes al español
            spanish_days = {
                "Monday": "Lunes",
                "Tuesday": "Martes",
                "Wednesday": "Miércoles",
                "Thursday": "Jueves",
                "Friday": "Viernes",
                "Saturday": "Sábado",
                "Sunday": "Domingo"
            }
            
            spanish_months = {
                "January": "enero",
                "February": "febrero",
                "March": "marzo",
                "April": "abril",
                "May": "mayo",
                "June": "junio",
                "July": "julio",
                "August": "agosto",
                "September": "septiembre",
                "October": "octubre",
                "November": "noviembre",
                "December": "diciembre"
            }
            
            for english, spanish in spanish_days.items():
                date_str = date_str.replace(english, spanish)
                
            for english, spanish in spanish_months.items():
                date_str = date_str.replace(english, spanish)
                
            # Obtener diferencia con hora de Perú
            peru_time = datetime.datetime.now(pytz.timezone("America/Lima"))
            time_diff = (now.hour - peru_time.hour) % 24
            
            diff_str = ""
            if time_diff > 0:
                diff_str = f"{time_diff} horas más que en Perú"
            elif time_diff < 0:
                diff_str = f"{abs(time_diff)} horas menos que en Perú"
            else:
                diff_str = "misma hora que en Perú"
            
            city = city.capitalize()
            return f"""Fecha y hora actual en {city}:
            
Fecha: {date_str}
Hora: {time_str} ({diff_str})

Zona horaria: {timezone_str}
"""
            
        except Exception as e:
            logger.error(f"Error obteniendo hora para {city}: {str(e)}")
            return f"No pude obtener la hora actual para {city}."
    
    def _extract_location(self, text: str) -> str:
        """
        Extrae la ubicación mencionada en la consulta.
        """
        # Patrones para detectar menciones de ubicación
        patterns = [
            r'hora (?:en|de) ([a-zá-úñ\s]+)',  # "hora en Lima"
            r'(?:qué|que) hora es en ([a-zá-úñ\s]+)',  # "qué hora es en Madrid"
            r'zona horaria (?:de|en) ([a-zá-úñ\s]+)',  # "zona horaria de Nueva York"
            r'hora actual (?:en|de) ([a-zá-úñ\s]+)',  # "hora actual en Tokio"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                location = match.group(1).strip()
                return location
                
        return ""
    
    def _get_timezone_for_city(self, city: str) -> Optional[str]:
        """
        Obtiene la zona horaria para una ciudad.
        """
        city_lower = city.lower()
        
        # Buscar en ciudades de Perú
        if city_lower in self.PERU_CITIES:
            return self.PERU_CITIES[city_lower]
            
        # Buscar en zonas horarias internacionales
        if city_lower in self.INTERNATIONAL_TIMEZONES:
            return self.INTERNATIONAL_TIMEZONES[city_lower]
            
        # Buscar coincidencias parciales
        for known_city, timezone in {**self.PERU_CITIES, **self.INTERNATIONAL_TIMEZONES}.items():
            if city_lower in known_city or known_city in city_lower:
                return timezone
                
        return None
    
    def _get_multiple_timezones(self) -> str:
        """
        Muestra la hora actual en diferentes zonas horarias.
        """
        result = "HORA ACTUAL EN DIFERENTES CIUDADES\n\n"
        
        # Seleccionar algunas ciudades importantes
        selected_cities = {
            "Lima": "America/Lima",
            "Nueva York": "America/New_York",
            "Londres": "Europe/London",
            "Madrid": "Europe/Madrid",
            "Tokio": "Asia/Tokyo",
            "Sydney": "Australia/Sydney"
        }
        
        # Obtener la hora actual en Perú como referencia
        peru_time = datetime.datetime.now(pytz.timezone("America/Lima"))
        
        # Mostrar hora para cada ciudad
        for city, timezone_str in selected_cities.items():
            try:
                timezone = pytz.timezone(timezone_str)
                now = datetime.datetime.now(timezone)
                time_str = now.strftime("%H:%M")
                
                # Calcular diferencia con Perú
                time_diff = (now.hour - peru_time.hour) % 24
                
                diff_str = ""
                if city == "Lima":
                    diff_str = "(hora local)"
                elif time_diff > 0:
                    diff_str = f"(+{time_diff}h)"
                elif time_diff < 0:
                    diff_str = f"(-{abs(time_diff)}h)"
                else:
                    diff_str = "(=h)"
                
                result += f"{city}: {time_str} {diff_str}\n"
                
            except Exception as e:
                logger.error(f"Error obteniendo hora para {city}: {str(e)}")
        
        result += "\nPuedes preguntar por la hora en una ciudad específica para más detalles."
        
        return result