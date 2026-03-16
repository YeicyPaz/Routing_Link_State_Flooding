import time
import threading
import heapq
from random import random
from Router import Router
from visualizer import Visualizer


def show_topologie(router):
    """il lis le LSDB d'un router et extrait tous les nodes uniques pour la reconstruction de la carte de reseau"""
    link_uniques = set()  # on utilise set pour eviter garder des dupliques

    # ici nous parcourons la base de données : 'origine' est le créateur du LSA, 'lsa' est l’objet LSA
    for origin, lsa in router.lsdb.items():
        # et ici nous parcourons les voisins signalés sur ce LSA
        for neighbor, cost in lsa.neighbors.items():
            # Nous trions alphabétiquement pour que (B, A) devienne (A, B)
            # Il est plus facile d’identifier les doublons
            node_1, node_2 = sorted([origin, neighbor])
            link_uniques.add((node_1, node_2, cost))

    print(f"\n--- Topology reconstructed by the Router {router.name} ---")

    # on imprime les links ordoned pour faciliter la lecture
    for n1, n2, cost in sorted(link_uniques):
        print(f"Link: {n1} <--> {n2} | Cost: {cost}")


def wait_for_flooding(visualizer):
    """attend la fin de tous les LSAs en transit"""
    while len(visualizer.edges_lsa) > 0:
        time.sleep(1)
    visualizer.capture()


def flood_router_lsa(router, network, visualizer):
    """fait originer un nouveau LSA au router et l'envoie à tous ses voisins directs"""
    my_lsa = router.generate_lsa()
    router.lsdb[router.name] = my_lsa  # on garde aussi notre propre LSA localement

    for neighbor in router.neighbors:
        neighbor_node = network[neighbor]
        visualizer.lsaTransit(router.name, neighbor, router.name)
        delay = random() + 0.5
        threading.Thread(target=neighbor_node.receive_lsa, args=(my_lsa, router.name, network, delay)).start()

    visualizer.capture()


def print_changed_entries(old_table, new_table):
    print("\n--- Routing entries changed at router A after failure of link E-D ---")

    changed = False
    all_destinations = sorted(set(old_table.keys()) | set(new_table.keys()))

    for destination in all_destinations:
        old_entry = old_table.get(destination, {"next_hop": None, "cost": float('inf')})
        new_entry = new_table.get(destination, {"next_hop": None, "cost": float('inf')})

        if old_entry["next_hop"] != new_entry["next_hop"] or old_entry["cost"] != new_entry["cost"]:
            changed = True
            old_cost = "inf" if old_entry["cost"] == float('inf') else old_entry["cost"]
            new_cost = "inf" if new_entry["cost"] == float('inf') else new_entry["cost"]
            print(f"{destination}: ({old_entry['next_hop']}, {old_cost}) -> ({new_entry['next_hop']}, {new_cost})")

    if not changed:
        print("No routing entry changed.")


# instanciation de 5 routers
if __name__ == "__main__":
    visualizer = Visualizer()

    router_A = Router("A", visualizer)
    router_B = Router("B", visualizer)
    router_C = Router("C", visualizer)
    router_D = Router("D", visualizer)
    router_E = Router("E", visualizer)

    # config de voisin et cost selon le lab
    # enlace de ---- router A-----
    router_A.add_neighbor("B", 5)
    router_A.add_neighbor("E", 3)

    # enlace de ---- router B-----
    router_B.add_neighbor("A", 5)
    router_B.add_neighbor("C", 8)
    router_B.add_neighbor("D", 2)

    # enlace de ---- router C-----
    router_C.add_neighbor("B", 8)
    router_C.add_neighbor("D", 8)
    router_C.add_neighbor("E", 8)

    # enlace de ---- router D-----
    router_D.add_neighbor("B", 2)
    router_D.add_neighbor("C", 8)
    router_D.add_neighbor("E", 3)

    # enlace de ---- router E-----
    router_E.add_neighbor("A", 3)
    router_E.add_neighbor("C", 8)
    router_E.add_neighbor("D", 3)

    # dictionnaire de reseau pour son agrupation
    network = {
        "A": router_A,
        "B": router_B,
        "C": router_C,
        "D": router_D,
        "E": router_E
    }
    visualizer.setNodes(network)
    visualizer.capture()  # initial network

    print("LSA exchanges are running...")

    for _, router in network.items():
        flood_router_lsa(router, network, visualizer)

        # Waiting time to prevent the sending of LSA of all routers at the same time
        # The shorter the waiting time, the more simultaneous traffic there will be.
        time.sleep(2)

    # Waiting all LSA message are finished to transit (impossible in reality)
    wait_for_flooding(visualizer)

    print("\n--------Flooding completed-----------")

    # et on montre le contenue de LSDB
    print("\nContenue du LSDB du Router A:")
    print(router_A.getLSDB())

    print("Contenue du LSDB du Router B:")
    print(router_B.getLSDB())

    show_topologie(router_A)

    old_routing_table_A = router_A.routing_table_from_lsdb()

    print()
    print(f">>> The shortest path from B to E: {router_B.compute_shortest_paths(router_E, network)}\n")
    print(f">>> The shortest path from C to E: {router_C.compute_shortest_paths(router_E, network)}\n")
    print(f">>> The shortest path from A to D: {router_A.compute_shortest_paths(router_D, network)}\n")

    print("\n===== Link failure and routing update: E-D =====")

    # suppression du lien E-D des deux cotes
    router_D.neighbors.pop("E", None)
    router_E.neighbors.pop("D", None)

    # mise a jour visuelle du lien supprime
    visualizer.edges_crashed.append(("D", "E"))
    visualizer.capture()

    # D et E originent de nouveaux LSAs
    flood_router_lsa(router_D, network, visualizer)
    flood_router_lsa(router_E, network, visualizer)

    # attendre la propagation complete du changement
    wait_for_flooding(visualizer)

    print("\n--------Flooding after failure completed-----------")
    print("\nContenue du LSDB du Router A apres la panne:")
    print(router_A.getLSDB())

    show_topologie(router_A)

    new_routing_table_A = router_A.routing_table_from_lsdb()
    print_changed_entries(old_routing_table_A, new_routing_table_A)

    visualizer.show()
