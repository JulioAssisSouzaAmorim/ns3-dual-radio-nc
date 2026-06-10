import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import networkx as nx

def plot_topology():
    G = nx.DiGraph()

    pos = {
        0: (0, 0),
        1: (15, 0),
        2: (30, 0),
        3: (0, 15),
        4: (15, 15),
        5: (30, 15)
    }

    for n in range(6):
        G.add_node(n)

    color_map = {
        0: '#3498db',
        5: '#2ecc71',
        3: '#9b59b6',
        1: '#e74c3c',
        4: '#e67e22',
        2: '#95a5a6'
    }

    node_colors = [color_map[n] for n in G.nodes()]

    labels = {
        0: "No 0\n(Origem)",
        1: "No 1\n(Agressor)",
        2: "No 2\n(Relay)",
        3: "No 3\n(Encoder)",
        4: "No 4\n(Vitima)",
        5: "No 5\n(Destino)"
    }

    plt.figure(figsize=(11, 7))
    ax = plt.gca()

    for n, (x, y) in pos.items():
        circle = plt.Circle((x, y), 18, color=color_map[n], alpha=0.1)
        ax.add_patch(circle)

    nx.draw_networkx_edges(G, pos, edgelist=[(0, 3)], edge_color='#3498db', width=3, arrows=True, arrowsize=20, arrowstyle='-|>', connectionstyle='arc3,rad=0.1', node_size=2500)
    nx.draw_networkx_edges(G, pos, edgelist=[(3, 4), (4, 5)], edge_color='#3498db', style='dashed', width=2, arrows=True, arrowsize=15, node_size=2500)
    nx.draw_networkx_edges(G, pos, edgelist=[(1, 4)], edge_color='#e74c3c', width=3, arrows=True, arrowsize=20, arrowstyle='-|>', connectionstyle='arc3,rad=-0.1', node_size=2500)

    nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=2500, edgecolors='white', linewidths=2)
    nx.draw_networkx_labels(G, pos, labels=labels, font_size=9, font_weight='bold', font_color='black')

    plt.title('Topologia Dual Radio - Trafego Cruzado e Network Coding', fontsize=14, fontweight='bold', pad=20)
    plt.axis('equal')
    plt.axis('off')

    legend_patches = [
        mpatches.Patch(color='#3498db', label='Fluxo Principal (0 -> 5)'),
        mpatches.Patch(color='#e74c3c', label='Trafego Cruzado (1 -> 4)'),
        mpatches.Patch(color='#9b59b6', label='Ponto de Interceptacao (XOR)'),
        mpatches.Patch(color='#ccc', alpha=0.5, label='Raio de Alcance Fisico (18m)')
    ]
    plt.legend(handles=legend_patches, loc='center left', bbox_to_anchor=(1.0, 0.5))

    plt.tight_layout()
    plt.savefig('diagrama_topologia.png', dpi=300, bbox_inches='tight')
    print("Diagrama gerado: diagrama_topologia.png")

if __name__ == "__main__":
    plot_topology()