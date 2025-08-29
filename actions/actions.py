
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
            dispatcher.utter_message("Por favor, dime la fecha o el código de la mesa a la que deseas inscribirte.")
            # Limpiar el contexto porque ya se ofrecieron las mesas
            return [SlotSet("flujo_actual", None), SlotSet("materia", None)]
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
                return [SlotSet("flujo_actual", None), SlotSet("materia", None)]
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
                dispatcher.utter_message("📝 Recuerda presentarte con tu DNI y los materiales necesarios para el examen.")
                return [SlotSet("flujo_actual", None), SlotSet("materia", None)]
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

class ActionConsultarMaterias(Action):

    def name(self):
        return "action_consultar_materias"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain):
        # Verificar si el usuario está autenticado
        is_authenticated = tracker.get_slot('is_authenticated')

        if not is_authenticated:
            dispatcher.utter_message("❌ Necesitas estar autenticado para consultar tus materias. Por favor, inicia sesión primero.")
            return []

        # Obtener la matrícula del slot
        matricula = tracker.get_slot('matricula')

        if not matricula:
            dispatcher.utter_message("❌ No tengo tu número de matrícula. Por favor, proporciona tu matrícula para poder consultar tus materias.")
            return [SlotSet("flujo_actual", "consultar_materias")]

        try:
            response = supabase.table("MateriaCursada").select('fecha_cursada, Materia(nombre)').eq("estudiante", matricula).execute()

            if not response.data:
                dispatcher.utter_message(f"📚 No se encontraron materias cursadas para la matrícula {matricula}.")
                return [SlotSet("flujo_actual", None)]

            dispatcher.utter_message(f"📚 **Materias cursadas para la matrícula {matricula}:**")

            for materia in response.data:
                nombre_materia = materia.get("Materia", {}).get("nombre", "Materia sin nombre")
                fecha_cursada = materia.get("fecha_cursada", "Fecha no disponible")

                dispatcher.utter_message(f"• **{nombre_materia}** - Cursada el: {fecha_cursada}")

            dispatcher.utter_message(f"✅ Total de materias encontradas: {len(response.data)}")
            return [SlotSet("flujo_actual", None), SlotSet("materia", None)]
        except Exception as e:
            print(f"Error al consultar materias: {e}")
            dispatcher.utter_message("❌ Hubo un error al consultar tus materias. Por favor, intenta nuevamente más tarde.")

        return []

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

class ActionConsultarNotas(Action):

    def name(self):
        return "action_consultar_notas"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain):
        # Verificar si el usuario está autenticado
        is_authenticated = tracker.get_slot('is_authenticated')

        if not is_authenticated:
            dispatcher.utter_message("❌ Necesitas estar autenticado para consultar tus notas. Por favor, inicia sesión primero.")
            return []

        # Obtener la matrícula del slot
        matricula = tracker.get_slot('matricula')

        if not matricula:
            dispatcher.utter_message("❌ No tengo tu número de matrícula. Por favor, proporciona tu matrícula para poder consultar tus notas.")
            return [SlotSet("flujo_actual", "consultar_notas")]

        # Convertir matrícula a entero
        try:
            matricula = int(matricula)
        except ValueError:
            dispatcher.utter_message("❌ El número de matrícula debe ser un número válido.")
            return []

        # Obtener la materia del slot
        materia = tracker.get_slot('materia')
        print(f"[LOG] Consultando notas para matrícula: {matricula}, materia: {materia}")
        if not materia:
            dispatcher.utter_message("❌ No tengo la materia especificada. Por favor, dime de qué materia quieres consultar las notas.")
            return [SlotSet("flujo_actual", "consultar_notas")]
        try:
            materia_codigo = None
            if materia:
                # Buscar el id de la materia por nombre
                materia_resp = supabase.table("Materia").select("codigo, nombre").ilike("nombre", "%" + materia + "%").execute()
                print(f"[LOG] Materia encontrada: {materia_resp.data}")
                if materia_resp.data:
                    materia_codigo = materia_resp.data[0]["codigo"]
                else:
                    dispatcher.utter_message(f"❌ No se encontró la materia '{materia}' en la base de datos.")
                    return [SlotSet("flujo_actual", None)]

            # Buscar las notas usando el id de la materia si está disponible
            print(f"[LOG] Materia codigo: {materia_codigo}")
            print(f"[LOG] Matricula: {matricula}")

            if materia_codigo:
                # Usar query SQL directa con .from_()
                sql_query = f"SELECT * FROM public.\"Notas\" WHERE materia_codigo = '{materia_codigo}' AND estudiante_id = {matricula}"
                print(f"[LOG] SQL Query: {sql_query}")
                response = supabase.from_('Notas').select("*").eq("materia_codigo", materia_codigo).eq("estudiante_id", matricula).execute()
            else:
                # Consulta sin filtro de materia
                sql_query = f"SELECT * FROM public.\"Notas\" WHERE estudiante_id = {matricula}"
                print(f"[LOG] SQL Query: {sql_query}")
                response = supabase.from_('Notas').select("*").eq("estudiante_id", matricula).execute()

            print(f"[LOG] Response: {response}")
            print(f"[LOG] Response data: {response.data}")
            print(f"[LOG] Response data length: {len(response.data) if response.data else 0}")

            # Verificar si hay errores en la respuesta
            if hasattr(response, 'error') and response.error:
                print(f"[LOG] Supabase error: {response.error}")

            # Si no hay datos, probar una consulta simple sin filtros
            if not response.data:
                print(f"[LOG] Probando consulta simple sin filtros...")
                try:
                    simple_response = supabase.from_('Notas').select("*").limit(5).execute()
                    print(f"[LOG] Simple response: {simple_response.data}")
                    print(f"[LOG] Simple response length: {len(simple_response.data) if simple_response.data else 0}")
                except Exception as e:
                    print(f"[LOG] Error en consulta simple: {e}")

            if not response.data:
                if materia:
                    dispatcher.utter_message(f"📊 No se encontraron notas registradas para la matrícula {matricula} en la materia '{materia}'.")
                else:
                    dispatcher.utter_message(f"📊 No se encontraron notas registradas para la matrícula {matricula}.")
                return [SlotSet("flujo_actual", None)]

            # Mostrar el título según si se especificó materia o no
            if materia:
                dispatcher.utter_message(f"📊 **Notas de {materia.upper()} para la matrícula {matricula}:**")
            else:
                dispatcher.utter_message(f"📊 **Todas las notas para la matrícula {matricula}:**")

            for nota in response.data:
                calificacion = nota.get("nota", "Sin calificar")
                fecha_nota = nota.get("created_at", "Fecha no disponible")
                descripcion = nota.get("descripcion", "Sin descripción")
                # Formatear la nota con emoji según la calificación
                if isinstance(calificacion, (int, float)):
                    if calificacion >= 7:
                        emoji = "🟢"
                    elif calificacion >= 4:
                        emoji = "🟡"
                    else:
                        emoji = "🔴"
                    nota_formateada = f"{emoji} {calificacion}/10"
                else:
                    nota_formateada = f"📝 {calificacion}"
                dispatcher.utter_message(f"• {nota_formateada} - {descripcion} - Fecha: {fecha_nota}")

            dispatcher.utter_message(f"✅ Total de notas encontradas: {len(response.data)}")
            return [SlotSet("flujo_actual", None), SlotSet("materia", None)]
        except Exception as e:
            print(f"Error al consultar notas: {e}")
            dispatcher.utter_message("❌ Hubo un error al consultar tus notas. Por favor, intenta nuevamente más tarde.")

        return []

