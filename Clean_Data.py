# Importer les bibliothèques nécessaires
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import re
from langdetect import detect, DetectorFactory
from langdetect.lang_detect_exception import LangDetectException

# Fixer la graine pour des résultats cohérents avec langdetect
DetectorFactory.seed = 0

# Authentification avec Google Sheets
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
# Charger les informations d'identification depuis le fichier JSON
creds = ServiceAccountCredentials.from_json_keyfile_name('awesome-height-441419-j4-5f2808cabaf5.json', scope)
client = gspread.authorize(creds)

# Ouvrir la première feuille Google Sheets pour lire les données
sheet_input = client.open_by_url("https://docs.google.com/spreadsheets/d/1eZs3-64SL92NrcmViDehMDTn8fIJTdCZqvsshQT1nekk/edit?usp=sharing")
worksheet1 = sheet_input.get_worksheet(0)  # Accéder à la première feuille (index 0)
data = pd.DataFrame(worksheet1.get_all_records())  # Lire toutes les données sous forme de DataFrame

# Filtrer les colonnes nécessaires
required_columns = [
    "firstName", "lastName", "fullName", "linkedinProfile", "headline", "email",
    "phone", "phonework", "location", "company", "jobTitle", "jobDescription",
    "jobLocation", "baseUrl", "professionalEmail", "description"
]
data = data[[col for col in required_columns if col in data.columns]]

# Ajouter la colonne 'Nro' qui compte le numéro de chaque ligne
data['Nro'] = range(1, len(data) + 1)

# Dictionnaire pour corriger les erreurs courantes de codage des caractères
replacement_dict = {
    "Ã¡": "á", "Ã©": "é", "Ã­": "í", "Ã³": "ó", "Ãº": "ú",
    "Ã±": "ñ", "Ã": "Ñ", "â": "'", "â": "-", "Ã¼": "ü",
    "â€œ": "\"", "â€": "\"", "â€˜": "'", "â€¢": "-", "â‚¬": "€",
    "â„¢": "™", "âˆ’": "-", "Â": ""
}

# Fonction pour nettoyer le texte
def clean_text(text):
    if pd.isna(text):  # Vérifier si le texte est NaN
        return ""
    for bad, good in replacement_dict.items():  # Remplacer les caractères erronés
        text = text.replace(bad, good)
    return re.sub(r'[^\w\s-]', '', text).strip()  # Supprimer les caractères indésirables

# Appliquer la fonction de nettoyage sur les colonnes nécessaires
special_columns = {"email", "linkedinProfile", "baseUrl", "professionalEmail"}
for column in required_columns:
    if column not in special_columns and column != "language":
        data[column] = data[column].apply(clean_text)

# Fonction pour détecter la langue à partir de la description
def detect_language(description):
    if description:
        try:
            return detect(description)
        except LangDetectException:
            return "unknown"  # Si la détection échoue
    return "unknown"  # Si la description est vide

# Appliquer la détection de langue et ajouter une colonne correspondante dans le DataFrame
data['language'] = data['description'].apply(detect_language)

# Ouvrir la deuxième feuille Google Sheets pour écrire les données nettoyées
sheet_output = client.open_by_url("https://docs.google.com/spreadsheets/d/1xRISBywX7X-tK3HSWeDlup-_VcFXc0dGwyarXvfMwCMk/edit?usp=sharing")
worksheet2 = sheet_output.get_worksheet(0)  # Accéder à la première feuille (index 0)

# Effacer le contenu de la feuille avant d'écrire de nouvelles données
worksheet2.clear()

# Écrire les données nettoyées et enrichies dans la feuille
worksheet2.update([data.columns.values.tolist()] + data.values.tolist())

print("Les données avec détection de langue ont été nettoyées, enrichies et copiées avec succès dans la feuille 2.")
