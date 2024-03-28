Arborescence des fichiers :

Source  
+--data   
   +----map.graphml  
+--static  
   +----image  
      +------logo.ico  
      +------logo.png  
   +----style.css  
   +----Style_glb.css  
   +----stylepro.css  
+--templates  
   +----accueil.html  
   +----connexion.html  
   +----inscription.html  
   +----profil.html  
   +----resultat.html  
   +----trajet.html  
   +----trajet_enregistre.html  
+--adresse.py  
+--bdd.py  
+--carte.py  
+--date_heure_trajet  
+--flask_app.py  
+--database.db  





Protocole d’utilisation :
- Ouvrir un terminal et exécuter pip install -r requirements.txt
- Si nécessaire, configurer le proxy en entrant l’adresse du proxy dans le dictionnaire à la ligne 3 du fichier adresse.py
- Exécuter flask_app.py depuis le dossier source
- Attendre que le message ‘serveur lancé’ s’affiche dans la console (cela peut prendre entre quelque secondes et une minute en fonction de la machine utilisé)
- Ouvrir un navigateur et entrer l’adresse localhost:5000

NB: Le site est aussi disponible à l'adresse https://covoitmarchal.eu.pythonanywhere.com/

