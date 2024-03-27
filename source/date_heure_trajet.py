from datetime import datetime, timedelta
from bdd import Bdd

dico_jours={"l_":0,
            "m_":1,
            "me":2,
            "j_":3,
            "v_":4}

def date_heure_trajet(id, horaire:str):
    """
    Entrées:
        id: l'identifiant de l'utilisateur connecté
        horaire: chaine de caractère représantant un jour de la semaine et un moment de la journée. Ex: l_m pour lundi matin, me_s pour mercredi soir 
    Sortie:
        objet datetime:
            - la date est le prochain jour correspondant au jour de la semaine demandé
            - l'heure correspond à l'heure de départ/arrivé au lycée pour l'horaire spécifié
    """
    heure = Bdd().get_horaires(id, horaire)
    date_heure = datetime.now()
    date_heure=date_heure.replace(hour=int(heure[:2]), minute=int(heure[3:]))

    delta_jours=(dico_jours[horaire[:2]]-datetime.now().weekday())%7 # nombre de jours à ajouter à la date actuelle pour tomber sur un jour de la semaine
    date_heure=date_heure+timedelta(days=delta_jours)
    return date_heure


