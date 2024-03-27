import osmnx as ox
import networkx as nx
from bdd import Bdd
import folium as flm

class Carte:
    def __init__(self):
        self.coord_marchal = 48.535755, 7.501135

        self.charger_graphe()

    def tps_trajet(self, start:tuple, end:tuple):
        """Calcul le temps de chacun des trajets
        Entrées:
            G :un graphe representant le réseau de routes
            start : les coordonnées de départ
            end : un tuple de 2 tableau, l'un contenant les latitudes des points d'arrivée de chaque trajet et l'autre les longitudes

        Sortie:
            un tableau contenant le temps de chaque trajet
        """

        orig = ox.distance.nearest_nodes(self.G, X=start[1], Y=start[0])
        dest = ox.distance.nearest_nodes(self.G, X=end[1], Y=end[0])

        times = nx.single_source_dijkstra_path_length(self.G, orig, weight='travel_time')

        result = [round(times[node]) for node in dest]

        return(result)


    def telecharger_graphe(self, rayon=30):
        """Telecharge la carte des routes dans un rayonde 30 km du lycée et la sauvegarde dans un fichier"""
        # https://github.com/gboeing/osmnx-examples/blob/main/notebooks/00-osmnx-features-demo.ipynb
        # https://github.com/gboeing/osmnx-examples/blob/main/notebooks/05-save-load-networks.ipynb

        self.G = ox.graph.graph_from_point(self.coord_marchal, dist=rayon * 1000, network_type='drive', simplify=True)
        filepath = "data/map.graphml"
        ox.save_graphml(self.G, filepath)


    def charger_graphe(self):
        """Charge la carte depuis un fichier. Doit être executé avant d'ultiliser recherche_trajet ou temps_marchal"""
        # https://github.com/gboeing/osmnx-examples/blob/main/notebooks/02-routing-speed-time.ipynb
        # https://github.com/gboeing/osmnx-examples/blob/main/notebooks/05-save-load-networks.ipynb

        filepath = "data/map.graphml"
        self.G = ox.load_graphml(filepath)
        self.G = ox.speed.add_edge_speeds(self.G)
        self.G = ox.speed.add_edge_travel_times(self.G)


    def recherche_trajet(self, id:int, jour_ms, sens=False, coeff = 1.5):
        """Recherche les meilleurs trajets pour un utilisateur

        Entrées:
            id(int): l'identifiant associé à l'utilisateur dans la base de donnée
            jour_ms(str): jour de la semaine du trajet recherché et matin/soir? ex : l_m pour lundi matin
            sens(bool): le sens du trajet (False pour l'aller, True pour le retour)
            coeff(float): quotient max entre le trajet direct et le trajet avec covoiturage. Un trajet est proposé seulement si tps_covoiturage/tps_direct <= coeff 

        Sortie:
            list: un tableau de dictionnaires contenant les informations à envoyer à la page
        """

        bdd=Bdd()
        tab_utilisateurs = bdd.tab_utilisateur(id, 'id, latitude, longitude, temps_trajet, nom, prenom', jour_ms)
        if tab_utilisateurs == []:
            return []
        orig = bdd.get_utilisateur(id, 'latitude, longitude')
        dests = [], []

        for utilisateur in tab_utilisateurs:
            dests[0].append(utilisateur[1])
            dests[1].append(utilisateur[2])

        temps = self.tps_trajet(orig, dests)

        trajets = []
        t_CL = bdd.get_utilisateur(id, 'temps_trajet')[0]  # temps de trajet entre l'utilisateur connecté et le lycée
        for utilisateur in tab_utilisateurs:
            t_CU = temps.pop(0) # temps de trajet entre l'utilisateur connecté et un autre utilisateur
            t_UL = utilisateur[3] # temps de trajet entre un  utilisateur et le lycée

            if t_CU + t_UL < t_CL * coeff and t_CU < t_CL:
                tps_sup=round((t_CU + t_UL - t_CL)/60)
                trajets.append(dict(tps = round(t_CU + t_UL), tps_sup=tps_sup, nom=utilisateur[4], prenom=utilisateur[5], role=True, conducteur=id, passager=utilisateur[0]))

            if t_CU + t_CL < t_UL * coeff and t_CU < t_UL:
                tps_sup=round((t_CU + t_CL - t_UL)/60)
                trajets.append(dict(tps = round(t_CU + t_UL), tps_sup=tps_sup, nom=utilisateur[4], prenom=utilisateur[5], role=False, conducteur=utilisateur[0], passager=id))

        return trajets


    def temps_marchal(self, lat, long):
        """Renvoie la durée du trajet d'un point au lycée Louis Marchal
        Entrées:
            lat(float):
            long(float)
    
        Sortie:
            int: temps en secondes nécessaire pour effectuer le trajet
        """
    
        orig = ox.distance.nearest_nodes(self.G, X=long, Y=lat)
        dest = ox.distance.nearest_nodes(self.G, X=self.coord_marchal[1], Y=self.coord_marchal[0])
        route = ox.shortest_path(self.G, orig, dest, weight="travel_time")
        travel_time = round(sum(ox.utils_graph.get_route_edge_attributes(self.G, route, "travel_time")))
        return travel_time

    def itineraire(self, id_conducteur, id_passager, sens=False):
        """Renvoie l'itineraire de l'utilisateur id_conducteur vers le lycée en passant par l'utilisateur id_conducteur
    
        Entrées:
            id_conducteur: l'identifiant de conducteur
            id_passager: l'identifiant du passager
            sens(bool): le sens du trajet (False pour l'aller, True pour le retour)
        Sortie:
            un tuples de 2 itineraires
        """
    
        bdd = Bdd()
        coord_cond = bdd.get_utilisateur(id_conducteur, 'latitude, longitude')
        coord_pass = bdd.get_utilisateur(id_passager, 'latitude, longitude')

        depart = coord_cond
        milieu = coord_pass
        arrivee = self.coord_marchal

        if  sens:
            depart, arrivee = arrivee, depart

        orig = ox.distance.nearest_nodes(self.G, X=depart[1], Y=depart[0])
        middle = ox.distance.nearest_nodes(self.G, X=milieu[1], Y=milieu[0])
        dest = ox.distance.nearest_nodes(self.G, X=arrivee[1], Y=arrivee[0])


        route1 = nx.shortest_path(self.G, orig, middle, weight="travel_time")
        route2 = nx.shortest_path(self.G, middle, dest, weight="travel_time")

        return route1 + route2[1:]
    
    def carte_folium(self, passager, conducteur, sens):
        """
        renvoie une carte folium représentant un itinéraire
        Entrées:
            conducteur: l'identifiant de conducteur
            passager: l'identifiant du passager
            sens(bool): le sens du trajet (False pour l'aller, True pour le retour)
        Sortie:
            une carte folium avec l'itinéraire de covoiturage du conducteur vers le lycée en passant par le passager
            et des marqueurs pour indiquer l'adresse du conducteur, du passager et du lycée

        """
        itineraire=self.itineraire(conducteur, passager, sens)
        m = ox.plot_route_folium(self.G, itineraire)

        flm.Marker(
            location=self.coord_marchal,
            popup="Lycée Louis Marchal",
            icon=flm.Icon(icon="briefcase", color='blue')
        ).add_to(m)

        info_passager = Bdd().get_utilisateur(passager, 'latitude, longitude, nom, prenom, adresse, code_postal, ville')
        flm.Marker(
            location=info_passager[0:2],
            popup=(info_passager[2] +  '<br>' + info_passager[3] + '<br>' + info_passager[4]+ '<br>' + str(info_passager[5])+ '<br>' + info_passager[6]),
            icon=flm.Icon(icon="home", color='red'),

        ).add_to(m)

        info_conducteur = Bdd().get_utilisateur(conducteur, 'latitude, longitude, nom, prenom, adresse, code_postal, ville')
        flm.Marker(
            location=info_conducteur[0:2],
            popup=(info_conducteur[2] +  '<br>' + info_conducteur[3] + '<br>' + info_conducteur[4]+ '<br>' + str(info_conducteur[5])+ '<br>' + info_conducteur[6]),
            icon=flm.Icon(icon="home", color="green"),
        ).add_to(m)



        m.get_root().width = "100%"
        m.get_root().height = "100%"

        return m


    

