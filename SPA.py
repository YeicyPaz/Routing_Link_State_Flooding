from heapq import heapify, heappop, heappush

def compute_shortest_paths(routers, start, target): #Dijkstra algorithme
    
    distances = {router: (float('inf'), None) for router in routers}  # on initialise les couts à l'infini
    distances[start] = (0, None)  #le  cout pour le router de départ est de 0
    # visiter les voisins du noeud actuel et mettre à jour les couts
    #on fait une file de priorité
    pq = [(0,start)]
    pq.heapify() #on transforme en min-heap
    visited = set()
    while pq: #tant que la priority queue n'est pas vide
        current_distance, current_node = heappop(pq) #on récupere le noeud avec la plus petite distance
        if current_node in visited:
            continue #on ignore les noeuds deja visités
        visited.add(current_node)
        for neighbor, cost in distances[start].neighbors.items():
            #additionner la distance
            tentative_distance = current_distance + cost
            if tentative_distance < distances[neighbor]:
                distances[neighbor] = tentative_distance
                heappush(pq, (tentative_distance, neighbor))
    return distances[target]

    #choisir le noeuds qui est 
