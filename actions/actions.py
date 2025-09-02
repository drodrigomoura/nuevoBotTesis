
from builtins import print
from typing import Any, Text, Dict, List
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk import Action, Tracker
from rasa_sdk import Action
from rasa_sdk.events import SlotSet
import json

import os
from dotenv import load_dotenv
from supabase import create_client, Client
import httpx

load_dotenv()
url: str = os.getenv("SUPABASE_URL")
key: str = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(url, key)

class ActionAuthenticateUser(Action):
    def name(self):
        return "action_authenticate_user"

    def run(self, dispatcher, tracker, domain):
        token = tracker.get_slot("auth_token")
        if token:
            # No enviar mensaje al usuario si el token es válido
            return [SlotSet("is_authenticated", True)]
        else:
            dispatcher.utter_message(text="No se recibió un token válido.")
            return [SlotSet("is_authenticated", False)]

class ActionConsultarAsistencia(Action):

    def name(self):
        return "action_consultar_asistencia"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain):
        # Verificar si el usuario está autenticado
        is_authenticated = tracker.get_slot('is_authenticated')

        if not is_authenticated:
            dispatcher.utter_message("❌ Necesitas estar autenticado para consultar tu asistencia. Por favor, inicia sesión primero.")
            return []

        # Obtener la matrícula del slot
        matricula = tracker.get_slot('matricula')

        if not matricula:
            dispatcher.utter_message("❌ No tengo tu número de matrícula. Por favor, proporciona tu matrícula para poder consultar tu asistencia.")
            return [SlotSet("flujo_actual", "consultar_asistencia")]

        # Obtener la materia del slot
        materia = tracker.get_slot('materia')

        if not materia:
            dispatcher.utter_message("❌ No tengo la materia especificada. Por favor, dime de qué materia quieres consultar la asistencia.")
            return [SlotSet("flujo_actual", "consultar_asistencia")]

        try:
            # Buscar el código de la materia por nombre
            materia_resp = supabase.table("Materia").select("codigo, nombre").ilike("nombre", "%" + materia + "%").execute()
            if not materia_resp.data:
                dispatcher.utter_message(f"❌ No se encontró la materia '{materia}' en la base de datos.")
                return [SlotSet("flujo_actual", None)]

            materia_codigo = materia_resp.data[0]["codigo"]
            nombre_materia = materia_resp.data[0]["nombre"]

            # Buscar las asistencias del estudiante para esa materia
            asistencia_resp = supabase.table("Asistencia").select('*').eq("estudiante", matricula).eq("materia", materia_codigo).execute()

            if not asistencia_resp.data:
                dispatcher.utter_message(f"📊 No se encontraron registros de asistencia para la matrícula {matricula} en la materia '{nombre_materia}'.")
                return [SlotSet("flujo_actual", None)]

            # Calcular estadísticas de asistencia
            clases_asistidas = 0
            clases_ausentes = 0

            for registro in asistencia_resp.data:
                asistio = registro.get("is_present", False)
                if asistio:
                    clases_asistidas += 1
                else:
                    clases_ausentes += 1

            # Calcular el porcentaje de asistencia usando la fórmula
            # Porcentaje de asistencia = (Clases asistidas / (Clases asistidas + Clases ausentes)) x 100
            total_clases = clases_asistidas + clases_ausentes

            if total_clases > 0:
                porcentaje_asistencia = (clases_asistidas / total_clases) * 100
                porcentaje_formateado = round(porcentaje_asistencia, 2)
            else:
                porcentaje_formateado = 0

            # Mostrar los resultados
            dispatcher.utter_message(f"📊 **Asistencia en {nombre_materia.upper()}:**")
            dispatcher.utter_message(f"🎓 Matrícula: {matricula}")
            dispatcher.utter_message(f"✅ Clases asistidas: {clases_asistidas}")
            dispatcher.utter_message(f"❌ Clases ausentes: {clases_ausentes}")
            dispatcher.utter_message(f"📅 Total de clases: {total_clases}")
            dispatcher.utter_message(f"📈 **Porcentaje de asistencia: {porcentaje_formateado}%**")

            # Agregar comentario sobre el rendimiento
            if porcentaje_formateado >= 80:
                dispatcher.utter_message("🎉 ¡Excelente asistencia! Mantén este buen rendimiento.")
            elif porcentaje_formateado >= 60:
                dispatcher.utter_message("⚠️ Tu asistencia es regular. Te recomiendo mejorar la asistencia a clases.")
            else:
                dispatcher.utter_message("🚨 Tu asistencia es baja. Es importante que asistas más a clases para mejorar tu rendimiento académico.")

            # # Mostrar la fórmula utilizada
            # dispatcher.utter_message(f"📝 **Fórmula utilizada:**")
            # dispatcher.utter_message(f"Porcentaje = ({clases_asistidas} / {total_clases}) × 100 = {porcentaje_formateado}%")

            return [SlotSet("flujo_actual", None), SlotSet("materia", None)]

        except Exception as e:
            print(f"Error al consultar asistencia: {e}")
            dispatcher.utter_message("❌ Hubo un error al consultar tu asistencia. Por favor, intenta nuevamente más tarde.")

        return []

