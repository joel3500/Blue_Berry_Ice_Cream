# -*- coding: utf-8 -*-
import os
import json
import base64  # (utile si jamais tu veux basculer en b64)
import requests
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

# ========================= Configuration ========================= #
load_dotenv()

API_KEY = (
    os.getenv("OPENAI_API_KEY_1")
    or os.getenv("OPENAI_API_KEY_2")
    or os.getenv("OPENAI_API_KEY_3")
)
if not API_KEY:
    raise RuntimeError("Aucune clé API trouvée dans .env (OPENAI_API_KEY).")

# Client OpenAI (SDK >= 1.x)
client = OpenAI(api_key=API_KEY)

IMAGE_MODEL = os.getenv("OPENAI_IMAGE_MODEL", "gpt-image-1")

IMAGE_SIZE = os.getenv("OPENAI_IMAGE_SIZE", "1024x1024" or "1024x1536" or "1536x1024" or "auto")
# valeurs valides: "1024x1024" | "1024x1536" | "1536x1024" | "auto"

BASE_DIR = Path(__file__).resolve().parent
JSON_PATH = BASE_DIR / "poissons.json"
IMAGES_DIR = BASE_DIR / "images_poissons"

# ===================== Extraction JSON + Affichage ===================== #
def extraction_et_affichage_Donnes_JSON(fichier_json: Path):
    try:
        with fichier_json.open("r", encoding="utf-8") as f:
            data = json.load(f)
        print("+---------------- Affichage JSON ----------------+")
        print(json.dumps(data, indent=4, ensure_ascii=False))
        return data
    except FileNotFoundError:
        print(f"[ERREUR] Fichier introuvable : {fichier_json}")
        print(f"[DEBUG] cwd = {Path.cwd()}")
        return None

def affichage_List(data):
    print("+----------- Liste de tous les poissons -----------+")
    poissons = data.get("poissons", [])
    print(json.dumps(poissons, indent=4, ensure_ascii=False))
    return poissons

def affichage_List_des_noms(poissons):
    print("+------ Noms des poissons présents dans le JSON ------+")
    noms = [poisson.get("nom", "Nom inconnu") for poisson in poissons]
    for nom in noms:
        print(nom)
    return noms

# ========================= Génération d’image ========================= #
def generer_image_article(le_poisson):
    """
    Retourne un tuple: ("url", <str URL>) OU ("b64", <str base64>).
    """
    prompt = (
        f"Une belle présentation de {le_poisson.get('nom','un poisson')}, "
        f"{le_poisson.get('morphologie_1','')}, "
        f"{le_poisson.get('morphologie_2','')}, "
        f"{le_poisson.get('morphologie_3','')}, "
        f"{le_poisson.get('morphologie_4','')}."
    )
    try:
        resp = client.images.generate(
            model=IMAGE_MODEL,
            prompt=prompt,
            size=IMAGE_SIZE,
            n=1,  # pas de response_format en 1.x
        )
        d0 = resp.data[0]
        if getattr(d0, "url", None):
            print("[INFO] images.generate a renvoyé une URL")
            return ("url", d0.url)
        if getattr(d0, "b64_json", None):
            print("[INFO] images.generate a renvoyé du base64")
            return ("b64", d0.b64_json)
        print("[ERREUR] Réponse inattendue de l’API:", d0)
        return (None, None)
    except Exception as e:
        print(f"[ERREUR] Génération pour {le_poisson.get('nom','(nom manquant)')} : {e}")
        return (None, None)

# ===================== Téléchargement/sauvegarde ===================== #
def telecharger_et_sauvegarder_article(url_image: str, i: int, out_dir: Path):
    r = requests.get(url_image, timeout=60)
    if r.status_code == 200:
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / f"{i}.jpg"
        with path.open("wb") as f:
            f.write(r.content)
        print(f"[OK] Image (URL) : {path}")
    else:
        print(f"[ERREUR] Téléchargement URL : HTTP {r.status_code}")


def sauvegarder_image_b64(b64_str: str, i: int, out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{i}.png"
    with path.open("wb") as f:
        f.write(base64.b64decode(b64_str))
    print(f"[OK] Image (base64) : {path}")


# ========================= Boucle principale ========================= #
def creer_toutes_les_images(poissons):
    for i, poisson in enumerate(poissons, start=1):
        kind, value = generer_image_article(poisson)
        if kind == "url":
            telecharger_et_sauvegarder_article(value, i, IMAGES_DIR)
        elif kind == "b64":
            sauvegarder_image_b64(value, i, IMAGES_DIR)
    print("[FIN] Génération des images terminée.")

# ========================= Teste ========================= #
def _sanity_check_image_api():
    kind, value = ("", "")
    try:
        resp = client.images.generate(
            model=IMAGE_MODEL,
            prompt="Voiture de marque Corvette Chevrolet de couleur jaune",
            size=IMAGE_SIZE,
            n=1
        )
        d0 = resp.data[0]
        if getattr(d0, "url", None):
            kind, value = "url", d0.url
            telecharger_et_sauvegarder_article(value, 0, IMAGES_DIR)
        else:
            kind, value = "b64", d0.b64_json
            sauvegarder_image_b64(value, 0, IMAGES_DIR)
        print(f"[CHECK] OK via {kind}. Fichier: {IMAGES_DIR / ('0.jpg' if kind=='url' else '0.png')}")
    except Exception as e:
        print("[CHECK] Échec:", e)

# ============================== Lancement ============================== #

if __name__ == "__main__":

    _sanity_check_image_api()  # décommente pour tester une fois

    data = extraction_et_affichage_Donnes_JSON(JSON_PATH)
    if data:
        poissons = affichage_List(data)
        _ = affichage_List_des_noms(poissons)
        creer_toutes_les_images(poissons)
    