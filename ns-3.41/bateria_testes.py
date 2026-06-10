import os
import subprocess
import sys
import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt

NS3_EXECUTABLE = "./ns3"
SCRIPT_NAME = "dual_radio_topology"
RESULTS_DIR = "resultados_simulacao"

PACKET_SIZES = [128, 256, 512, 1024]
INTERVALS = [0.05, 0.02, 0.01, 0.005]

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
    total = len(PACKET_SIZES) * len(INTERVALS)

    for size in PACKET_SIZES:
        for interval in INTERVALS:
            print(f"[{test_counter}/{total}] Size={size}B | Int={interval}s")
            cmd = [NS3_EXECUTABLE, "run", f"scratch/{SCRIPT_NAME} --packetSize={size} --interval={interval} --maxPackets=500 --distance=15.0 --simTime=50.0 --enableCross=true --crossInterval={interval}"]
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            thr, pdr, dly = parse_flowmon("flowmon-results.xml")
            results.append((size, interval, thr, pdr, dly))
            test_counter += 1

    table_data = []
    for r in results: table_data.append([str(r[0]), str(r[1]), f"{r[2]:.2f}", f"{r[3]:.2f}", f"{r[4]:.4f}"])

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.axis('tight')
    ax.axis('off')
    headers = ['Tamanho (B)', 'Intervalo (s)', 'Vazão (Kbps)', 'Entrega (%)', 'Atraso (s)']
    table = ax.table(cellText=table_data, colLabels=headers, loc='center', cellLoc='center')
    table.scale(1, 1.5)
    plt.title('Resultados Bateria 1: Estresse de Carga')
    plt.savefig(os.path.join(RESULTS_DIR, 'tabela_b1_carga.png'), bbox_inches='tight')
    plt.close()

    plt.figure(figsize=(10, 6))
    for interval in INTERVALS:
        thr_vals = [r[2] for r in results if r[1] == interval]
        plt.plot(PACKET_SIZES, thr_vals, marker='o', label=f'Int {interval}s')
    plt.title('Vazão da Rede por Carga de Tráfego')
    plt.xlabel('Tamanho do Pacote (Bytes)')
    plt.ylabel('Vazão (Kbps)')
    plt.grid(True)
    plt.legend()
    plt.savefig(os.path.join(RESULTS_DIR, 'grafico_b1_vazao.png'))
    plt.close()

    plt.figure(figsize=(10, 6))
    for interval in INTERVALS:
        pdr_vals = [r[3] for r in results if r[1] == interval]
        plt.plot(PACKET_SIZES, pdr_vals, marker='s', label=f'Int {interval}s')
    plt.title('Taxa de Entrega por Carga de Tráfego')
    plt.xlabel('Tamanho do Pacote (Bytes)')
    plt.ylabel('Taxa de Entrega (%)')
    plt.grid(True)
    plt.legend()
    plt.savefig(os.path.join(RESULTS_DIR, 'grafico_b1_pdr.png'))
    plt.close()

    plt.figure(figsize=(10, 6))
    for interval in INTERVALS:
        dly_vals = [r[4] for r in results if r[1] == interval]
        plt.plot(PACKET_SIZES, dly_vals, marker='^', label=f'Int {interval}s')
    plt.title('Atraso Médio por Carga de Tráfego')
    plt.xlabel('Tamanho do Pacote (Bytes)')
    plt.ylabel('Atraso Médio (s)')
    plt.grid(True)
    plt.legend()
    plt.savefig(os.path.join(RESULTS_DIR, 'grafico_b1_atraso.png'))
    plt.close()

if __name__ == "__main__": run()