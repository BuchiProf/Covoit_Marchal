from flask import Flask, render_template, request, url_for, redirect
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from adresse import coordonnees_adresse
import os
from bdd import Bdd, Utilisateur
from werkzeug.security import generate_password_hash
from date_heure_trajet import date_heure_trajet
from carte import Carte

carte = Carte()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.urandom(24)

login_manager = LoginManager()
login_manager.init_app(app)
 
print('Serveur lancé')

@login_manager.user_loader
def loader_user(user_id):
    return Utilisateur(user_id)
 

@app.route('/inscription', methods=["GET", "POST"])
def register():
    """page d'inscription"""
    result = request.form

    if request.method == "POST" and result['password1'] == result['password2']:
        lat, long =  coordonnees_adresse(result['adress'], result['city'], result['code'])
       
        bdd=Bdd()
        bdd.creer_utilisateur(result['username'],
                              generate_password_hash(result['password1']),
                              result['name'],
                              result['first_name'],
                              result['adress'],
                              result['code'],
                              result['city'],
                              lat, 
                              long,
                              carte.temps_marchal(lat, long))

        return redirect(url_for("login"))
    return render_template("inscription.html")
 
 
@app.route("/connexion", methods=["GET", "POST"])
def login():
    """page de connexion"""
    result=request.form
    log=True
    if request.method == "POST":
        bdd = Bdd()
        id = bdd.connexion(result["username"], result['password'])
        if id != 0:
            utilisateur = Utilisateur(id)
            login_user(utilisateur) 
            return redirect(url_for("home"))
        log=False

    return render_template("connexion.html",log=log)
 
@login_manager.unauthorized_handler
def unauthorized():
    """
    Défini la page vers laquelle rediriger un utilisateur non connecté
    https://flask-login.readthedocs.io/en/latest/#flask_login.LoginManager.unauthorized_handler
    """
    return redirect(url_for("login"))
 
@app.route("/logout")
def logout():
    """déconnecte un utilisateur"""
    logout_user()
    return redirect(url_for("home"))
 
 
@app.route("/")
@login_required
def home():
    """page d'accueil"""
    trajets_non_confirmes = Bdd().liste_trajets(int(current_user.id), False, True)
    trajets_confirmes = Bdd().liste_trajets(int(current_user.id), True, True)

    return render_template("accueil.html", trajets_confirmes=trajets_confirmes, trajets_non_confirmes=trajets_non_confirmes)


@app.route("/resultat", methods =["GET", "POST"])
@login_required
def recherche():
    """page de recherche de trajet"""
    if request.method == "POST":
        result=request.form
        horaire=result["jour"]
        if result['matin']=='matin':
            horaire += '_m'
        else:
            horaire += '_s'

        id = current_user.id
        tab= carte.recherche_trajet(id, horaire)
        return render_template("resultat.html",items=tab, horaire=horaire)
    return redirect(url_for('home'))


@app.route("/trajet", methods=["GET", "POST"])
@login_required
def trajet():
    """page d'affichage d'un trajet recherché"""
    if request.method == "POST":
        result=request.form
        sens = result["horaire"][-1]=="s"
        m = carte.carte_folium(result["passager"], result["conducteur"], sens)          
        iframe = m.get_root()._repr_html_()
        coord_debut=carte.coord_marchal
        coord_milieu=Bdd().get_utilisateur(result["passager"], "latitude, longitude")
        coord_fin=Bdd().get_utilisateur(result["conducteur"], "latitude, longitude")

        if sens:
            coord_debut, coord_fin = coord_fin, coord_debut

        return render_template("trajet.html",iframe=iframe, id_passager=result["passager"], id_conducteur=result["conducteur"], horaire=result["horaire"], coord_debut=coord_debut, coord_milieu=coord_milieu, coord_fin=coord_fin)
    return redirect(url_for("home"))

@app.route("/trajet_enregistre", methods=["GET", "POST"])
@login_required
def trajet_enregistre():
    """page d'affichage d'un trajet enregistré"""
    if request.method == "POST":
        result=request.form
        trajet=Bdd().infos_trajet(result["id_trajet"], current_user.id)
        sens = int(trajet["heure"]) < 12
        m = carte.carte_folium(trajet["id_passager"], trajet["id_conducteur"], sens)
        iframe = m.get_root()._repr_html_()

        coord_debut=carte.coord_marchal
        coord_milieu=Bdd().get_utilisateur(trajet["id_passager"], "latitude, longitude")
        coord_fin=Bdd().get_utilisateur(trajet["id_conducteur"], "latitude, longitude")

        if sens:
            coord_debut, coord_fin = coord_fin, coord_debut


        if trajet["confirmation_pass"] and trajet["confirmation_cond"]:
            return render_template("trajet_enregistre.html",iframe=iframe, infos=trajet, etat=0, coord_debut=coord_debut, coord_milieu=coord_milieu, coord_fin=coord_fin) # trajet confirme
        elif (trajet["confirmation_cond"] and int(current_user.id)==trajet["id_passager"]) or (trajet["confirmation_pass"] and int(current_user.id)==trajet["id_conducteur"]):
            print('t2')
            return render_template("trajet_enregistre.html",iframe=iframe, infos=trajet, etat=2, coord_debut=coord_debut, coord_milieu=coord_milieu, coord_fin=coord_fin) # trajet à confirmer par l'utilisateur
        else:
            return render_template("trajet_enregistre.html",iframe=iframe, infos=trajet, etat=1, coord_debut=coord_debut, coord_milieu=coord_milieu, coord_fin=coord_fin) # trajet à confirmer par l'autre personne

    return redirect(url_for("home"))





@app.route("/profil", methods=["GET", "POST"])
@login_required
def profil():
    """page de profil"""
    if request.method == "POST":
        result = request.form
        bdd=Bdd()
        bdd.modifier(current_user.id, "adresse", result['adress'])
        bdd.modifier(current_user.id, "ville", result['city'])
        bdd.modifier(current_user.id, "code_postal", result['code'])
        lat, long =  coordonnees_adresse(result['adress'], result['city'], result['code'])
        bdd.modifier(current_user.id, "latitude", lat)
        bdd.modifier(current_user.id, "longitude", long)
        tps_trajet = carte.temps_marchal(lat, long)
        bdd.modifier(current_user.id, "temps_trajet", tps_trajet)

        horaires=[result["l_m"], result["l_s"],
                  result["m_m"], result["m_s"],
                  result["me_m"], result["me_s"],
                  result["j_m"], result["j_s"],
                  result["v_m"], result["v_s"]]
        bdd.modifier_horaires(current_user.id, horaires)

        return redirect(url_for('home'))
    info = Bdd().get_utilisateur(current_user.id, 'adresse, ville, code_postal, nom, prenom')
    return render_template("profil.html", adresse=info[0], ville=info[1], code_postal=info[2], nom=info[3], prenom=info[4], horaires=Bdd().get_horaires(current_user.id))



@app.route("/enregistrer_trajet", methods=["GET", "POST"])
@login_required
def enregistrer_trajet():
    """enregistre un trajet dans la base de données"""
    if request.method == "POST":
        result=request.form
        Bdd().enregistrer_trajet(result["id_conducteur"], result["id_passager"], date_heure_trajet(current_user.id, result['horaire']), current_user.id)
    return redirect(url_for("home"))


@app.route("/confirmer_trajet", methods=["GET", "POST"])
@login_required
def confirmer_trajet():
    """confirme un trajet"""
    if request.method == "POST":
        result=request.form
        Bdd().confirmer_trajet(result["id_trajet"], current_user.id)
        
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run()