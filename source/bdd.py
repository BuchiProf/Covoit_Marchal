import sqlite3
from flask_login import UserMixin
from werkzeug.security import check_password_hash
from datetime import datetime

format_date_heure = "%Y-%m-%d-%H-%M"

tab_jours_semaine = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
tab_mois = ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin", "Juillet", "Août", "Septembre", "Octobre", "Décembre"]

class Bdd:
    def __init__(self, chemin = 'database.db'):
        self.conn = sqlite3.connect(chemin)
        self.conn.execute("PRAGMA foreign_keys = 1")

    def __del__(self):
        self.conn.close()

    def construire(self):
        """crée toute les tables de la base de données"""
        self.conn.execute('CREATE TABLE IF NOT EXISTS utilisateurs (id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE, pseudo TEXT, mdp TEXT, nom TEXT, prenom TEXT, adresse TEXT, code_postal INTEGER, ville TEXT, latitude INTEGER, longitude INTEGER, temps_trajet INTEGER)')
        self.conn.execute('CREATE TABLE IF NOT EXISTS horaires (id_user INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE, l_m TEXT, l_s TEXT, m_m TEXT, m_s TEXT, me_m TEXT, me_s TEXT, j_m TEXT, j_s TEXT, v_m TEXT, v_s TEXT, FOREIGN KEY (id_user) REFERENCES utilisateurs(id))')
        self.conn.execute('CREATE TABLE IF NOT EXISTS trajets (id_trajet INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE, id_conducteur INTEGER, id_passager INTEGER, date_heure TEXT, confirmation_cond INTEGER, confirmation_pass INTEGER, FOREIGN KEY (id_conducteur) REFERENCES utilisateurs(id), FOREIGN KEY (id_passager) REFERENCES utilisateurs(id))')
    
    def get_utilisateur(self, id:int, descripteur = '*'):
        """renvoie les descripteurs de l'utilisateur corresponandt à l'id"""
        cur = self.conn.cursor()
        cur.execute(f'SELECT {descripteur} FROM utilisateurs WHERE id={id}')
        resultat = cur.fetchall()
        if resultat != []:
            return resultat[0] 
    
    def tab_utilisateur(self, id:int = 0, descripteur = '*', horaire='l_m'):
        """
        Renvoie un tableau dont chaque élement contient les descripteurs d'un utilisateur.
        Seul les utilisateurs dont l'heure de départ/arrivée du lycée pour l'horaire indiqué(jour de la semaine + matin/soir) correspond à celle de l'utilisateur id pour ce même horaire sont renvoyés
        """
        cur = self.conn.cursor()
        cur.execute(f'SELECT {horaire} FROM horaires WHERE id_user={id}')
        h=cur.fetchall()[0][0]
        cur.execute(f'SELECT {descripteur} FROM utilisateurs JOIN horaires ON id = id_user WHERE id!={id} AND {horaire} = ?', [h])
        return cur.fetchall()
    
    
    def connexion(self, pseudo, mdp):
        """
        vérifie si le pseudo et le mot de passe correspondent à un utilisateur.
        si le pseudo et mdp sont correctes : renvoie l'id de l'utilisateur
        sinon: renvoie 0
        """
        cur = self.conn.cursor()
        cur.execute(f'SELECT id, mdp FROM utilisateurs WHERE pseudo = "{pseudo}"')

        resultat = cur.fetchall()
        if resultat != []:
            if check_password_hash(resultat[0][1], mdp):
                return resultat[0][0]
        return 0
    
    def creer_utilisateur(self, pseudo, mdp, nom, prenom, adresse, code_postal, ville, latitude, longitude, temps_trajet):
        """
        Crée un nouvel utilisateur dans la base de données avec les données entrées
        """
        self.conn.execute("INSERT INTO utilisateurs(pseudo, mdp, nom, prenom, adresse, code_postal, ville, latitude, longitude, temps_trajet) VALUES (?,?,?,?,?,?,?,?,?,?)", (pseudo, mdp, nom, prenom, adresse, code_postal, ville, latitude, longitude, temps_trajet))
        horaires = ["08:00", "17:00"]*5
        self.conn.execute("INSERT INTO horaires (l_m, l_s, m_m, m_s, me_m, me_s, j_m, j_s, v_m, v_s) VAlUES (?,?,?,?,?,?,?,?,?,?)", horaires)
        self.conn.commit()

    def supprimer_table(self, table:str):
        """supprime une table de la base de données"""
        self.conn.execute(f'DROP TABLE IF EXISTS {table}')
        self.conn.commit()

    def supprimer_utilisateur(self, id):
        """supprime l'utilisateur d'identifiant id de la table utilisateurs"""
        self.conn.execute(f'DELETE FROM utilisateurs WHERE id={id}')
        self.conn.commit()
    
    def modifier(self, id, descripteur, valeur):
        """modifie la valeur d'un descripteur de l'objet dont l'identifiant est id"""
        self.conn.execute(f'UPDATE utilisateurs SET {descripteur} = ? WHERE id={id}', [valeur])
        self.conn.commit()

    def get_horaires(self, id:int, descr="*"):
        """renvoie un tuple contenant les horaires d'un utilisateurs id"""
        cur = self.conn.cursor()
        cur.execute(f'SELECT {descr} FROM horaires WHERE id_user={id}')
        resultat = cur.fetchall()
        if resultat != []:
            if descr=="*":
                return resultat[0][1:]
            else:
                return resultat[0][0]
        
    def modifier_horaires(self, id:int, horaires):
        """modfie les horaires d'un utilisateur id"""
        self.conn.execute(f"UPDATE horaires SET (l_m, l_s, m_m, m_s, me_m, me_s, j_m, j_s, v_m, v_s) = (?,?,?,?,?,?,?,?,?,?) WHERE id_user ={id}", horaires)
        self.conn.commit()

    def enregistrer_trajet(self, id_conducteur, id_passager, date_heure, id_confirmateur):
        """crée un trajet dans la table trajets"""
        date_heure_str = date_heure.strftime(format_date_heure)
        self.conn.execute("INSERT INTO trajets (id_conducteur, id_passager, date_heure, confirmation_cond, confirmation_pass) VALUES (?, ?, ?, ?, ?)", (id_conducteur, id_passager, date_heure_str, id_confirmateur==id_conducteur, id_confirmateur==id_passager))
        self.conn.commit()


    def liste_trajets(self, id, trajets_confirmes:bool, trajets_futurs_uniquement:bool=False):
        """
        renvoie un tableau contenant les informations sur tous les trajets enregistrés d'un utilisateur id
        trajets_futurs_uniquement(bool): si True, renvoie seulement les trajets qui n'ont pas encore eu lieu
        """
        cur = self.conn.cursor()
        if trajets_futurs_uniquement:
            date_mini = datetime.now().strftime(format_date_heure)
        else:
            date_mini="0"
        
        if trajets_confirmes:
            cur.execute("SELECT id_trajet FROM trajets JOIN utilisateurs ON utilisateurs.id = id_conducteur OR utilisateurs.id = id_passager WHERE utilisateurs.id = ? AND date_heure > ? AND confirmation_cond and confirmation_pass", (id, date_mini))
        else:
            cur.execute("SELECT id_trajet FROM trajets JOIN utilisateurs ON utilisateurs.id = id_conducteur OR utilisateurs.id = id_passager WHERE utilisateurs.id = ? AND date_heure > ? AND NOT(confirmation_cond and confirmation_pass)", (id, date_mini))
        res = cur.fetchall()
        tab=[]
        for trajet in res:
            tab.append(self.infos_trajet(trajet[0], id))            
        return tab
    
    def infos_trajet(self, id_trajet, id_user):
        """renvoie les informations sur un trajet id_trajet"""
        cur = self.conn.cursor()

        cur.execute("SELECT id_trajet, id_conducteur, id_passager, date_heure, confirmation_cond, confirmation_pass FROM trajets WHERE id_trajet=?", (id_trajet,))
        res = cur.fetchall()[0]

        if res[1]==id_user:
            nom_prenom = self.get_utilisateur(res[2], "nom, prenom")
        else:
            nom_prenom = self.get_utilisateur(res[1], "nom, prenom")
        date_heure=datetime.strptime(res[3], format_date_heure)

        jour_semaine=tab_jours_semaine[date_heure.weekday()]
        mois=tab_mois[date_heure.month-1]

        return {"id_trajet":res[0],
                "id_conducteur":res[1],
                "id_passager":res[2],
                "confirmation_cond":res[4],
                "confirmation_pass":res[5], 
                "nom":nom_prenom[0],
                "prenom":nom_prenom[1],
                "date_heure":res[3],
                "annee":date_heure.year,
                "mois":mois,
                "jour":date_heure.day,
                "jour_semaine":jour_semaine,
                "heure":str(date_heure.hour),
                "minutes":date_heure.strftime("%M")}


    def confirmer_trajet(self, id_trajet, id_utilisateur):
        """confirme un trajet id_trajet par un utilisateur id_utilisateur"""
        self.conn.execute('UPDATE trajets SET confirmation_pass=1, confirmation_cond=1 WHERE id_trajet=? AND (id_conducteur=? AND confirmation_pass=1 OR id_passager=? AND confirmation_cond=1)', (id_trajet, id_utilisateur, id_utilisateur))
        self.conn.commit()

class Utilisateur(UserMixin):
    """
    Classe utilisateur nécessaire pour flask_login
    https://flask-login.readthedocs.io/en/latest/#your-user-class
    """
    def __init__(self, id):
        self.id = id



