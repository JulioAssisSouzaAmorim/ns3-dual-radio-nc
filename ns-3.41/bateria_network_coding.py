import os
import subprocess
import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt

NS3_EXECUTABLE = "./ns3"
SCRIPT_NAME    = "dual_radio_topology"
RESULTS_DIR    = "resultados_simulacao"

AGGRESSOR_RATES_PPS = [0, 10, 20, 40, 80, 160]

FIXED_SIZE     = 1024
FIXED_INTERVAL = 0.05
MAX_PACKETS    = 500
DISTANCE       = 15.0
SIM_TIME       = 50.0


def pps_to_interval(pps):
    return 1.0 / pps if pps > 0 else 0.0


def parse_flowmon_flow(xml_file, flow_id):
    if not os.path.exists(xml_file): return 0.0, 0.0, 0.0
    tree = ET.parse(xml_file)
    root = tree.getroot()
    flow = root.find(f'.//FlowStats/Flow[@flowId="{flow_id}"]')
    if flow is None: return 0.0, 0.0, 0.0
    tx  = int(flow.get('txPackets', 0))
    rx  = int(flow.get('rxPackets', 0))
    rxb = int(flow.get('rxBytes',   0))
    delay_str = str(flow.get('delaySum', '0ns'))
    delay_val = 0.0
    if 'ns' in delay_str:
        try: delay_val = float(delay_str.replace('+', '').replace('ns', '')) / 1e9
        except ValueError: pass
    pdr        = (rx / tx * 100) if tx > 0 else 0.0
    throughput = (rxb * 8) / 1000 / SIM_TIME
    avg_delay  = (delay_val / rx) if rx > 0 else 0.0
    return throughput, pdr, avg_delay


