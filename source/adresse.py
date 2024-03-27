import requests

proxy={"http":"","https":""}


def coordonnees_adresse(adresse, ville, code_postal):
    """
    Renvoie les coordonnées géographiques d'un lieu après interrogation de l'API Base Adresse Nationale.
    - Entrées : adresse (chaîne de caractères)
    - Sortie : (lat, long) (couple de coordonnées géographiques)
    """
    url = f"https://api-adresse.data.gouv.fr/search/?q={adresse},{ville}&postcode={code_postal}&lat=48.535755&lon=7.501135"
    reponse = requests.get(url, proxies=proxy)
    reponse = reponse.json()
    coord = reponse['features'][0]['geometry']['coordinates']
    long = coord[0]
    lat = coord[1]
    return (lat, long)