class ActionConsultarFechasParciales(Action):

    def name(self):
        return "action_consultar_fechas_parciales"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain):
        # Verificar si el usuario está autenticado
        is_authenticated = tracker.get_slot('is_authenticated')

        if not is_authenticated:
            dispatcher.utter_message("❌ Necesitas estar autenticado para consultar las fechas de los parciales. Por favor, inicia sesión primero.")
            return []

        # Obtener la matrícula del slot
        matricula = tracker.get_slot('matricula')

        if not matricula:
            dispatcher.utter_message("❌ No tengo tu número de matrícula. Por favor, proporciona tu matrícula para poder consultar las fechas de los parciales.")
            return [SlotSet("flujo_actual", "consultar_fechas_parciales")]

        # Obtener la materia del slot
        materia = tracker.get_slot('materia')

        if not materia:
            dispatcher.utter_message("❌ No tengo la materia especificada. Por favor, dime de qué materia quieres consultar las fechas de los parciales.")
            return [SlotSet("flujo_actual", "consultar_fechas_parciales")]

        try:
            # Buscar el código de la materia por nombre
            materia_resp = supabase.table("Materia").select("codigo, nombre").ilike("nombre", "%" + materia + "%").execute()
            if not materia_resp.data:
                dispatcher.utter_message(f"❌ No se encontró la materia '{materia}' en la base de datos.")
                return [SlotSet("flujo_actual", None)]

            materia_codigo = materia_resp.data[0]["codigo"]
            # Buscar las fechas de los parciales
            fechas_parciales_resp = supabase.table("Parciales").select("*").eq("materia_codigo", materia_codigo).execute()

            if not fechas_parciales_resp.data:
                dispatcher.utter_message("❌ No se encontraron fechas de parciales registradas.")
                return [SlotSet("flujo_actual", None)]

            # Ordenar los parciales por fecha
            parciales_ordenados = sorted(fechas_parciales_resp.data, key=lambda x: x.get('fecha_parcial', ''))

            dispatcher.utter_message(f"📊 **Fechas de los parciales:**")

            for i, parcial in enumerate(parciales_ordenados, 1):
                fecha = parcial.get('fecha_parcial', 'Sin fecha')
                dispatcher.utter_message(f"• **Parcial nro {i} - {fecha}**")

            dispatcher.utter_message(f"✅ Total de parciales encontrados: {len(fechas_parciales_resp.data)}")
            return [SlotSet("flujo_actual", None), SlotSet("materia", None)]
        except Exception as e:
            print(f"Error al consultar fechas de parciales: {e}")
            dispatcher.utter_message("❌ Hubo un error al consultar las fechas de los parciales. Por favor, intenta nuevamente más tarde.")

        return []