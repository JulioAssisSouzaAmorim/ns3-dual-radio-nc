import os
import subprocess
import sys
import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt

NS3_EXECUTABLE = "./ns3"
SCRIPT_NAME = "dual_radio_topology"
RESULTS_DIR = "resultados_simulacao"

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
    fixed_size, fixed_interval, dist = 1024, 0.05, 15.0
    
    cmd = [NS3_EXECUTABLE, "run", f"scratch/{SCRIPT_NAME} --packetSize={fixed_size} --interval={fixed_interval} --maxPackets=500 --distance={dist} --simTime=50.0 --enableCross=false"]
    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    thr, pdr, dly = parse_flowmon("flowmon-results.xml")
    results.append((0.0, thr, pdr, dly))

    current_cross_int = 0.1
    min_cross_int = 0.001
    
    while current_cross_int >= min_cross_int:
        cmd = [NS3_EXECUTABLE, "run", f"scratch/{SCRIPT_NAME} --packetSize={fixed_size} --interval={fixed_interval} --maxPackets=500 --distance={dist} --simTime=50.0 --enableCross=true --crossInterval={current_cross_int}"]
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        thr, pdr, dly = parse_flowmon("flowmon-results.xml")
        results.append((current_cross_int, thr, pdr, dly))
        
        if pdr < 5.0: break
        if pdr > 90.0: current_cross_int *= 0.5
        else: current_cross_int *= 0.75

    table_data = []
    plot_rates, plot_thr, plot_pdr, plot_dly = [], [], [], []
    
    for r in results:
        cross_rate = 0 if r[0] == 0.0 else (1.0 / r[0])
        table_data.append([f"{cross_rate:.1f}", f"{r[1]:.2f}", f"{r[2]:.2f}", f"{r[3]:.4f}"])
        plot_rates.append(cross_rate)
        plot_thr.append(r[1])
        plot_pdr.append(r[2])
        plot_dly.append(r[3])
        
    sorted_indices = sorted(range(len(plot_rates)), key=lambda k: plot_rates[k])
    plot_rates = [plot_rates[i] for i in sorted_indices]
    plot_thr = [plot_thr[i] for i in sorted_indices]
    plot_pdr = [plot_pdr[i] for i in sorted_indices]
    plot_dly = [plot_dly[i] for i in sorted_indices]
    table_data = [table_data[i] for i in sorted_indices]

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.axis('tight')
    ax.axis('off')
    headers = ['Taxa Agressão (Pacotes/s)', 'Vazão (Kbps)', 'Entrega (%)', 'Atraso (s)']
    table = ax.table(cellText=table_data, colLabels=headers, loc='center', cellLoc='center')
    table.scale(1, 1.5)
    plt.title('Resultados Bateria 3: Interferência')
    plt.savefig(os.path.join(RESULTS_DIR, 'tabela_b3_interferencia.png'), bbox_inches='tight')
    plt.close()

    plt.figure(figsize=(10, 6))
    plt.plot(plot_rates, plot_thr, marker='o', color='blue')
    plt.title('Impacto da Colisão na Vazão Principal')
    plt.xlabel('Taxa de Tráfego Cruzado (Pacotes/s)')
    plt.ylabel('Vazão do Fluxo Principal (Kbps)')
    plt.grid(True)
    plt.savefig(os.path.join(RESULTS_DIR, 'grafico_b3_vazao.png'))
    plt.close()

    plt.figure(figsize=(10, 6))
    plt.plot(plot_rates, plot_pdr, marker='s', color='red')
    plt.title('Queda de Taxa de Entrega por Saturação do Meio')
    plt.xlabel('Taxa de Tráfego Cruzado (Pacotes/s)')
    plt.ylabel('Taxa de Entrega (%)')
    plt.grid(True)
    plt.savefig(os.path.join(RESULTS_DIR, 'grafico_b3_pdr.png'))
    plt.close()
    
    plt.figure(figsize=(10, 6))
    plt.plot(plot_rates, plot_dly, marker='^', color='orange')
    plt.title('Aumento do Atraso devido a Filas e Retransmissões')
    plt.xlabel('Taxa de Tráfego Cruzado (Pacotes/s)')
    plt.ylabel('Atraso Médio (s)')
    plt.grid(True)
    plt.savefig(os.path.join(RESULTS_DIR, 'grafico_b3_atraso.png'))
    plt.close()

if __name__ == "__main__": run()