# python
import json
import networkx as nx
import matplotlib.pyplot as plt
from typing import Any, Dict, List, Optional
from numpy.f2py.auxfuncs import throw_error


class ReferenceTreeBuilder:
    def __init__(self):
        self._tree = nx.DiGraph()

### GETTERS / SETTERS ###

    def addNode(self, node_id: str):
        self._tree.add_node(node_id)

    def getEdges(self) -> List[tuple]:
        return list(self._tree.edges(data=True))

    def addEdge(self, source_id: str, target_id: str, weight: float = -1.0):
        self.addEdgeTuple((source_id, target_id, weight))

    def addEdgeTuple(self, edge: tuple):
        if self.checkIfCercular(edge[0], edge[1]):
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
            throw_error("Edge must be a tuple of (source_id: str, target_id: str, weight: float)")

    def getWeight(self, source_id: str, target_id: str):
        if self._tree.has_edge(source_id, target_id):
            return self._tree[source_id][target_id].get('weight', None)
        else:
            throw_error("Edge from {source_id} to {target_id} does not exist.")

    def changeWeightOfEdge(self, source_id: str, target_id: str, weight: float):
        if self._tree.has_edge(source_id, target_id):
            self._tree[source_id][target_id]['weight'] = weight
        else:
            throw_error(f"Edge from {source_id} to {target_id} does not exist.")

    def create(self, nodes: Optional[List[str]] = None, edges: Optional[List[tuple]] = None):
        self._tree.add_nodes_from(nodes)
        for edge in edges:
            self.addEdgeTuple(edge)

### VISUALIZATION ###

    def printTree(self):
        reset = "\x1b[0m"

        def fg_escape(r: int, g: int, b: int) -> str:
            return f"\x1b[38;2;{r};{g};{b}m"

        def bg_block(r: int, g: int, b: int) -> str:
            return f"\x1b[48;2;{r};{g};{b}m  {reset}"

        print("Nodes:")
        for n, data in self._tree.nodes(data=True):
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
            try:
                weight_f = float(weight)
            except Exception:
                weight_f = -1.0
            r, g, b = self.rgbForWeight(weight_f)
            color = fg_escape(r, g, b)
            print(f"  {u} -> {v}  weight={color}{weight_f:.3f}{reset}")

    def plotTree(
            self,
            filename: Optional[str] = None,
            node_size: int = 300,
            seed: Optional[int] = 42):

        pos = nx.spring_layout(self._tree, seed=seed)
        pos = nx.circular_layout(self._tree, scale=2.0)
        #TODO: add more layout options if needed in the future

        nx.draw_networkx_nodes(self._tree, pos, node_size=node_size, node_color="#88ccee")
        nx.draw_networkx_labels(self._tree, pos, font_size=9)

        edge_colors = []
        edge_widths = []
        for u, v, data in self._tree.edges(data=True):
            w = data.get("weight", -1.0)
            edge_colors.append(self.rgbForWeightNorm(w))
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

        plt.axis("off")
        if filename:
            plt.savefig(filename, bbox_inches="tight", dpi=150)
            plt.close()
        else:
            plt.show()

    def printCrawl(self, start_node: str, max_depth: int):
        #TODO: implement a print method for the crawlTree
        pass

    def plotCrawl(self, start_node: str, max_depth: int, filename: Optional[str] = None):
        #TODO: implement a plot method for the crawlTree
        pass

### IO ###

    def build(self) -> Dict[str, Any]:
        nodes = {n: dict(d) for n, d in self._tree.nodes(data=True)}
        edges = [
            {"source": u, "target": v, "attrs": dict(data)}
            for u, v, data in self._tree.edges(data=True)
        ]
        return {"nodes": nodes, "edges": edges}

    def store(self, path: str):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.build(), f, indent=2)

    @classmethod
    def load(cls, path: str):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        nodes_h = data.get("nodes").keys()
        nodes = [str(n) for n in nodes_h]
        edges_h = data.get("edges", [])
        edges = [(str(e["source"]), str(e["target"]), float(e["attrs"].get("weight", -1.0))) for e in edges_h]
        gb = cls()
        gb.create(nodes, edges)
        return gb

### HELPERS ###
    def crawlTree(self, start_node: str, max_depth: int):
        #TODO: implement a tree crawl method which returns a build which can be stored and loaded
        pass

    def checkIfCercular(self, source_id: str, target_id: str):
        if source_id == target_id or nx.has_path(self._tree, target_id, source_id):
            return True
        return False

    def warning(self, msg: str):
        yellow = "\x1b[93m"  # bright yellow
        reset = "\x1b[0m"
        prefix = "WARNING! "
        print(f"{yellow}{prefix}{msg}{reset}")

    def rgbForWeight(self, w: float):

        def interp(a: int, b: int, t: float) -> int:
            return int(round(a + (b - a) * t))

        try:
            w = float(w)
        except Exception:
            w = -1.0
        w = max(-1.0, min(1.0, w))
        # -1 -> blue (0,0,255)
        #  0 -> green (0,255,0)
        #  1 -> red (255,0,0)
        if w <= 0:
            # interpolate blue -> green for w in [-1,0]
            t = (w + 1.0) / 1.0  # 0-1
            r = interp(0, 0, t)
            g = interp(0, 255, t)
            b = interp(255, 0, t)
        else:
            # interpolate green -> red for w in (0,1]
            t = w / 1.0  # 0-1
            r = interp(0, 255, t)
            g = interp(255, 0, t)
            b = interp(0, 0, t)
        return r, g, b

    def rgbForWeightNorm(self, w: float):
        r, g, b = self.rgbForWeight(w)
        return (r / 255.0, g / 255.0, b / 255.0)
