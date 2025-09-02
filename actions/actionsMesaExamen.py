from builtins import print
from typing import Any, Text, Dict, List
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk import Action, Tracker, FormValidationAction
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

class ActionVerMesasExamen(Action):

    def name(self):
        return "action_consultar_mesas_examen"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain):
        is_authenticated = tracker.get_slot('is_authenticated')
        if not is_authenticated:
            dispatcher.utter_message("❌ Necesitas estar autenticado para consultar las mesas de examen. Por favor, inicia sesión primero.")
            return []

        materia = tracker.get_slot('materia')
        if not materia:
            dispatcher.utter_message("❌ No especificaste qué materia quieres consultar. Por favor, dime de qué materia necesitas ver las mesas de examen.")
            return []

        try:
            # 1. Buscar el código de la materia
            materia_resp = supabase.table("Materia").select("codigo, nombre").ilike("nombre", "%" + materia + "%").execute()
            if not materia_resp.data:
                dispatcher.utter_message(f"❌ No se encontró la materia '{materia}' en la base de datos.")
                return []

            materia_codigo = materia_resp.data[0]["codigo"]
            nombre_materia = materia_resp.data[0]["nombre"]

            # 2. Buscar las mesas de examen con ese código de materia
            mesas_resp = supabase.table("MesaExamen").select('fecha, codigo').eq("materia_codigo", materia_codigo).execute()
            if not mesas_resp.data:
                dispatcher.utter_message(f"📅 No se encontraron mesas de examen para la materia '{nombre_materia}'.")
                return []

            dispatcher.utter_message(f"📅 **Mesas de examen disponibles para {nombre_materia.upper()}:**")
            for idx, mesa in enumerate(mesas_resp.data, 1):
                codigo_mesa = mesa.get("codigo", "Sin código")
                fecha_mesa = mesa.get("fecha", "Fecha no disponible")
                dispatcher.utter_message(
                    f"-----------------------------\n"
                    f"📝 Mesa #{idx}\n"
                    f"📋 Código: `{codigo_mesa}`\n"
                    f"📅 Fecha: {fecha_mesa}\n"
                    f"-----------------------------"
                )
            dispatcher.utter_message(f"✅ Se encontraron {len(mesas_resp.data)} mesa(s) de examen para {nombre_materia.upper()}")
            dispatcher.utter_message("💡 **Nota:** Estas son las fechas disponibles para la materia consultada.")
            return [SlotSet("materia", None)]

        except Exception as e:
            print(f"Error al consultar mesas de examen: {e}")
            dispatcher.utter_message("❌ Hubo un error al consultar las mesas de examen. Por favor, intenta nuevamente más tarde.")

        return []

class ActionOfrecerMesasExamen(Action):
    def name(self):
        return "action_ofrecer_mesas_examen"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain):
        is_authenticated = tracker.get_slot('is_authenticated')
        if not is_authenticated:
            dispatcher.utter_message("❌ Necesitas estar autenticado para consultar e inscribirte a una mesa de examen. Por favor, inicia sesión primero.")
            return []

        matricula = tracker.get_slot('matricula')
        materia = tracker.get_slot('materia')

        if not matricula:
            dispatcher.utter_message("❌ No tengo tu número de matrícula. Por favor, proporciona tu matrícula para poder continuar.")
            return [SlotSet("flujo_actual", "inscripcion_mesa_examen")]
        if not materia:
            dispatcher.utter_message("❌ No tengo la materia especificada. Por favor, dime a qué materia quieres inscribirte para la mesa de examen.")
            return [SlotSet("flujo_actual", "inscripcion_mesa_examen")]
        try:
            materia_resp = supabase.table("Materia").select("codigo, nombre").ilike("nombre", "%" + materia + "%").execute()
            if not materia_resp.data:
                dispatcher.utter_message(f"❌ No se encontró la materia '{materia}' en la base de datos.")
                return []
            materia_codigo = materia_resp.data[0]["codigo"]
            nombre_materia = materia_resp.data[0]["nombre"]

            mesas_resp = supabase.table("MesaExamen").select('fecha, codigo').eq("materia_codigo", materia_codigo).order("fecha", desc=False).execute()
            if not mesas_resp.data:
                dispatcher.utter_message(f"📅 No se encontraron mesas de examen para la materia '{nombre_materia}'.")
                return []

            dispatcher.utter_message(f"📅 **Mesas de examen disponibles para {nombre_materia.upper()}:**")
            mesas_list = []
            for idx, mesa in enumerate(mesas_resp.data, 1):
                codigo_mesa = mesa.get("codigo", "Sin código")
                fecha_mesa = mesa.get("fecha", "Fecha no disponible")
                mesas_list.append({"codigo": codigo_mesa, "fecha": fecha_mesa})
                dispatcher.utter_message(
                    f"-----------------------------\n"
                    f"📝 Mesa #{idx}\n"
                    f"📋 Código: `{codigo_mesa}`\n"
                    f"📅 Fecha: {fecha_mesa}\n"
                    f"-----------------------------"
                )
            # Mantener la materia para el flujo de formularios, solo limpiar flujo_actual
            return [SlotSet("flujo_actual", None)]
        except Exception as e:
            print(f"Error al ofrecer mesas de examen: {e}")
            dispatcher.utter_message("❌ Hubo un error al consultar las mesas de examen. Por favor, intenta nuevamente más tarde.")
        return []

