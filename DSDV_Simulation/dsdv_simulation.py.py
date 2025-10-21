# -*- coding: utf-8 -*-
"SIMULATION OF DSDV ROUTING PROTOCOL:REACTION TO LINK FAILURES AND ROUTING TABLE CONVERGENCE"

import random
import time
import networkx as nx
import matplotlib.pyplot as plt

# -------------------------------
# DSDV Node Representation
# -------------------------------
class Node:
    def __init__(self, node_id):
        self.id = node_id
        self.routing_table = {}

    def initialize_table(self, graph):
        """Initialize routing table with direct neighbors"""
        for n in graph.nodes():
            if n == self.id:
                self.routing_table[n] = (self.id, 0, 0)
            elif graph.has_edge(self.id, n):
                self.routing_table[n] = (n, 1, 0)
            else:
                self.routing_table[n] = (None, float("inf"), -1)

    def update_table(self, neighbor_table, neighbor_id):
        """DSDV Update rule"""
        updated = False
        for dest, (nh, hc, seq) in neighbor_table.items():
            if dest == self.id:
                continue
            current = self.routing_table.get(dest, (None, float("inf"), -1))
            if seq > current[2] or (seq == current[2] and hc + 1 < current[1]):
                self.routing_table[dest] = (neighbor_id, hc + 1, seq)
                updated = True
        return updated

    def invalidate_route(self, dest):
        """Mark route invalid on link failure"""
        nh, hc, seq = self.routing_table.get(dest, (None, float("inf"), -1))
        self.routing_table[dest] = (None, float("inf"), seq + 1)


# -------------------------------
# DSDV Simulation
# -------------------------------
class DSDVSimulation:
    def __init__(self, num_nodes=5):
        self.graph = nx.Graph()
        self.nodes = {i: Node(i) for i in range(num_nodes)}
        self.graph.add_nodes_from(self.nodes.keys())
        self.control_messages = 0

        # Randomly connect nodes
        for i in range(num_nodes):
            for j in range(i + 1, num_nodes):
                if random.random() < 0.6:
                    self.graph.add_edge(i, j)

        # Initialize routing tables
        for node in self.nodes.values():
            node.initialize_table(self.graph)

    def broadcast_updates(self):
        converged = False
        while not converged:
            converged = True
            for i, node in self.nodes.items():
                for neighbor in list(self.graph.neighbors(i)):
                    updated = self.nodes[neighbor].update_table(node.routing_table, i)
                    self.control_messages += 1
                    if updated:
                        converged = False

    def introduce_link_failure(self, u, v):
        if self.graph.has_edge(u, v):
            self.graph.remove_edge(u, v)
            self.nodes[u].invalidate_route(v)
            self.nodes[v].invalidate_route(u)

    def simulate_packet_delivery(self, num_packets=30):
        delivered = 0
        total_delay = 0
        for _ in range(num_packets):
            src, dst = random.sample(list(self.nodes.keys()), 2)
            route = self.get_route(src, dst)
            if route:
                delivered += 1
                total_delay += len(route)
        pdr = delivered / num_packets
        avg_delay = total_delay / delivered if delivered > 0 else float("inf")
        return pdr, avg_delay

    def get_route(self, src, dst):
        path = [src]
        current = src
        visited = set()
        while current != dst and current not in visited:
            visited.add(current)
            next_hop, hc, seq = self.nodes[current].routing_table.get(dst, (None, float("inf"), -1))
            if next_hop is None or hc == float("inf"):
                return None
            path.append(next_hop)
            current = next_hop
        return path if current == dst else None

    def run(self, fail_link=(0, 1)):
        # Initial convergence
        self.broadcast_updates()
        pdr_before, delay_before = self.simulate_packet_delivery()

        # Introduce failure
        start = time.time()
        self.introduce_link_failure(*fail_link)
        self.broadcast_updates()
        end = time.time()

        convergence_time = end - start
 #Before any failure the simulation sends random packets between nodes.        
        pdr_after, delay_after = self.simulate_packet_delivery()

        return {
            "pdr": pdr_after,
            "delay": delay_after,
            "overhead": self.control_messages,
            "convergence": convergence_time,
        }


# -------------------------------
# Run Multiple Experiments & Plot
# -------------------------------
if __name__ == "__main__":
    node_counts = range(4, 26)  # vary nodes from 4 → 10
    results = {"nodes": [], "pdr": [], "delay": [], "overhead": [], "convergence": []}

    for n in node_counts:
        sim = DSDVSimulation(num_nodes=n)
        metrics = sim.run()
        results["nodes"].append(n)
        results["pdr"].append(metrics["pdr"])
        results["delay"].append(metrics["delay"])
        results["overhead"].append(metrics["overhead"])
        results["convergence"].append(metrics["convergence"])
        print(f"Nodes={n}: {metrics}")

    # Plot graphs
plt.figure()
plt.plot(results["nodes"], results["pdr"], marker="o")
plt.xlabel("Number of Nodes")
plt.ylabel("Packet Delivery Ratio (PDR)")
plt.title("PDR vs Number of Nodes")
plt.grid(True)
plt.savefig("PDR_vs_Nodes.png")
plt.show()

plt.figure()
plt.plot(results["nodes"], results["delay"], marker="o", color="orange")
plt.xlabel("Number of Nodes")
plt.ylabel("Average End-to-End Delay")
plt.title("Delay vs Number of Nodes")
plt.grid(True)
plt.savefig("Delay_vs_Nodes.png")
plt.show()

plt.figure()
plt.plot(results["nodes"], results["overhead"], marker="o", color="red")
plt.xlabel("Number of Nodes")
plt.ylabel("Routing Overhead (Control Messages)")
plt.title("Overhead vs Number of Nodes")
plt.grid(True)
plt.savefig("Overhead_vs_Nodes.png")
plt.show()

plt.figure()
plt.plot(results["nodes"], results["convergence"], marker="o", color="green")
plt.xlabel("Number of Nodes")
plt.ylabel("Convergence Time (seconds)")
plt.title("Convergence Time vs Number of Nodes")
plt.grid(True)
plt.savefig("Convergence_vs_Nodes.png")
plt.show()
