import os
import subprocess
import sys
import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt

NS3_EXECUTABLE = "./ns3"
SCRIPT_NAME = "dual_radio_topology"
RESULTS_DIR = "resultados_simulacao"

DISTANCES = [15.0, 18.0, 18.5, 18.6, 18.7, 18.8, 18.9, 19.0, 20.0] 

def parse_flowmon(xml_file):
    if not os.path.exists(xml_file): return 0.0, 0.0, 0.0
    tree = ET.parse(xml_file)
    root = tree.getroot()
    flow = root.find('.//FlowStats/Flow[@flowId="1"]')
    if flow is None: return 0.0, 0.0, 0.0
    tx_packets = int(flow.get('txPackets', 0))
    rx_packets = int(flow.get('rxPackets', 0))
    rx_bytes = int(flow.get('rxBytes', 0))
    delay_sum = str(flow.get('delaySum', '0ns'))
    delay_val = 0.0
    if 'ns' in delay_sum:
        try: delay_val = float(delay_sum.replace('+', '').replace('ns', '')) / 1e9
        except ValueError: pass
    delivery_ratio = (rx_packets / tx_packets * 100) if tx_packets > 0 else 0
    throughput_kbps = (rx_bytes * 8) / 1000 / 50.0 
    avg_delay = (delay_val / rx_packets) if rx_packets > 0 else 0.0
    return throughput_kbps, delivery_ratio, avg_delay

def run():
    if not os.path.exists(RESULTS_DIR): os.makedirs(RESULTS_DIR)
    results = []
    test_counter = 1
    total = len(DISTANCES)
    fixed_size, fixed_interval = 1024, 0.05

    for dist in DISTANCES:
        print(f"[{test_counter}/{total}] Dist={dist}m")
        cmd = [NS3_EXECUTABLE, "run", f"scratch/{SCRIPT_NAME} --packetSize={fixed_size} --interval={fixed_interval} --maxPackets=500 --distance={dist} --simTime=50.0 --enableCross=false"]
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        thr, pdr, dly = parse_flowmon("flowmon-results.xml")
        results.append((dist, thr, pdr, dly))
        test_counter += 1

    table_data = []
    for r in results: table_data.append([f"{r[0]:.1f}", f"{r[1]:.2f}", f"{r[2]:.2f}", f"{r[3]:.4f}"])

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.axis('tight')
    ax.axis('off')
    headers = ['Distância (m)', 'Vazão (Kbps)', 'Entrega (%)', 'Atraso (s)']
    table = ax.table(cellText=table_data, colLabels=headers, loc='center', cellLoc='center')
    table.scale(1, 1.5)
    plt.title('Resultados Bateria 2: Degradação de Sinal (Fina)')
    plt.savefig(os.path.join(RESULTS_DIR, 'tabela_b2_distancia.png'), bbox_inches='tight')
    plt.close()

    dists_plot = [r[0] for r in results]
    pdr_vals = [r[2] for r in results]
    plt.figure(figsize=(10, 6))
    plt.plot(dists_plot, pdr_vals, marker='s', color='red')
    plt.title('Degradação do Sinal: Taxa de Entrega por Distância')
    plt.xlabel('Distância entre Nós (Metros)')
    plt.ylabel('Pacotes Entregues (%)')
    plt.grid(True)
    plt.savefig(os.path.join(RESULTS_DIR, 'grafico_b2_pdr.png'))
    plt.close()

    thr_vals = [r[1] for r in results]
    plt.figure(figsize=(10, 6))
    plt.plot(dists_plot, thr_vals, marker='o', color='blue')
    plt.title('Degradação do Sinal: Vazão por Distância')
    plt.xlabel('Distância entre Nós (Metros)')
    plt.ylabel('Vazão (Kbps)')
    plt.grid(True)
    plt.savefig(os.path.join(RESULTS_DIR, 'grafico_b2_vazao.png'))
    plt.close()

if __name__ == "__main__": run()