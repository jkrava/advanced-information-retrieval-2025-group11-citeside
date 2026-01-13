import json

import networkx as nx
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from typing import List, Optional
from collections import deque
from CiteSide.ReferenceTreeTools.ScoreCombiner import ScoreCombiner

class ReferenceTreeBuilder:
    def __init__(self):
        self._tree = nx.DiGraph()
        self._crawl_root = None
        self._crawl_depth = None
        self._reverse_depth = None
        self._comb_indexed = False

### GETTERS / SETTERS ###
    def addNode(self, node_id: str):
        if (self._tree.has_node(str)):
            self.warning(f"Adding node {node_id} not possible as it already exists")
        self._tree.add_node(node_id)

    def getEdges(self) -> List[tuple]:
        return list(self._tree.edges(data=True))

    def addEdge(self, source_id: str, target_id: str, weight: float = -1.0):
        self.addEdgeTuple((source_id, target_id, weight))

    def addEdgeTuple(self, edge: tuple):
        if  (len(edge) not in (2,3) or
            not isinstance(edge[0], str) or
            not isinstance(edge[1], str)):
            raise ValueError("Invalid tuple format!")
        elif (not self._tree.has_node(edge[0])):
            self.warning(f"Adding edge from {edge[0]} to {edge[1]} not possible. {edge[0]} is not a node.")
        elif (not self._tree.has_node(edge[1])):
            self.warning(f"Adding edge from {edge[0]} to {edge[1]} not possible. {edge[1]} is not a node.")
        elif self.checkIfCircular(edge[0], edge[1]):
            self.warning(f"Adding edge from {edge[0]} to {edge[1]} would create a cycle. Edge not added.")
        elif (len(edge) == 3 and
            isinstance(edge[0], str) and
            isinstance(edge[1], str) and
            isinstance(edge[2], float)):
            self._tree.add_edge(edge[0], edge[1], weight=edge[2])
        elif (len(edge) == 2 and
            isinstance(edge[0], str) and
            isinstance(edge[1], str)):
            self._tree.add_edge(edge[0], edge[1], weight= -1.0)
        else:
            raise ValueError("Edge must be a tuple of (source_id: str, target_id: str, weight: float)")

    def getReferences(self, node_id: str):
        return list(self._tree.successors(node_id))

    def getWeight(self, source_id: str, target_id: str):
        if self._tree.has_edge(source_id, target_id):
            return self._tree[source_id][target_id].get('weight', None)
        else:
            raise ValueError("Edge from {source_id} to {target_id} does not exist.")

    def changeWeightOfEdge(self, source_id: str, target_id: str, weight: float):
        if self._tree.has_edge(source_id, target_id):
            self._tree[source_id][target_id]['weight'] = weight
        else:
            raise ValueError(f"Edge from {source_id} to {target_id} does not exist.")

    def create(self, nodes: Optional[List[str]] = None, edges: Optional[List[tuple]] = None):
        self._tree.add_nodes_from(nodes)
        for edge in edges:
            self.addEdgeTuple(edge)

    def getLeafs(self):
        return [n for n, deg in self._tree.in_degree if deg == 0]

