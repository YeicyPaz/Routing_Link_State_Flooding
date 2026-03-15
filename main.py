import time
import threading
from random import random
from Router import Router
from visualizer import Visualizer

def show_topologie(router):
    """il lis le LSDB d'un router et extrait tous les nodes uniques pour la reconstruction de la carte de reseau"""
    link_uniques= set() #on utilise set pour eviter garder des dupliques

    #ici nous parcourons la base de données : 'origine' est le créateur du LSA, 'lsa' est l’objet LSA
    for origin, lsa in router.lsdb.items():
        # et ici nous parcourons les voisins signalés sur ce LSA
        for neighbor, cost in lsa.neighbors.items():

           # Nous trions alphabétiquement pour que (B, A) devienne (A, B)
            # Il est plus facile d’identifier les doublons
            node_1, node_2 = sorted([origin,neighbor])

            link_uniques.add((node_1, node_2, cost)) ## on ajoute la tupla à l’ensemble

    print(f"\n--- Topology reconstructed by the Router {router.name} ---")

    #on imprime les links ordoned pour faciliter la lecture
    for n1, n2, cost in sorted(link_uniques):
        print(f"Link: {n1} <--> {n2} | Cost: {cost}")

#instanciation de 5 routers


if __name__ == "__main__":
    visualizer = Visualizer()

    router_A = Router("A",visualizer)
    router_B = Router("B",visualizer)
    router_C = Router("C",visualizer)
    router_D = Router("D",visualizer)
    router_E = Router("E",visualizer)

    #config de voisin et cost selon le lab
    #enlace de ---- router A-----
    router_A.add_neighbor("B",5)
    router_A.add_neighbor("E",3)

    #enlace de ---- router B-----
    router_B.add_neighbor("A",5)
    router_B.add_neighbor("C",8)
    router_B.add_neighbor("D",2)

    #enlace de ---- router C-----
    router_C.add_neighbor("B",8)
    router_C.add_neighbor("D",8)
    router_C.add_neighbor("E",8)

    #enlace de ---- router D-----
    router_D.add_neighbor("B", 2)
    router_D.add_neighbor("C", 8)
    router_D.add_neighbor("E", 3)

    #enlace de ---- router E-----
    router_E.add_neighbor("A", 3) 
    router_E.add_neighbor("C", 8) 
    router_E.add_neighbor("D", 3)

    #dictionnaire de reseau pour son agrupation
    network ={
        "A":router_A,
        "B":router_B,
        "C":router_C,
        "D":router_D,
        "E":router_E
    }
    visualizer.setNodes(network)
    visualizer.capture()    # initial network
    """
    for name, router in network.items():
        my_lsa= router.generate_lsa() #genere son prope LSA

        #on l'envoie le LSA à tous ces voisin direct
        for neighbor in router.neighbors:
            neighbor_node =network[neighbor] #on obtienne l'object du vosin depuis notre dictionnaire de reseau
            visualizer.lsaTransit(name, neighbor, name)
            delay = random()+0.5    # simulate a sending time between 0.5 and 1.5 second
            # Call the receive function through a thread to make the actions simultaneous and non-blocking
            threading.Thread(target=neighbor_node.receive_lsa, args=(my_lsa, name, network, delay)).start()
        
        visualizer.capture()    # LSAs of a same router are assumed to be sent at the same time

        # Waiting time to prevent the sending of LSA of all routers at the same time
        # The shorter the waiting time, the more simultaneous traffic there will be.
        time.sleep(2)

    # Waiting all LSA message are finished to transit (impossible in reality)
    while len(visualizer.edges_lsa) > 0:
        time.sleep(1)
    visualizer.capture()
    """
    print("--------Flooding completed-----------")

    #et on montre le contenue de LSDB
    print("Contenue du LSDB du Router A:")
    for origin, lsa in router_A.lsdb.items():
        print(f"Origin: {origin} | Seq: {lsa.seq} | Age: {lsa.age}  | Neighbors: {lsa.neighbors}")     

    """print("Contenue du LSDB du Router B:")
    for origin, lsa in router_B.lsdb.items():
        print(f"Origin: {origin} | Seq: {lsa.seq} | Age: {lsa.age}  | Neighbors: {lsa.neighbors}")           """
    
    #show_topologie(router_A)

    #visualizer.show()

    #print(f"the shortest path from B to E: {router_B.compute_shortest_paths(router_E, network)}")
    print(f"the shortest path from C to E: {router_C.compute_shortest_paths(router_E, network)}")

    print(f"the shortest path from A to D: {router_A.compute_shortest_paths(router_D, network)}")
    
    