# Modificar ActionInscripcionMesaExamen para solo inscribir si ya hay código de mesa seleccionado
def _find_mesa_by_codigo(codigo_mesa):
    try:
        mesa_response = supabase.table("MesaExamen").select('fecha, Materia(nombre)').eq("codigo", codigo_mesa).execute()
        if mesa_response.data:
            return mesa_response.data[0]
    except Exception as e:
        print(f"Error buscando mesa por código: {e}")
    return None

class ActionInscripcionMesaExamen(Action):
    def name(self):
        return "action_inscripcion_mesa_examen"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain):
        is_authenticated = tracker.get_slot('is_authenticated')
        if not is_authenticated:
            dispatcher.utter_message("❌ Necesitas estar autenticado para inscribirte a una mesa de examen. Por favor, inicia sesión primero.")
            return []
        matricula = tracker.get_slot('matricula')
        codigo_mesa = tracker.get_slot('codigo_mesa_examen')
        fecha_mesa = tracker.get_slot('fecha_mesa')
        materia = tracker.get_slot('materia')
        if not matricula:
            dispatcher.utter_message("❌ No tengo tu número de matrícula. Por favor, proporciona tu matrícula para poder inscribirte a la mesa de examen.")
            return []
        # Si no hay código pero sí fecha, buscar el código de la mesa para esa fecha y materia
        if not codigo_mesa and fecha_mesa and materia:
            try:
                materia_resp = supabase.table("Materia").select("codigo").ilike("nombre", "%" + materia + "%").execute()
                if not materia_resp.data:
                    dispatcher.utter_message(f"❌ No se encontró la materia '{materia}' en la base de datos.")
                    return []
                materia_codigo = materia_resp.data[0]["codigo"]
                mesa_resp = supabase.table("MesaExamen").select('codigo').eq("materia_codigo", materia_codigo).eq("fecha", fecha_mesa).execute()
                if not mesa_resp.data:
                    dispatcher.utter_message(f"❌ No se encontró una mesa de examen para la materia '{materia}' en la fecha '{fecha_mesa}'.")
                    return []
                codigo_mesa = mesa_resp.data[0]["codigo"]
            except Exception as e:
                print(f"Error buscando mesa por fecha: {e}")
                dispatcher.utter_message("❌ Hubo un error al buscar la mesa de examen por fecha. Por favor, intenta nuevamente más tarde.")
                return []
        if not codigo_mesa:
            dispatcher.utter_message("❌ No tengo el código de la mesa de examen. Por favor, selecciona una mesa de examen para inscribirte (puedes consultarlas primero).")
            return []
        try:
            mesa_info = _find_mesa_by_codigo(codigo_mesa)
            if not mesa_info:
                dispatcher.utter_message(f"❌ No se encontró una mesa de examen con el código '{codigo_mesa}'.")
                return []
            nombre_materia = mesa_info.get("Materia", {}).get("nombre", "Materia sin nombre")
            fecha_mesa_final = mesa_info.get("fecha", "Fecha no disponible")
            # Verificar si ya está inscrito
            inscripcion_existente = supabase.table("Inscripcion").select('*').eq("estudiante", matricula).eq("codigo_mesa", codigo_mesa).execute()
            if inscripcion_existente.data:
                dispatcher.utter_message(f"⚠️ Ya estás inscrito a la mesa de examen de **{nombre_materia}** (código: {codigo_mesa}) que se realizará el {fecha_mesa_final}.")
                return [SlotSet("flujo_actual", None), SlotSet("materia", None), SlotSet("fecha_mesa", None), SlotSet("codigo_mesa_examen", None)]
            # Realizar la inscripción
            inscripcion_data = {
                "estudiante": matricula,
                "codigo_mesa": codigo_mesa,
                "fecha_inscripcion": "now()"
            }
            print(f"[LOG] matricula: {matricula}")
            print(f"[LOG] codigo_mesa: {codigo_mesa}")
            print(f"[LOG] fecha_inscripcion: {inscripcion_data['fecha_inscripcion']}")
            insert_response = supabase.table("Inscripcion").insert(inscripcion_data).execute()
            if insert_response.data:
                dispatcher.utter_message(f"✅ **¡Inscripción exitosa!**")
                dispatcher.utter_message(f"📚 Materia: **{nombre_materia}**")
                dispatcher.utter_message(f"📋 Código de mesa: `{codigo_mesa}`")
                dispatcher.utter_message(f"📅 Fecha del examen: {fecha_mesa_final}")
                dispatcher.utter_message(f"🎓 Matrícula: {matricula}")
                dispatcher.utter_message("📝 Recuerda presentarte con tu libreta y los materiales necesarios para el examen.")
                return [SlotSet("flujo_actual", None), SlotSet("materia", None), SlotSet("fecha_mesa", None), SlotSet("codigo_mesa_examen", None)]
            else:
                dispatcher.utter_message("❌ Hubo un problema al procesar tu inscripción. Por favor, intenta nuevamente.")
        except Exception as e:
            print(f"Error al inscribir a mesa de examen: {e}")
            dispatcher.utter_message("❌ Hubo un error al procesar tu inscripción. Por favor, intenta nuevamente más tarde.")
        return []