### VISUALIZATION ###
    def printTree(self):
        reset = "\x1b[0m"

        def fg_escape(r: int, g: int, b: int):
            return f"\x1b[38;2;{r};{g};{b}m"

        def bg_block(r: int, g: int, b: int):
            return f"\x1b[48;2;{r};{g};{b}m  {reset}"

        print("\nLegend (color = depth):")
        samples = [(-1.0, " (blue) reverse crawl depth"), (0.0, " (white) root"), (1.0, " (red) crawl depth")]
        legend_parts = []
        for val, label in samples:
            r, g, b = self.rgbForCrawl(1, val)
            block = bg_block(r, g, b)
            legend_parts.append(f"{block} {label}")
        print("  " + "   ".join(legend_parts))

        print("\nNodes:")
        for n, data in self._tree.nodes(data=True):
            if (self._crawl_root != None):
                depth = data.get("depth")
                r, g, b = 0, 0, 0
                if depth < 0:
                    r, g, b = self.rgbForCrawl(self._reverse_depth, depth)
                else:
                    r, g, b = self.rgbForCrawl(self._crawl_depth, depth)
                color = fg_escape(r, g, b)
                print(f"  {n}: depth={color}{depth}{reset}")
            else:
                print(f"  {n}: {data}")

        print("\nLegend (color = weight):")
        samples = [(-1.0, " -1 (blue) undefined"), (0.0, " 0 (green) non critical"), (1.0, " 1 (red) critical")]
        legend_parts = []
        for val, label in samples:
            r, g, b = self.rgbForWeight(val)
            block = bg_block(r, g, b)
            legend_parts.append(f"{block} {label}")
        print("  " + "   ".join(legend_parts))

        print("\nEdges:")
        for u, v, data in self._tree.edges(data=True):
            weight = data.get("weight", -1)
            r, g, b = self.rgbForWeight(weight)
            color = fg_escape(r, g, b)
            print(f"  {u} -> {v}  weight={color}{weight:.3f}{reset}")

    def plotTree(
            self,
            node_size: int = 300,
            seed: Optional[int] = 42):

        pos = nx.spring_layout(self._tree, seed=seed)
        pos = nx.circular_layout(self._tree, scale=2.0)

        if (self._crawl_root != None):
            #"fdp"/"neato"/"sfdp"(faster version) seems to be the best, but "circo", "twopi", "dot" in this order should also be testet!
            pos = nx.nx_pydot.graphviz_layout(self._tree, prog="neato", root=self._crawl_root)
            nodelist = []
            node_colors = []
            for node, data in self._tree.nodes(data=True):
                depth = data.get("depth", None)
                if depth == None:
                    raise ValueError("Depth could not be None for crawled Trees.")
                if (depth < 0 and self._reverse_depth == None):
                    continue
                nodelist.append(node)
                rgb = self.rgbForCrawl(self._crawl_depth, depth)
                if (depth < 0 and self._reverse_depth != None):
                    rgb = self.rgbForCrawl(self._reverse_depth, depth)
                node_colors.append(self.rgbNorm(rgb))
            nx.draw_networkx_nodes(self._tree, pos, node_size=node_size, node_color=node_colors, nodelist=nodelist)
        else:
            nx.draw_networkx_nodes(self._tree, pos, node_size=node_size, node_color="#88ccee")
        nx.draw_networkx_labels(self._tree, pos, font_size=9)

        edge_colors = []
        edge_widths = []
        for u, v, data in self._tree.edges(data=True):
            w = data.get("weight", -1.0)
            edge_colors.append(self.rgbNorm(self.rgbForWeight(w)))
            try:
                width = 1.0 + abs(float(w)) * 3.0
            except Exception:
                width = 1.0
            edge_widths.append(width)

        nx.draw_networkx_edges(
            self._tree,
            pos,
            edge_color=edge_colors,
            width=edge_widths,
            arrows=True,
            arrowstyle="-|>",
            arrowsize=12,
        )

        cmap = mpl.colors.LinearSegmentedColormap.from_list(
            "green_red", [(1.0, 0.0, 0.0), (0.0, 1.0, 0.0)]
        )
        norm = mpl.colors.Normalize(vmin=0.0, vmax=1.0)
        sm = mpl.cm.ScalarMappable(norm=norm, cmap=cmap)
        sm.set_array(np.linspace(0.0, 1.0, 256))  # non-empty array for the colorbar
        cb = plt.colorbar(sm, ax=plt.gca(), orientation="horizontal", fraction=0.05, pad=0.04)
        cb.set_ticks([0.0, 0.5, 1.0])
        cb.set_ticklabels(["0 (red) critical", "1 (green) non critical"])
        cb.set_label("critical index")

        blue_color = self.rgbNorm(self.rgbForWeight(-1.0))
        blue_patch = mpl.patches.Patch(color=blue_color, label="-1 (blue) unknown")
        ax = plt.gca()
        ax.legend(handles=[blue_patch], loc="upper left", frameon=False, fontsize=9)

        plt.axis("off")
        plt.show()

### IO ###

    def build(self):
        meta = {"crawl_root": self._crawl_root, "crawl_depth": self._crawl_depth, "reverse_depth": self._reverse_depth, "comb_indexed": self._comb_indexed}
        nodes = {n: dict(d) for n, d in self._tree.nodes(data=True)}
        edges = [
            {"source": u, "target": v, "attrs": dict(data)}
            for u, v, data in self._tree.edges(data=True)
        ]
        return {"meta": meta, "nodes": nodes, "edges": edges}


    def store(self, path: str):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.build(), f, indent=2)

    @classmethod
    def load(cls, path: str):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        meta = data.get("meta", {})
        nodes_h = data.get("nodes").keys()
        nodes = [str(n) for n in nodes_h]
        edges_h = data.get("edges", [])
        edges = [(str(e["source"]), str(e["target"]), float(e["attrs"].get("weight", -1.0))) for e in edges_h]
        gb = cls()
        gb.create(nodes, edges)
        gb._crawl_root = meta.get("crawl_root")
        gb._crawl_depth = meta.get("crawl_depth")
        gb._reverse_depth = meta.get("reverse_depth")
        gb._comb_indexed = meta.get("comb_indexed")
        if (gb._crawl_root != None):
            depths = {meta.get("crawl_root"): 0}
            for node, attr in data.get('nodes', {}).items():
                depths[node] = attr["depth"]
            nx.set_node_attributes(gb._tree, depths, name="depth")
        return gb

