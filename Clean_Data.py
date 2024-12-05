import os
import json
import gspread
import pandas as pd
import pycountry
import langcodes
import re
from langdetect import detect, LangDetectException
from oauth2client.service_account import ServiceAccountCredentials
from flask import Flask

app = Flask(__name__)

# Definir el alcance de las credenciales
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

# Fixer la graine pour des résultats cohérents dans langdetect
#DetectorFactory.seed = 0

google_credentials_json = os.getenv('GOOGLE_CREDENTIALS')

if google_credentials_json:
    # Cargar las credenciales desde el JSON que se obtiene de la variable de entorno
    creds_dict = json.loads(google_credentials_json)
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
else:
    print("No se encontraron las credenciales de Google en la variable de entorno.")

@app.route("/")
def home():
    return("app server is running")
@app.route("/clean", methods=["POST"])
def cleaning():
    # Leer los datos de la hoja de cálculo
    data = pd.DataFrame(worksheet1.get_all_records())

    # Verificar el cargado de los datos
    print("Données originales chargées :")
    print(data.head())  # Imprimir las primeras filas para verificación

    # Limpiar las columnas excepto las especiales
    for column in required_columns:
        if column not in special_columns:
            data[column] = data[column].apply(clean_text)

    # Escribir los datos limpios en la hoja 2
    worksheet2.clear()
    worksheet2.update([data.columns.values.tolist()] + data.values.tolist())

    # Mensaje de éxito
    return jsonify({"message": "Los datos han sido limpiados y actualizados en la hoja 2 con éxito."}), 200

# Abre la hoja de cálculo usando la URL
sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1klDIZ9ZBhmiUZ_FwS0DejKOl8iRph6ewW4C6JAUJ598/edit?usp=sharing")

# Acceder a la hoja 1 (index 0) para leer los datos originales
worksheet1 = sheet.get_worksheet(0)
data = pd.DataFrame(worksheet1.get_all_records())

# Verificar el cargado de los datos
print("Données originales chargées :")
print(data.head())  # Imprimir las primeras filas para verificación

# Columnas requeridas para filtrar
required_columns = [
    "Profile Url", "Full Name", "First Name", "Last Name", "Job Title", "Additional Info", 
    "Location", "Company", "Company Url", "Industry", "Company 2", "Company Url 2", 
    "Job Date Range", "Job Title 2", "Job Date Range 2", "School", "School Degree",
    "School Date Range", "School 2", "School Degree 2", "School Date Range 2"]

data = data[required_columns]

# Diccionario de reemplazo para corregir errores comunes de codificación
replacement_dict = {
    "Ã¡": "á", "Ã©": "é", "Ã­": "í", "Ã³": "ó", "Ãº": "ú",
    "Ã±": "ñ", "Ã": "Ñ", "â": "'", "â": "-", "Ã¼": "ü",
    "â€œ": "\"", "â€": "\"", "â€˜": "'", "â€¢": "-", "â‚¬": "€",
    "â„¢": "™", "âˆ’": "-", "Â": ""
}

# Columnas especiales donde no se aplica eliminación de caracteres especiales
special_columns = {"email", "mail", "linkedinProfile", "baseUrl", "professionalEmail"}

# Función para limpiar el texto en las columnas no especiales
def clean_text(text):
    if pd.isna(text):
        return ""
    text = str(text)  # Convertir en cadena para manejar valores no textuales
    for bad, good in replacement_dict.items():
        text = text.replace(bad, good)
    return re.sub(r'[^\w\s-]', '', text).strip()

# Limpiar las columnas excepto las especiales
for column in required_columns:
    if column not in special_columns:
        data[column] = data[column].apply(clean_text)

# Verificar las columnas después de limpiar
print("Données après le nettoyage :")
print(data.head())

# Función para obtener el idioma predeterminado de un país usando pycountry y langcodes
def get_language_from_country(country_name):
    try:
        country = pycountry.countries.lookup(country_name)
        language = langcodes.standardize_tag(langcodes.Language.get(country.alpha_2).language)
        return language
    except LookupError:
        return None

# Función para detectar el idioma basado en el texto o el país
def detect_language(description, headline, location):
    for text in [description, headline]:
        if text:
            try:
                return detect(text)
            except LangDetectException:
                continue
    for country in pycountry.countries:
        if country.name.lower() in location.lower():
            lang = get_language_from_country(country.name)
            if lang:
                return lang
    return "en"

# Aplicar la detección de idioma
'''data['language'] = data.apply(
    lambda row: detect_language(row['description'], row['headline'], row['location']),
    axis=1
)'''

# Verificar los datos después de la detección de idioma
print("Données après la détection de la langue :")
#print(data.head())

# Acceder a la hoja 2 (index 1) para escribir los datos limpiados
worksheet2 =  sheet.worksheet('Sheet6')
worksheet2.clear()

# Escribir los datos en la hoja 2
#worksheet2.update([data.columns.values.tolist()] + data.values.tolist())

print("Les données avec détection de langue ont été copiées et nettoyées avec succès dans la Feuille 2.")

if __name__ == '__main__':
    app.run(debug=True, port=5000)
