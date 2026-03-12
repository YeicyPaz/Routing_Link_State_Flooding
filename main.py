from Router import Router

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
    router_A = Router("A")
    router_B = Router("B")
    router_C = Router("C")
    router_D = Router("D")
    router_E = Router("E")

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

    for name, router in network.items():
        my_lsa= router.generate_lsa() #genere son prope LSA

        #on l'envoie le LSA à tous ces voisin direct
        for neighbor in router.neighbors:
            neighbor_node =network[neighbor] #on obtienne l'object du vosin depuis notre dictionnaire de reseau

            neighbor_node.receive_lsa(my_lsa, name, network)

    print("--------Flooding completed-----------")

    #et on montre le contenue de LSDB
    print("Contenue du LSDB du Router A:")
    for origin, lsa in router_A.lsdb.items():
        print(f"Origin: {origin} | Seq: {lsa.seq} | Age: {lsa.age}  | Neighbors: {lsa.neighbors}")     

    """print("Contenue du LSDB du Router B:")
    for origin, lsa in router_B.lsdb.items():
        print(f"Origin: {origin} | Seq: {lsa.seq} | Age: {lsa.age}  | Neighbors: {lsa.neighbors}")           """
    
    show_topologie(router_A)