### HELPERS ###

    def buildCombCritIndex(self, mode: str = ScoreCombiner.MULTIPLICATION):
        if self._comb_indexed:
            return
        for u, v, data in self.getEdges():
            weight = data.get("weight", -1)
            if weight == -1:
                self.warning("Not all edges have an Index - not executing combination Indexing")
                return
        self._comb_indexed = True
        # Creating Crit Index of Nodes:
        crits = {}
        for node in self._tree.nodes():
            total = 0.0
            count = 0
            for u, v, data in self._tree.out_edges(node, data=True):
                weight = float(data.get("weight"))
                total += weight
                count += 1
            crits[node] = (total / count) if count > 0 else -1.0
        nx.set_node_attributes(self._tree, crits, name="critical")

        # Creating Combination of Edge and Node Index:
        for u, v, data in self.getEdges():
            edge_weight = float(data.get("weight"))
            attr = self._tree.nodes[v]
            node_weight = float(attr.get("critical"))
            combined = ScoreCombiner.combineCrits(node_weight, edge_weight, mode)
            self._tree[u][v]['base_weight'] = edge_weight
            self._tree[u][v]['weight'] = combined


    def buildCrawlTree(self, start_node: str, max_depth: int, reverse_depth: Optional[int] = None):
        if start_node not in self._tree:
            raise ValueError(f"Start node {start_node} does not exist in the graph.")

        visited = {start_node}
        q = deque([start_node])
        d = deque([0])
        edges = []
        depths = {start_node: 0}

        while q:
            node = q.popleft()
            depth = d.popleft()
            if depth >= max_depth:
                continue
            for nbr in self._tree.successors(node):
                weight = self._tree[node][nbr].get("weight", -1.0)
                edges.append((str(node), str(nbr), weight))
                if nbr not in visited:
                    visited.add(nbr)
                    depths[nbr] = depth + 1
                    q.append(nbr)
                    d.append(depth + 1)

        q = deque([start_node])
        d = deque([0])
        if (reverse_depth != None):
            reverse_depth = -abs(reverse_depth)

        while q and reverse_depth != None:
            node = q.popleft()
            depth = d.popleft()
            if depth <= reverse_depth:
                continue
            for nbr in self._tree.predecessors(node):
                weight = self._tree[nbr][node].get("weight", -1.0)
                edges.append((str(nbr), str(node), weight))
                if nbr not in visited:
                    visited.add(nbr)
                    depths[nbr] = depth - 1
                    q.append(nbr)
                    d.append(depth - 1)

        tree = self.__class__()
        tree.create(visited, edges)

        tree._crawl_root = start_node
        tree._crawl_depth = max_depth
        tree._reverse_depth = reverse_depth

        nx.set_node_attributes(tree._tree, depths, name="depth")
        return tree


    def checkIfCircular(self, source_id: str, target_id: str):
        if source_id == target_id or nx.has_path(self._tree, target_id, source_id):
            return True
        return False

    def warning(self, msg: str):
        yellow = "\x1b[93m"  # bright yellow
        reset = "\x1b[0m"
        prefix = "WARNING! "
        print(f"{yellow}{prefix}{msg}{reset}")

    def interp(self, a: int, b: int, t: float) -> int:
        #this interpolates the gradient from one color to another
        return int(round(a + (b - a) * t))


    def rgbForCrawl(self, depth: int, w: int):
        w_h = float(w)/ float(abs(depth))
        # -1 -> blue (0,0,255)
        #  0 -> white (255,255,255)
        #  1 -> red (255,0,0)
        if w_h <= 0:
            t = (w_h + 1.0) / 1.0  # 0-1
            r = self.interp(0, 255, t)
            g = self.interp(0, 255, t)
            b = self.interp(255, 255, t)
        else:
            t = w_h / 1.0  # 0-1
            r = self.interp(255, 255, t)
            g = self.interp(255, 0, t)
            b = self.interp(255, 0, t)
        return r, g, b

    def rgbForWeight(self, w: float):
        w = max(-1.0, min(1.0, w))
        # -1 -> blue (0,0,255)
        #  0 -> green (0,255,0)
        #  1 -> red (255,0,0)
        if w <= 0:
            t = (w + 1.0) / 1.0  # 0-1
            r = self.interp(0, 255, t)
            g = self.interp(0, 255, t)
            b = self.interp(255, 255, t)
        else:
            t = w / 1.0  # 0-1
            r = self.interp(255, 0, t)
            g = self.interp(0, 255, t)
            b = self.interp(0, 0, t)
        return r, g, b

    def rgbNorm(self, rgb):
        r, g, b = rgb
        return (r / 255.0, g / 255.0, b / 255.0)