class ActionCancelarInscripcionMesa(Action):

    def name(self):
        return "action_cancelar_inscripcion_mesa_examen"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain):
        materia = tracker.get_slot('materia')
        matricula = tracker.get_slot('matricula')
        
        if not matricula:
            dispatcher.utter_message("❌ No tengo tu número de matrícula. Por favor, proporciona tu matrícula para poder cancelar la inscripción.")
            return []
        
        if not materia:
            dispatcher.utter_message("❌ No tengo la materia especificada. Por favor, dime de qué materia quieres cancelar la inscripción.")
            return []
        
        try:
            # Primero buscar el código de la materia
            materia_resp = supabase.table("Materia").select("codigo, nombre").ilike("nombre", "%" + materia + "%").execute()
            if not materia_resp.data:
                dispatcher.utter_message(f"❌ No se encontró la materia '{materia}' en la base de datos.")
                return []
            
            materia_codigo = materia_resp.data[0]["codigo"]
            nombre_materia = materia_resp.data[0]["nombre"]
            
            # Buscar las mesas de examen para esa materia específica
            mesa_response = supabase.table("MesaExamen").select('codigo').eq("materia_codigo", materia_codigo).execute()
            
            print(f"Mesas encontradas para {nombre_materia}: {mesa_response.data}")
            if not mesa_response.data:
                dispatcher.utter_message(f"❌ No se encontraron mesas de examen para la materia '{materia}'.")
                return []
            
            # Buscar todas las inscripciones del estudiante para las mesas de esa materia
            inscripciones_canceladas = 0
            for mesa in mesa_response.data:
                codigo_mesa = mesa.get("codigo")
                
                # Buscar la inscripción específica
                inscripcion_response = supabase.table("Inscripcion").select('*').eq("estudiante", matricula).eq("codigo_mesa", codigo_mesa).execute()
                
                print(inscripcion_response.data)
                if inscripcion_response.data:
                    # Eliminar la inscripción
                    delete_response = supabase.table("Inscripcion").delete().eq("estudiante", matricula).eq("codigo_mesa", codigo_mesa).execute()
                    
                    if delete_response.data:
                        inscripciones_canceladas += 1
                        dispatcher.utter_message(f"✅ Tu inscripción a la mesa de examen de {nombre_materia} (código: {codigo_mesa}) ha sido cancelada exitosamente.")
            
            if inscripciones_canceladas == 0:
                dispatcher.utter_message(f"❌ No se encontró una inscripción activa para la matrícula {matricula} en ninguna mesa de examen de la materia '{materia}'.")
            elif inscripciones_canceladas == 1:
                dispatcher.utter_message("✅ Cancelación completada.")
            else:
                dispatcher.utter_message(f"✅ Se cancelaron {inscripciones_canceladas} inscripciones.")
                
        except Exception as e:
            print(f"Error al cancelar inscripción: {e}")
            dispatcher.utter_message("❌ Hubo un error al procesar la cancelación. Por favor, intenta nuevamente más tarde.")
        
        return []

class ValidateSeleccionarMesaForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_seleccionar_mesa_form"

    def validate_codigo_mesa_examen(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        import re
        
        print(f"DEBUG: Validando codigo_mesa_examen con valor: '{slot_value}'")
        
        # Verificar si hay entidades extraídas por NLU
        entities = tracker.latest_message.get('entities', [])
        
        # Buscar si hay una entidad fecha_mesa
        for entity in entities:
            if entity.get('entity') == 'fecha_mesa':
                fecha_valor = entity.get('value')
                print(f"DEBUG: Entidad fecha detectada por NLU: {fecha_valor}")
                return {"codigo_mesa_examen": None, "fecha_mesa": fecha_valor}
        
        # Si no hay entidad fecha, verificar con regex como fallback
        if slot_value and re.match(r'^\d{4}-\d{2}-\d{2}$', slot_value):
            print(f"DEBUG: Fecha detectada por regex: {slot_value}")
            return {"codigo_mesa_examen": None, "fecha_mesa": slot_value}
        
        # Si es un código válido
        if slot_value:
            print(f"DEBUG: Código detectado: {slot_value}")
            return {"codigo_mesa_examen": slot_value}
        
        print(f"DEBUG: Valor vacío o inválido")
        return {"codigo_mesa_examen": None}

    def validate_fecha_mesa(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        print(f"DEBUG: Validando fecha_mesa con valor: '{slot_value}'")
        # Si ya tenemos fecha, limpiar código
        if slot_value:
            print(f"DEBUG: Fecha validada: {slot_value}")
            return {"fecha_mesa": slot_value, "codigo_mesa_examen": None}
        return {"fecha_mesa": None}

    async def required_slots(
        self,
        domain_slots: List[Text],
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Text]:
        # Verificar si ya tenemos uno de los dos valores
        codigo_mesa = tracker.get_slot("codigo_mesa_examen")
        fecha_mesa = tracker.get_slot("fecha_mesa")
        
        print(f"DEBUG: required_slots - codigo_mesa: {codigo_mesa}, fecha_mesa: {fecha_mesa}")
        
        # Si tenemos alguno de los dos, formulario completo
        if codigo_mesa or fecha_mesa:
            print("DEBUG: Formulario completo, no se requieren más slots")
            return []
        
        # Por defecto, pedimos código primero (que puede ser código o fecha)
        print("DEBUG: Solicitando codigo_mesa_examen")
        return ["codigo_mesa_examen"]
    
    async def submit(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict]:
        print("DEBUG: Formulario submit ejecutado")
        # El formulario está completo, no hacer nada aquí
        # La regla se encargará de ejecutar action_inscripcion_mesa_examen
        return []
