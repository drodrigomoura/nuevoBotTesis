
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

class ActionMaterias(Action):

    def name(self):
        return "action_materia"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain):
        matricula = tracker.get_slot('matricula')
        
        if not matricula:
            dispatcher.utter_message("❌ No tengo tu número de matrícula. Por favor, proporciona tu matrícula para poder consultar tus materias.")
            return []
        
        try:
            response = supabase.table("MateriaCursada").select('fecha_cursada, Materia(nombre)').eq("estudiante", matricula).execute()
            
            if not response.data:
                dispatcher.utter_message(f"📚 No se encontraron materias cursadas para la matrícula {matricula}.")
                return []
            
            dispatcher.utter_message(f"📚 **Materias cursadas para la matrícula {matricula}:**")
            
            for materia in response.data:
                nombre_materia = materia.get("Materia", {}).get("nombre", "Materia sin nombre")
                fecha_cursada = materia.get("fecha_cursada", "Fecha no disponible")
                
                dispatcher.utter_message(f"• **{nombre_materia}** - Cursada el: {fecha_cursada}")
            
            dispatcher.utter_message(f"✅ Total de materias encontradas: {len(response.data)}")
            
        except Exception as e:
            print(f"Error al consultar materias: {e}")
            dispatcher.utter_message("❌ Hubo un error al consultar tus materias. Por favor, intenta nuevamente más tarde.")
        
        return []

class ActionVerMesasExamen(Action):

    def name(self):
        return "action_mesas_examen"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain):
        materia = tracker.get_slot('materia')
        
        if not materia:
            dispatcher.utter_message("❌ No especificaste qué materia quieres consultar. Por favor, dime de qué materia necesitas ver las mesas de examen.")
            return []
        
        try:
            response = supabase.table("MesaExamen").select('fecha, codigo, Materia(nombre)').ilike("Materia.nombre", "%" + materia + "%").execute()
            
            if not response.data:
                dispatcher.utter_message(f"📅 No se encontraron mesas de examen para la materia '{materia}'.")
                return []
            
            dispatcher.utter_message(f"📅 **Mesas de examen disponibles para {materia.upper()}:**")
            
            for mesa in response.data:
                nombre_materia = mesa.get("Materia", {}).get("nombre", "Materia sin nombre")
                codigo_mesa = mesa.get("codigo", "Sin código")
                fecha_mesa = mesa.get("fecha", "Fecha no disponible")
                
                dispatcher.utter_message(f"• **{nombre_materia}**")
                dispatcher.utter_message(f"  📋 Código: `{codigo_mesa}`")
                dispatcher.utter_message(f"  📅 Fecha: {fecha_mesa}")
            
            # Mostrar botones de inscripción solo al final
            if len(response.data) == 1:
                # Si solo hay una mesa, mostrar botón directo
                mesa = response.data[0]
                nombre_materia = mesa.get("Materia", {}).get("nombre", "Materia")
                codigo_mesa = mesa.get("codigo")
                dispatcher.utter_message(
                    buttons=[
                        {
                            "title": f"📝 Inscribirse a {nombre_materia}",
                            "payload": f"/codigo_mesa_examen{{\"codigo_mesa_examen\": \"{codigo_mesa}\"}}"
                        }
                    ]
                )
            else:
                # Si hay múltiples mesas, mostrar opciones
                dispatcher.utter_message("📝 **¿Te gustaría inscribirte a alguna de estas mesas?**")
                for mesa in response.data:
                    nombre_materia = mesa.get("Materia", {}).get("nombre", "Materia")
                    codigo_mesa = mesa.get("codigo")
                    dispatcher.utter_message(
                        buttons=[
                            {
                                "title": f"Inscribirse a {nombre_materia}",
                                "payload": f"/codigo_mesa_examen{{\"codigo_mesa_examen\": \"{codigo_mesa}\"}}"
                            }
                        ]
                    )
            
            dispatcher.utter_message(f"✅ Se encontraron {len(response.data)} mesa(s) de examen para {materia.upper()}")
            dispatcher.utter_message("💡 **Nota:** Puedes consultar las fechas sin inscribirte. Los botones de inscripción son opcionales.")
            
        except Exception as e:
            print(f"Error al consultar mesas de examen: {e}")
            dispatcher.utter_message("❌ Hubo un error al consultar las mesas de examen. Por favor, intenta nuevamente más tarde.")
        
        return []

