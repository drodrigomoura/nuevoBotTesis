#!/usr/bin/env python3
"""
Script para instalar el modelo de español de spaCy necesario para Rasa
"""

import subprocess
import sys
import os

def install_spacy_spanish():
    """Instala el modelo de español de spaCy"""
    print("Instalando modelo de español para spaCy...")
    
    try:
        # Instalar el modelo de español
        subprocess.check_call([
            sys.executable, "-m", "spacy", "download", "es_core_news_sm"
        ])
        print("✅ Modelo de español instalado correctamente")
        
        # Verificar la instalación
        subprocess.check_call([
            sys.executable, "-m", "spacy", "validate"
        ])
        print("✅ Validación de spaCy completada")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error al instalar el modelo: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        sys.exit(1)

if __name__ == "__main__":
    install_spacy_spanish() 