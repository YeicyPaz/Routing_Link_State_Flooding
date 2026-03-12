#c'est la classe pour la creation des messages type link-state advertisements: 
#la class dataclasses en python nous permetre de garde les informations consernants à l'origine au nombre de sequence,
# l'age, le dictionnaire des routers voisins


from dataclasses import dataclass
from typing import Dict

#Un LSA c'est un type de message qui se envoie entre routers
@dataclass
class LSA:
    origin:str              #quelle router à generé le message, le A ou B? Les routers sont {A,B,C,D,E}
    seq:int                 #le nombre de sequence pour savoir si c'est nouveau ou ancien le message
    age:int                 #le temp de vie que reste par rapport au message (aging)
    neighbors:Dict[str,int] #dictionaire de conectivité local: {voisin: coûte}