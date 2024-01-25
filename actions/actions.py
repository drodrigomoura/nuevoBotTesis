
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
        response = supabase.table("MateriaCursada").select('fecha_cursada, Materia(nombre)').eq("estudiante", matricula).execute()
        print(response)
        for materia in response.data:
            print(materia)
            dispatcher.utter_message("{}".format(materia))

        # dispatcher.utter_message("hola probando la custom action materias cursadas")
        return []

class ActionVerMesasExamen(Action):

    def name(self):
        return "action_mesas_examen"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain):
        response = supabase.table("MesaExamen").select('fecha, codigo,Materia(nombre)').execute()
        for materia in response.data:
            dispatcher.utter_message(json_message = materia)
            dispatcher.utter_message(buttons = [
                {"payload":  materia.get("codigo"), "title": materia.get("Materia").get("nombre"), "fecha de la mesa": materia.get("fecha")},
            ])
        return []