class ActionInscripcionMesaExamen(Action):

    def name(self):
        return "action_inscripcion_mesa"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain):
        codigoMesa = tracker.get_slot('codigo_mesa_examen')
        matricula = tracker.get_slot('matricula')
        
        if not matricula:
            dispatcher.utter_message("❌ No tengo tu número de matrícula. Por favor, proporciona tu matrícula para poder inscribirte a la mesa de examen.")
            return []
        
        if not codigoMesa:
            dispatcher.utter_message("❌ No tengo el código de la mesa de examen. Por favor, selecciona una mesa de examen para inscribirte.")
            return []
        
        try:
            # Primero verificar que la mesa de examen existe
            mesa_response = supabase.table("MesaExamen").select('fecha, Materia(nombre)').eq("codigo", codigoMesa).execute()
            
            if not mesa_response.data:
                dispatcher.utter_message(f"❌ No se encontró una mesa de examen con el código '{codigoMesa}'.")
                return []
            
            mesa_info = mesa_response.data[0]
            nombre_materia = mesa_info.get("Materia", {}).get("nombre", "Materia sin nombre")
            fecha_mesa = mesa_info.get("fecha", "Fecha no disponible")
            
            # Verificar si ya está inscrito
            inscripcion_existente = supabase.table("InscripcionMesa").select('*').eq("estudiante", matricula).eq("mesa_examen", codigoMesa).execute()
            
            if inscripcion_existente.data:
                dispatcher.utter_message(f"⚠️ Ya estás inscrito a la mesa de examen de **{nombre_materia}** (código: {codigoMesa}) que se realizará el {fecha_mesa}.")
                return []
            
            # Realizar la inscripción
            inscripcion_data = {
                "estudiante": matricula,
                "mesa_examen": codigoMesa,
                "fecha_inscripcion": "now()"
            }
            
            insert_response = supabase.table("InscripcionMesa").insert(inscripcion_data).execute()
            
            if insert_response.data:
                dispatcher.utter_message(f"✅ **¡Inscripción exitosa!**")
                dispatcher.utter_message(f"📚 Materia: **{nombre_materia}**")
                dispatcher.utter_message(f"📋 Código de mesa: `{codigoMesa}`")
                dispatcher.utter_message(f"📅 Fecha del examen: {fecha_mesa}")
                dispatcher.utter_message(f"🎓 Matrícula: {matricula}")
                dispatcher.utter_message("📝 Recuerda presentarte con tu DNI y los materiales necesarios para el examen.")
            else:
                dispatcher.utter_message("❌ Hubo un problema al procesar tu inscripción. Por favor, intenta nuevamente.")
                
        except Exception as e:
            print(f"Error al inscribir a mesa de examen: {e}")
            dispatcher.utter_message("❌ Hubo un error al procesar tu inscripción. Por favor, intenta nuevamente más tarde.")
        
        return []

class ActionCancelarInscripcionMesa(Action):

    def name(self):
        return "action_cancelar_inscripcion_mesa"

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
            # Primero buscar las mesas de examen para la materia
            mesa_response = supabase.table("MesaExamen").select('codigo, Materia(nombre)').ilike("Materia.nombre", "%" + materia + "%").execute()
            
            if not mesa_response.data:
                dispatcher.utter_message(f"❌ No se encontraron mesas de examen para la materia '{materia}'.")
                return []
            
            # Buscar todas las inscripciones del estudiante para las mesas de esa materia
            inscripciones_canceladas = 0
            for mesa in mesa_response.data:
                codigo_mesa = mesa.get("codigo")
                nombre_materia = mesa.get("Materia", {}).get("nombre", "Materia")
                
                # Buscar la inscripción específica
                inscripcion_response = supabase.table("InscripcionMesa").select('*').eq("estudiante", matricula).eq("mesa_examen", codigo_mesa).execute()
                
                if inscripcion_response.data:
                    # Eliminar la inscripción
                    delete_response = supabase.table("InscripcionMesa").delete().eq("estudiante", matricula).eq("mesa_examen", codigo_mesa).execute()
                    
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