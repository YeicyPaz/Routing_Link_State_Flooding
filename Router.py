#dans chaque router il doit avoir au moins:
#une table de voisins et une base de donnes d'état d'enlace(LSDB)
#on aura besoin aussi d'un conteur pour son prope nombre de sequence vu que chanque fois que se emitte un LSA(link-statement advertissment) il faut utiliser un nombre strictement croissant
import time
import threading
from random import random
from typing import Dict
import heapq
from LSA import LSA

class Router:
    def __init__(self, name:str, visualizer=None):
        self.name = name
        self.visualizer = visualizer

        #table de voisin directs: dictionnaire de: {voisin: coute} 
        self.neighbors: Dict[str,int] ={}

        #Link-State Database (LSDB)
        #ici on va gardé le LSA plus recent de chaque router du reseau
        #LSDB dictionnaire: {origin: LSA plus recent}
        self.lsdb: Dict [str, LSA]={}

        #conteur prope du router pour generer ses nombre de sequence
        self.seq_counter = 0
    
    def add_neighbor(self, neighbor:str, cost:int): 
        """metode auxiliar pour conecter ce router avec ses voisins"""
        self.neighbors[neighbor] = cost
        if self.visualizer: self.visualizer.addEdge(self.name, neighbor, cost)

    def generate_lsa(self)-> LSA:
        """Genere un nouveau LSA en decribant le voisin actueles de ce router"""
        self.seq_counter += 1 #pour l'incrementation de numéro de sequence 

        return LSA(
            origin=self.name,
            seq=self.seq_counter,
            age=10,
            neighbors=self.neighbors.copy() #on a fait une copie de voisins pour ne pas modifie l'originel accidentallement
            )
    
    #pour le processus des LSA
    def receive_lsa(self, lsa_received: LSA, sender_name:str, network:dict, delay=0, track_visualizer=True, async_mode=True):

        # A positive delay allows to simulate the message (LSA) transit time
        # It's therefore better to call this function in a thread (parallel process)
        if delay > 0: time.sleep(delay)
        self.visualizer.removeTransit(sender_name, self.name, lsa_received.origin)
       
       #si il y a LSA expiré il faut le descarted
        if lsa_received.age <=0:
            return
        origin=lsa_received.origin
        is_new= False

        #c'est nouveau si on l'avait pas dans le LSDB ou si la sequence est majeur
        if origin not in self.lsdb or lsa_received.seq > self.lsdb[origin].seq:
            is_new = True

        if is_new:
            self.lsdb[origin] = lsa_received #on garde le LSA recived dans notre base de donnée

            #on le envoie aux vosins
            for neighbor_name in self.neighbors:
                if neighbor_name != sender_name: #on le envoie pas au router qui nous a envoyé le LSA

                    new_age= lsa_received.age -1 #on simule un aging en restant -1 dans age

                    #et on cree une copie de LSA pour le reenvoyer
                    lsa_to_send= LSA(
                        origin=lsa_received.origin,
                        seq=lsa_received.seq,
                        age=new_age,
                        neighbors=lsa_received.neighbors
                    )

                    #si il n'expire pas encore il faut passer le LSA au voisin
                    if lsa_to_send.age >0:
                        neighbors_obj= network[neighbor_name]
                        #le voisin recive le LSA et on est le sender
                        if track_visualizer and self.visualizer:
                            self.visualizer.lsaTransit(self.name, neighbor_name, lsa_to_send.origin)
                        delay = random()+0.5 if async_mode else 0    # simulate a sending time between 0.5 and 1.5 second
                        # Call the receive function through a thread to make the actions simultaneous and non-blocking
                        if async_mode:
                            threading.Thread(target=neighbors_obj.receive_lsa, args=(lsa_to_send, self.name, network, delay, track_visualizer, async_mode)).start()
                        else:
                            neighbors_obj.receive_lsa(lsa_to_send, self.name, network, delay, track_visualizer, async_mode)
                
            self.visualizer.capture()

    def compute_shortest_paths(self, target, routers): #Dijkstra algorithme
        distances = {router_obj: (float('inf'), None) for router_obj in routers.values()}  # on initialise les couts à l'infini
        distances[self] = (0, None)  #le  cout pour le router de départ est de 0
        # visiter les voisins du noeud actuel et mettre à jour les couts
        #on fait une file de priorité
        pq = [(0, self.name, self)]
        #print(f"Computing shortest path from {self.name} to {target.name}...")
        heapq.heapify(pq) #on transforme en min-heap
        visited = set()
        while pq: #tant que la priority queue n'est pas vide
            current_distance, _, current_node = heapq.heappop(pq) #on récupere le noeud avec la plus petite distance
            if current_node in visited:
                continue #on ignore les noeuds deja visités
            visited.add(current_node)
            for neighbor_name, cost in routers[current_node.name].neighbors.items():
                neighbor_obj = routers[neighbor_name]
                #additionner la distance
                tentative_distance = current_distance + cost
                if tentative_distance < distances[neighbor_obj][0]:
                    distances[neighbor_obj] = (tentative_distance, current_node)
                    #print(f"Updating distance to {neighbor_obj.name}: {tentative_distance}, via the last node used {current_node.name}")
                    heapq.heappush(pq, (tentative_distance, neighbor_obj.name, neighbor_obj))
        # Reconstruct the path
        path = []
        current = target
        while current is not None:
            path.append(current.name)
            current = distances[current][1]
        path.reverse()
        return path, distances[target][0]

    def getLSDB(self)->str:
        result = ""
        for origin, lsa in self.lsdb.items():
            result += f"Origin: {origin} | Seq: {lsa.seq} | Age: {lsa.age}  | Neighbors: {lsa.neighbors}\n"
        return result
    






    def store_local_LSA(self, lsa: LSA):
        # Garde le dernier LSA local dans le LSDB
        self.lsdb[self.name] = lsa


    # PAS SUR,  A REVOIR
    def flood_LSA(self, lsa: LSA, network:dict, sender_name=None, track_visualizer=True, async_mode=True):
        # Envoie un LSA a tous les voisins sauf le sender
        for neighbor_name in self.neighbors:
            if neighbor_name != sender_name:
                neighbor_obj = network[neighbor_name]
                if track_visualizer and self.visualizer:
                    self.visualizer.lsaTransit(self.name, neighbor_name, lsa.origin)
                delay = random()+0.5 if async_mode else 0
                if async_mode:
                    threading.Thread(target=neighbor_obj.receive_lsa, args=(lsa, self.name, network, delay, track_visualizer, async_mode)).start()
                else:
                    neighbor_obj.receive_lsa(lsa, self.name, network, delay, track_visualizer, async_mode)

    def originate_lsa(self, network:dict, track_visualizer=True, async_mode=True):
        # Genere, stocke et diffuse un nouveau LSA local
        LSA = self.generate_lsa()
        self.store_local_LSA(LSA)
        self.flood_LSA(LSA, network, None, track_visualizer, async_mode)
        return LSA


    def build_topology(self):
        # Reconstruit la topologie connue
        topology = {}
        for origin, lsa in self.lsdb.items():
            topology.setdefault(origin, {})
            for neighbor, cost in lsa.neighbors.items():
                topology[origin][neighbor] = cost
                topology.setdefault(neighbor, {})
        topology.setdefault(self.name, {})
        return topology

    # NE PREND PAS LES BONNES A MODIFIER
    def shortest_path_topology(self, target_name:str, topology:dict):
        # Dijkstra sur la topologie reconstruite
        distances = {node: float('inf') for node in topology}
        previous = {node: None for node in topology}
        distances[self.name] = 0
        pq = [(0, self.name)]

        while pq:
            current_distance, current_node = heapq.heappop(pq)
            if current_distance > distances[current_node]:
                continue
            for neighbor_name, cost in topology.get(current_node, {}).items():
                tentative_distance = current_distance + cost
                if tentative_distance < distances.get(neighbor_name, float('inf')):
                    distances[neighbor_name] = tentative_distance
                    previous[neighbor_name] = current_node
                    heapq.heappush(pq, (tentative_distance, neighbor_name))

        if distances.get(target_name, float('inf')) == float('inf'):
            return [], float('inf')

        path = []
        current = target_name
        while current is not None:
            path.append(current)
            current = previous[current]
        path.reverse()
        return path, distances[target_name]

    def get_next_step(self, path:list):
        # Retourne le prochain saut du chemin
        if len(path) >= 2:
            return path[1]
        if len(path) == 1:
            return path[0]
        return None

    def get_routing_table_from_lsdb(self, network:dict):
        # Construit la table de routage depuis le LSDB
        topology = self.build_topology()
        routing_table = {}
        for destination in network.keys():
            if destination == self.name:
                continue
            path, cost = self.shortest_path_topology(destination, topology)
            routing_table[destination] = (self.get_next_step(path), cost)
        return routing_table
    

    # A REVOIR N EFFACE PAS LA ROUTE A CHANGER
    def apply_link_failure(self, router_1:str, router_2:str, network:dict):
        # Applique la panne, flood les nouveaux LSAs et affiche les changements
        old_routing_table = self.get_routing_table_from_lsdb(network)

        if router_2 in network[router_1].neighbors:
            network[router_1].neighbors.pop(router_2)
        if router_1 in network[router_2].neighbors:
            network[router_2].neighbors.pop(router_1)

        network[router_1].originate_lsa(network, track_visualizer=False, async_mode=False)
        network[router_2].originate_lsa(network, track_visualizer=False, async_mode=False)

        new_routing_table = self.get_routing_table_from_lsdb(network)

        print(f"\n--------Link failure injected: {router_1}-{router_2}-----------")
        print(f"\nChanged routing entries at router {self.name}:")

        has_changed = False
        for destination in sorted(new_routing_table.keys()):
            old_next_hop, old_cost = old_routing_table[destination]
            print(f"{destination}: ({old_next_hop}, {old_cost})", end=" -> ")
            new_next_hop, new_cost = new_routing_table[destination]
            if old_next_hop != new_next_hop or old_cost != new_cost:
                has_changed = True
                print(f"{destination}: ({old_next_hop}, {old_cost}) -> ({new_next_hop}, {new_cost})")

        if not has_changed:
            print("No routing entry changed.")