def run_scenario(cross_interval, enable_cross):
    cross_flag = "true" if enable_cross else "false"
    args = (
        f"scratch/{SCRIPT_NAME}"
        f" --packetSize={FIXED_SIZE}"
        f" --interval={FIXED_INTERVAL}"
        f" --maxPackets={MAX_PACKETS}"
        f" --distance={DISTANCE}"
        f" --simTime={SIM_TIME}"
        f" --enableCross={cross_flag}"
        f" --crossInterval={cross_interval}"
    )
    subprocess.run(
        [NS3_EXECUTABLE, "run", args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    thr1, pdr1, dly1 = parse_flowmon_flow("flowmon-results.xml", 1)
    thr2, pdr2, dly2 = parse_flowmon_flow("flowmon-results.xml", 2)
    return thr1, pdr1, dly1, thr2, pdr2, dly2


def run():
    if not os.path.exists(RESULTS_DIR): os.makedirs(RESULTS_DIR)

    rates      = []
    thr_base   = []
    thr_princ  = []
    thr_cruz   = []
    pdr_base   = []
    pdr_princ  = []
    pdr_cruz   = []
    dly_base   = []
    dly_princ  = []
    dly_cruz   = []

    total = len(AGGRESSOR_RATES_PPS)

    for i, pps in enumerate(AGGRESSOR_RATES_PPS):
        enable         = pps > 0
        cross_interval = pps_to_interval(pps) if enable else 0.1

        print(f"[{i+1}/{total}] Agressão={pps} pps  |  enableCross={enable}")

        if not enable:
            thr1, pdr1, dly1, _, _, _ = run_scenario(cross_interval, enable_cross=False)
            thr_base.append(thr1)
            pdr_base.append(pdr1)
            dly_base.append(dly1)
            thr_princ.append(thr1)
            pdr_princ.append(pdr1)
            dly_princ.append(dly1)
            thr_cruz.append(0.0)
            pdr_cruz.append(0.0)
            dly_cruz.append(0.0)
            print(f"         Base (sem agressor) → {thr1:.2f} Kbps / {pdr1:.1f}% / {dly1:.4f}s")
        else:
            thr1, pdr1, dly1, thr2, pdr2, dly2 = run_scenario(cross_interval, enable_cross=True)
            thr_base.append(thr_base[0])
            pdr_base.append(pdr_base[0])
            dly_base.append(dly_base[0])
            thr_princ.append(thr1)
            pdr_princ.append(pdr1)
            dly_princ.append(dly1)
            thr_cruz.append(thr2)
            pdr_cruz.append(pdr2)
            dly_cruz.append(dly2)
            print(f"         Fluxo principal → {thr1:.2f} Kbps / {pdr1:.1f}% / {dly1:.4f}s")
            print(f"         Fluxo cruzado   → {thr2:.2f} Kbps / {pdr2:.1f}% / {dly2:.4f}s")

        rates.append(pps)

    table_data = []
    for j, pps in enumerate(rates):
        degradacao = thr_princ[j] - thr_base[j]
        deg_pct    = (degradacao / thr_base[j] * 100) if thr_base[j] > 0 else 0.0
        table_data.append([
            str(pps),
            f"{thr_base[j]:.2f}",
            f"{thr_princ[j]:.2f}",
            f"{thr_cruz[j]:.2f}",
            f"{degradacao:+.2f}",
            f"{deg_pct:+.1f}%",
        ])

    fig, ax = plt.subplots(figsize=(13, 4))
    ax.axis('tight')
    ax.axis('off')
    headers = ['Agressão (pps)', 'Base sem agressor (Kbps)', 'Fluxo Principal (Kbps)', 'Fluxo Cruzado (Kbps)', 'Degradação (Kbps)', 'Degradação (%)']
    t = ax.table(cellText=table_data, colLabels=headers, loc='center', cellLoc='center')
    t.scale(1, 1.6)
    plt.title('Resultados Bateria 4: Fluxo Principal vs Fluxo Cruzado sob Network Coding')
    plt.savefig(os.path.join(RESULTS_DIR, 'tabela_b4_nc.png'), bbox_inches='tight')
    plt.close()

    plt.figure(figsize=(10, 6))
    plt.axhline(y=thr_base[0], color='green', linestyle='--', linewidth=1.5, label=f'Linha de base (sem agressor): {thr_base[0]:.2f} Kbps')
    plt.plot(rates, thr_princ, marker='s', color='blue', label='Fluxo Principal (com agressor)')
    plt.plot(rates[1:], thr_cruz[1:], marker='^', color='red', label='Fluxo Cruzado (agressor)')
    plt.fill_between(rates, thr_base, thr_princ, alpha=0.10, color='red', label='Degradação do fluxo principal')
    plt.title('Bateria 4: Vazão dos Dois Fluxos sob Network Coding')
    plt.xlabel('Taxa de Tráfego Cruzado (Pacotes/s)')
    plt.ylabel('Vazão (Kbps)')
    plt.legend()
    plt.grid(True)
    plt.savefig(os.path.join(RESULTS_DIR, 'grafico_b4_vazao.png'))
    plt.close()

    plt.figure(figsize=(10, 6))
    plt.plot(rates, pdr_princ, marker='s', color='blue', label='Fluxo Principal')
    plt.plot(rates[1:], pdr_cruz[1:], marker='^', color='red', label='Fluxo Cruzado')
    plt.title('Bateria 4: Taxa de Entrega dos Dois Fluxos sob Network Coding')
    plt.xlabel('Taxa de Tráfego Cruzado (Pacotes/s)')
    plt.ylabel('Taxa de Entrega (%)')
    plt.ylim(0, 110)
    plt.legend()
    plt.grid(True)
    plt.savefig(os.path.join(RESULTS_DIR, 'grafico_b4_pdr.png'))
    plt.close()

    plt.figure(figsize=(10, 6))
    plt.plot(rates, dly_princ, marker='s', color='blue', label='Fluxo Principal')
    plt.plot(rates[1:], dly_cruz[1:], marker='^', color='red', label='Fluxo Cruzado')
    plt.title('Bateria 4: Atraso Médio dos Dois Fluxos sob Network Coding')
    plt.xlabel('Taxa de Tráfego Cruzado (Pacotes/s)')
    plt.ylabel('Atraso Médio (s)')
    plt.legend()
    plt.grid(True)
    plt.savefig(os.path.join(RESULTS_DIR, 'grafico_b4_atraso.png'))
    plt.close()

    print("\nGráficos salvos em", RESULTS_DIR)
    print("\nResumo final:")
    for j, pps in enumerate(rates):
        deg_pct = ((thr_princ[j] - thr_base[j]) / thr_base[j] * 100) if thr_base[j] > 0 else 0.0
        print(f"  {pps:>4} pps → fluxo principal: {thr_princ[j]:.2f} Kbps  |  fluxo cruzado: {thr_cruz[j]:.2f} Kbps  |  degradação: {deg_pct:+.1f}%")


if __name__ == "__main__": run()