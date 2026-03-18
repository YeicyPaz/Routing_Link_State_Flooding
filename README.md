# Routing Under Dynamics : Link-State Flooding

*This project illustrates how routers build a consistent view of the network using link-state flooding and how routing information is updated after a link failure*

## Requirement
- Python environment
- [Graphviz Python library](https://pypi.org/project/graphviz/): ```pip install graphviz```
- [Graphviz software](https://graphviz.org/) installed if you are using UNIX. On Windows, the software is integrated into the repository (no actions required).

## Running

The example involves representing a mini-network of 5 routers (A, B, C, D, E). They will initially exchange LSA messages to inform other routers of their neighbors (link-state flooding) so they can build their routing tables. Then, a link failure will occur between E and D. The new LSA messages sent will update the routing tables.

The implementation of this example is described in the main script **Main.py** (the program to run).

### Initial Network State
Initially, the 5 routers have several links between them (not a complete graph) with different costs. Their link-state database (LSDB) and routing table are empty. They only know their neighbors.

### LSA Exchanges
In reality, Link Support Attachments (LSAs) are periodically sent by routers to their neighbors to ensure the network topology is properly updated everywhere. In this example, there will only be two iterations of the exchange: one before the link failure (network initialization) and one after.

When an LSA is received by a router, it can be retransmitted to its neighbors. It was advantageous to represent simultaneous LSA transmissions rather than sequential ones with a recursive call stack. [Threading](https://docs.python.org/3/library/threading.html) was therefore used to send LSAs in parallel and simulate the concurrency that exists between routers in reality. A short, random but bounded transmission delay was also implemented to reflect the presence of latency in the network. The fact that transmission times are random leads to differences in the order of exchanged messages (visualized via the graphical interface), and this allows verification that the router states are the same at the end regardless of the order.

To avoid an overloaded representation of exchanged LSA messages in the graphical interface, the initialization of an LSA to be sent is staggered by 2 seconds for each router in this order: A, B, C, D, E. This can, however, be changed.

The use of strictly increasing sequence numbers for LSAs allows routers to retain only the most recent messages, guaranteeing the end of flooding and thus the termination property.

### LSDB and routing table update
A router's link-state database (LSDB) contains all recent and unexpired LSAs from other routers. It is used to compute the router's routing table using [Dijkstra's algorithm](https://en.wikipedia.org/wiki/Dijkstra%27s_algorithm) for shortest path calculation.

During the simulation, the LSDB, and therefore each router's routing table, is updated based on the received LSAs.

### Link failure
After all LSA messages had been exchanged between the routers (end of the first iteration), a link failure between routers D and E was simulated. Routing directly from D to E was then no longer possible, and vice versa.

A new LSA exchange iteration was performed, with only routers D and E initiating the exchange for simplicity. These new transmissions notified all routers of the network topology change so they could update their routing tables accordingly.

### Graphical Visualization of the Simulation
During the simulation, several snapshots of the router states (LSDB + routing table) and the LSAs being transmitted were taken and modeled as graphs using the Graphviz tool. PNG images of the models were exported to the hard drive for later viewing.

After the simulation ended, a basic Tkinter graphical interface was launched, allowing the user to scroll through the different snapshots in order to better understand how routing tables are updated (after a link failure). The image folder can also be retrieved from **network_img/**.

#### Example: Snapshot 1
![Example Snapshot](https://github.com/YeicyPaz/Routing_Link_State_Flooding/blob/main/network_img/readme/screenshot1.png?raw=true)
Here is an example of a system state capture using the graphical interface. You can see:
- the network topology as a graph with the different routers represented by nodes, the links between routers by edges with their transmission costs
- the LSA messages __currently being transmitted__ from the different originating routers
- the state of each router (selection list) with their LSDB and routing table

Here, router A is selected. According to its LSDB, it hasn't yet received the LSA from router C, but it knows a path to reach it (via B) thanks to the LSA from router B received previously. LSAs originating from C are currently being transmitted to A from both B and E. The next screenshot will show the reception of one of these transmissions.

If we consider the case of the simultaneous, two-way transmission of the same LSA between B and D, or between D and E, this is perfectly normal because neither of these routers yet knows that they will receive this LSA between themselves (the transmissions are concurrent).

#### Example: Snapshot 2
![Example Snapshot](https://github.com/YeicyPaz/Routing_Link_State_Flooding/blob/main/network_img/readme/screenshot2.png?raw=true)
In this second screenshot, we can see that router A successfully received the LSA from router C via router E (receiving it via router B first would have yielded the same result because the list of C's neighbors contained in the LSA remains unchanged during transmission). This LSA was added to router A's LSDB, and its routing table was updated because a shorter path was found to reach C: via E, with a cost of 11 (3+8), lower than the previous cost of 13 (5+8) via B.

We can also see that A is retransmitting the LSA from C to B because it has not yet received the same LSA from that router.

## Contributors:
- **Gabriel BELTZER**
- **Titouan HINSCHBERGER**
- **Klaudia KUBALE**
- **Yeicy PAZ CORDOBA**

*M1 ISA 2025-2026 Université de Tours*
