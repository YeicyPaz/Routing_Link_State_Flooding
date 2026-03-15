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
    def receive_lsa(self, lsa_received: LSA, sender_name:str, network:dict, delay=0):

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
                        self.visualizer.lsaTransit(self.name, neighbor_name, lsa_to_send.origin)
                        delay = random()+0.5    # simulate a sending time between 0.5 and 1.5 second
                        # Call the receive function through a thread to make the actions simultaneous and non-blocking
                        threading.Thread(target=neighbors_obj.receive_lsa, args=(lsa_to_send, self.name, network, delay)).start()
                
            self.visualizer.capture()

    def compute_shortest_paths(self, target, routers): #Dijkstra algorithme
        distances = {router_obj: (float('inf'), None) for router_obj in routers.values()}  # on initialise les couts à l'infini
        distances[self] = (0, None)  #le  cout pour le router de départ est de 0
        # visiter les voisins du noeud actuel et mettre à jour les couts
        #on fait une file de priorité
        pq = [(0,self)]
        heapq.heapify(pq) #on transforme en min-heap
        visited = set()
        while pq: #tant que la priority queue n'est pas vide
            current_distance, current_node = heapq.heappop(pq) #on récupere le noeud avec la plus petite distance
            if current_node in visited:
                continue #on ignore les noeuds deja visités
            visited.add(current_node)
            for neighbor_name, cost in routers[current_node.name].neighbors.items():
                neighbor_obj = routers[neighbor_name]
                #additionner la distance
                tentative_distance = current_distance + cost
                if tentative_distance < distances[neighbor_obj][0]:
                    distances[neighbor_obj] = (tentative_distance, current_node)
                    heapq.heappush(pq, (tentative_distance, neighbor_obj))
        # le chemin sous forme de liste de noms de routeurs
        path = []
        current = target
        while current is not None:
            path.append(current.name)
            current = distances[current][1]
        path.reverse()
        return path