class ActionConsultarRequerimientosMateria(Action):

    def name(self):
        return "action_consultar_requerimientos_materia"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain):
        # Verificar si el usuario está autenticado
        is_authenticated = tracker.get_slot('is_authenticated')

        if not is_authenticated:
            dispatcher.utter_message("❌ Necesitas estar autenticado para consultar los requerimientos de las materias. Por favor, inicia sesión primero.")
            return []

        # Obtener la matrícula del slot
        matricula = tracker.get_slot('matricula')

        if not matricula:
            dispatcher.utter_message("❌ No tengo tu número de matrícula. Por favor, proporciona tu matrícula para poder consultar los requerimientos de las materias.")
            return [SlotSet("flujo_actual", "consultar_requerimientos_materia")]

        # Obtener la materia del slot
        materia = tracker.get_slot('materia')

        if not materia:
            dispatcher.utter_message("❌ No tengo la materia especificada. Por favor, dime de qué materia quieres consultar los requerimientos.")
            return [SlotSet("flujo_actual", "consultar_requerimientos_materia")]

        try:
            # Buscar el id de la materia por nombre
            materia_resp = supabase.table("Materia").select("codigo, nombre").ilike("nombre", "%" + materia + "%").execute()
            if not materia_resp.data:
                dispatcher.utter_message(f"❌ No se encontró la materia '{materia}' en la base de datos.")
                return [SlotSet("flujo_actual", None)]

            materia_codigo = materia_resp.data[0]["codigo"]

            # Buscar los requerimientos de la materia
            requerimientos_resp = supabase.table("MateriaEquivalencia").select('*, Materia!MateriaEquivalencia_equivalencia_id_fkey(nombre)').eq("materia_codigo", materia_codigo).execute()

            if not requerimientos_resp.data:
                dispatcher.utter_message(f"❌ No se encontraron requerimientos para la materia '{materia}'.")
                return [SlotSet("flujo_actual", None)]

            dispatcher.utter_message(f"📊 **Requerimientos de {materia.upper()}:**")

            for requerimiento in requerimientos_resp.data:
                nombre_materia_equivalencia = requerimiento.get("Materia", {}).get("nombre", "Materia sin nombre")
                dispatcher.utter_message(f"• **{nombre_materia_equivalencia}**")

            dispatcher.utter_message(f"✅ Total de requerimientos encontrados: {len(requerimientos_resp.data)}")
            return [SlotSet("flujo_actual", None), SlotSet("materia", None)]
        except Exception as e:
            print(f"Error al consultar requerimientos de la materia: {e}")
            dispatcher.utter_message("❌ Hubo un error al consultar los requerimientos de la materia. Por favor, intenta nuevamente más tarde.")

        return []

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

            dispatcher.utter_message(f"📊 **Fechas de los parciales:**")

            for parcial in fechas_parciales_resp.data:
                dispatcher.utter_message(f"• **{parcial.get('fecha', 'Parcial sin fecha')}**")

            dispatcher.utter_message(f"✅ Total de parciales encontrados: {len(fechas_parciales_resp.data)}")
            return [SlotSet("flujo_actual", None), SlotSet("materia", None)]
        except Exception as e:
            print(f"Error al consultar fechas de parciales: {e}")
            dispatcher.utter_message("❌ Hubo un error al consultar las fechas de los parciales. Por favor, intenta nuevamente más tarde.")

        return []