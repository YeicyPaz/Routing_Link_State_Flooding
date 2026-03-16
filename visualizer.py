import os
import time
import graphviz
import threading
import tkinter as tk
from tkinter import ttk
from tkinter import PhotoImage
from LSA import LSA
from Router import Router

# Path to the Graphviz software's bin folder
graphviz_path = os.path.abspath("Graphviz-14.1.2-win64/bin")
# Add to PATH temporarily
os.environ["PATH"] += os.pathsep + graphviz_path

class Visualizer:

    format = "png"
    colors = ["blue", "red", "green", "gold", "purple", "cyan", "magenta", "lime"]

    def __init__(self, img_folder="default", autocapture=False):
        # autocapture permits to capture network when its topology and routing tables change + LSA transmitted
        # but it's not good for showing events that are happening at the same time
        self.img_folder = 'network_img/'+img_folder
        self.clear_img_folder()
        self.nb_img = 0
        self.autocapture = autocapture
        self.nodes = {}         # format: {label: Router}
        self.nodes_colors = {}  # format: {label: color}
        self.edges = {}         # format: [(label_router1, label_router2): link_cost]
        self.edges_lsa = {}     # format: {(label_router_sender, label_router_receiver): [label_router_origins]}
        self.edges_crashed = [] # format: [(label_router1, label_router2)]
        self.nodes_data = {}    # to save LSDB and routing table for each capture   format: {int: {label: string}}
    
    
    def setNodes(self, routers:{str:Router}):
        assert len(routers) <= len(Visualizer.colors), "Impossible to represents more than 10 routers actually"
        self.nodes = routers
        self.nodes_colors = {}
        c = 0
        for router in routers.keys():
            self.nodes_colors[router] = Visualizer.colors[c]
            c += 1


    # Possibility to define all links between routers but not used actually
    # Be careful of duplicate links in both directions
    def setEdges(self, edges:{(str,str):int}):
        self.edges = {}
        self.edges_lsa = {}
        self.edges_crashed = []
        for routers, cost in edges.items():
            self.edges[(routers[0], routers[1])] = cost


    # Used by Router in function add_neighbor
    def addEdge(self, r1, r2, cost):
        if not (r2,r1) in self.edges:  # prevent duplication of link (display one direction only)
            self.edges[(r1,r2)] = cost
    

    def lsaTransit(self, sender:str, receiver:str, origin:str):
        if not (sender, receiver) in self.edges_lsa:
            self.edges_lsa[(sender, receiver)] = [origin]
        else:
            self.edges_lsa[(sender, receiver)].append(origin)
        #print(self.edges_lsa)
    

    def removeTransit(self, sender:str, receiver:str, origin:str):
        try:
            if len(self.edges_lsa[(sender, receiver)]) > 1:
                self.edges_lsa[(sender, receiver)].remove(origin)
            else:
                self.edges_lsa.pop((sender, receiver))
        except: print((sender, receiver, origin), "not in LSA transits")

    
    def clearTransit(self):
        self.edges_lsa = {}
    

    def capture(self):
        # Build network and save as image file
        network = graphviz.Digraph(filename=str(self.nb_img), format=Visualizer.format, graph_attr={'rankdir':'LR'})    # LR to display horizontally
        self.nodes_data[self.nb_img] = {}

        for label, router in self.nodes.items():
            network.node(label, color=self.nodes_colors[label])
            
            # Save LSDB and routing table of router
            # Actually saving data in node tooltip is possible with Graphviz but data can't be exportable in PNG or JPG image
            # SVG preserves tooltips, but this image format is not compatible with Tkinter.
            # The data will therefore be displayed in a dynamic table with router selection.
            lsdb = router.getLSDB()
            data = "----- LSDB -----\n" + (lsdb if len(lsdb) > 0 else "None\n")
            data += "\n----- Routing Table -----\nTarget \tVia \tCost \tPath"
            for other_label, routing in router.routing_table_from_lsdb().items():
                data += f"\n{other_label} \t{routing['next_hop']} \t{routing['cost']} \t{routing['path']}"
            #for other_label, other_router in self.nodes.items():
                #if other_label != label:
                    #path, cost = router.compute_shortest_paths(other_router, self.nodes)
                    #data += f"\n{other_label} \t{path[min(1,len(path))]} \t{cost} \t{path}"
            self.nodes_data[self.nb_img][label] = data
        
        for routers, cost in self.edges.items():
            r1, r2 = routers[0], routers[1]
            if (r1,r2) in self.edges_crashed or (r2,r1) in self.edges_crashed:
                network.edge(r1, r2, style="dashed", color="black", dir='none')
            elif (r1,r2) in self.edges_lsa:
                if (r2,r1) in self.edges_lsa:
                    # two LSAs transits from 2 directions -> display double directed link with colors of the two origin routers that send LSAs
                    color = self.nodes_colors[self.edges_lsa[(r1,r2)][0]] + ":" + self.nodes_colors[self.edges_lsa[(r2,r1)][0]]
                    network.edge(r1, r2, label=str(cost), color=color, dir='both')
                else:
                    # LSA transits from router to one neighbor -> display directed link with color of origin router that send LSA
                    color = ":".join(map(lambda x: self.nodes_colors[x], self.edges_lsa[(r1,r2)]))
                    network.edge(r1, r2, label=str(cost), color=color, dir='forward')
            elif (r2,r1) in self.edges_lsa:
                # As before but in the opposite direction
                color = ":".join(map(lambda x: self.nodes_colors[x], self.edges_lsa[(r2,r1)]))
                network.edge(r1, r2, label=str(cost), color=color, dir='back')    # trick to keep same structure with edge r1 to r2 but inversed arrow
            else:
                # No LSA transits -> display simple link
                network.edge(r1, r2, label=str(cost), color="black", dir='none')

        self.nb_img += 1
        return network.render(directory=self.img_folder)


    def clear_img_folder(self):
        if os.path.isdir(self.img_folder):
            for file in os.listdir(self.img_folder):
                try: os.remove(self.img_folder+'/'+file)
                except: continue
    

    def _create_interface(self):
        self.root = tk.Tk()
        self.root.title("Routing with Link-State Flooding")
        tk.Label(self.root, text="Routing with Link-State Flooding", font="Arial 20").pack()
        
        # Control buttons
        controls = tk.Frame(self.root)
        controls.pack(pady=20)
        self.btn_autoplay = tk.Button(controls, text="▶", command=self._play_stop, fg="blue", font='Arial 20 bold')
        self.btn_back = tk.Button(controls, text="⏮", command=self._back, fg="blue", font='Arial 20 bold')
        self.btn_forward = tk.Button(controls, text="⏭", command=self._forward, fg="blue", font='Arial 18 bold')
        self.progress_bar = ttk.Progressbar(controls, length=400)
        self.btn_back.grid(row=0, column=0, padx=30)
        self.btn_autoplay.grid(row=0, column=1, padx=30)
        self.btn_forward.grid(row=0, column=2, padx=30)
        self.progress_bar.grid(row=1, column=0, columnspan=3, pady=10)

        # Network & Routers Data (LSDB + routing table)
        system_infos = tk.Frame(self.root)
        system_infos.pack(padx=20, pady=20)
        self.network = tk.Label(system_infos)
        self.network.grid(row=0, column=0, padx=30)
        router_data_frame = tk.Frame(system_infos)
        router_data_frame.grid(row=0, column=1, padx=30)
        self.selected_router = tk.StringVar()
        combo = ttk.Combobox(router_data_frame, font='Arial 14 bold', state="readonly", textvariable=self.selected_router)
        combo['values'] = tuple("Router "+label for label in self.nodes.keys())
        combo.bind('<<ComboboxSelected>>', self._upd_router_data)
        combo.pack(pady=5)
        self.router_data = tk.StringVar()
        self.router_data.set("⬆ Select a router ⬆")
        tk.Label(router_data_frame, bg="white", font='Arial 12', relief="groove", justify="left", textvariable=self.router_data).pack(pady=5)

        # Legend
        legend = tk.Frame(self.root, bg="white")
        legend.pack(padx=20, pady=10)
        tk.Label(legend, bg="white", font='Arial 12 bold', text="LSAs in transit:", fg="black").grid(row=0, column=0, padx=15, pady=5)
        i = 0
        for router, color in self.nodes_colors.items():
            i+=1
            tk.Label(legend, bg="white", font='Arial 12 bold', text="→ from "+router, fg=color).grid(row=0, column=i, padx=10)
        tk.Label(legend, bg="white", font='Arial 12 bold', text="- - -  link failure", fg="black").grid(row=1, column=0, columnspan=i+1, padx=10)
    

    def _back(self):
        self.step = max(self.step - 1, 0)
        self._update_system()
    

    def _forward(self):
        self.step = min(self.step + 1, self.nb_img-1)
        self._update_system()
    

    def _play_stop(self):
        if self.thread_autoplaying == None:
            self.thread_autoplaying = threading.Thread(target=self._autoplay)
            self.thread_autoplaying.start()
            self.btn_autoplay.configure(text="⏸")
        else:
            self.thread_autoplaying = None
            self.btn_autoplay.configure(text="▶")
    

    def _autoplay(self):
        while self.step < self.nb_img-1:
            time.sleep(2)
            if self.thread_autoplaying != None:
                self._forward()
            else: return
        self.thread_autoplaying = None
        self.btn_autoplay.configure(text="▶")
    

    def _update_system(self):
        try:
            self.progress_bar.config(value= (self.step)/(self.nb_img-1)*100)   # percentage of progression
            # update image
            image = PhotoImage(file=self.img_folder+'/'+str(self.step)+"."+Visualizer.format)
            self.network.configure(image=image)
            self.network.image = image
            # update router data
            if self.step >= 0: self._upd_router_data(None)
        except Exception as e: print(e)
    

    def _upd_router_data(self, event):
        label_router = self.selected_router.get()[-1]   # assume that the router name consists of a single character
        data = self.nodes_data[self.step][label_router]
        self.router_data.set(data)


    def show(self):
        self._create_interface()
        self.step = 0
        self.thread_autoplaying = None
        self._update_system()
        self.root.mainloop()
