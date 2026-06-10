#include "ns3/core-module.h"
#include "ns3/network-module.h"
#include "ns3/internet-module.h"
#include "ns3/wifi-module.h"
#include "ns3/mobility-module.h"
#include "ns3/applications-module.h"
#include "ns3/olsr-helper.h"
#include "ns3/flow-monitor-module.h"
#include "ns3/udp-socket-factory.h"
#include "ns3/socket.h"
#include "ns3/inet-socket-address.h"
#include <map>

using namespace ns3;

NS_LOG_COMPONENT_DEFINE ("DualRadioTopology");

static Ptr<Packet>  ncBufferedPacket = nullptr;
static Ptr<Socket>  ncTxSocket       = nullptr;
static Ipv4Address  ncDestAddr;
static uint16_t     ncDestPort       = 7777;
static bool         enableNC_global  = true;

static Ptr<Packet> XorPackets (Ptr<const Packet> a, Ptr<const Packet> b)
{
    uint32_t sizeA = a->GetSize ();
    uint32_t sizeB = b->GetSize ();
    uint32_t sz    = std::min (sizeA, sizeB);

    uint8_t *bufA = new uint8_t[sizeA];
    uint8_t *bufB = new uint8_t[sizeB];
    a->CopyData (bufA, sizeA);
    b->CopyData (bufB, sizeB);

    uint8_t *xored = new uint8_t[sz];
    for (uint32_t i = 0; i < sz; ++i)
        xored[i] = bufA[i] ^ bufB[i];

    Ptr<Packet> result = Create<Packet> (xored, sz);
    delete[] bufA;
    delete[] bufB;
    delete[] xored;
    return result;
}

void InterceptAndEncode (Ptr<const Packet> packet)
{
    if (!enableNC_global)
    {
        std::cout << "[PASSTHROUGH] No 3 repassando pacote UID: " << packet->GetUid () << std::endl;
        return;
    }

    if (ncBufferedPacket == nullptr)
    {
        ncBufferedPacket = packet->Copy ();
        std::cout << "[BUFFER] No 3 armazenou pacote UID: " << packet->GetUid () << std::endl;
    }
    else
    {
        Ptr<Packet> combined = XorPackets (ncBufferedPacket, packet);
        std::cout << "[ENCODE] No 3 XOR UID " << ncBufferedPacket->GetUid ()
                  << " + UID " << packet->GetUid ()
                  << " → pacote combinado de " << combined->GetSize () << " bytes" << std::endl;

        if (ncTxSocket != nullptr)
        {
            ncTxSocket->SendTo (combined, 0, InetSocketAddress (ncDestAddr, ncDestPort));
        }

        ncBufferedPacket = nullptr;
    }
}

void InterceptAndDecode (Ptr<const Packet> packet)
{
    std::cout << "[DECODE] No 5 decodificando pacote UID: " << packet->GetUid () << std::endl;
}

int main (int argc, char *argv[])
{
    uint32_t packetSize   = 1024;
    double   interval     = 0.1;
    uint32_t maxPackets   = 500;
    double   distance     = 15.0;
    double   simTime      = 50.0;
    double   crossInterval = 0.1;
    bool     enableCross  = true;
    bool     enableNC     = true;

    CommandLine cmd;
    cmd.AddValue ("packetSize",    "", packetSize);
    cmd.AddValue ("interval",      "", interval);
    cmd.AddValue ("maxPackets",    "", maxPackets);
    cmd.AddValue ("distance",      "", distance);
    cmd.AddValue ("simTime",       "", simTime);
    cmd.AddValue ("crossInterval", "", crossInterval);
    cmd.AddValue ("enableCross",   "", enableCross);
    cmd.AddValue ("enableNC",      "", enableNC);
    cmd.Parse (argc, argv);

    enableNC_global = enableNC;

    NodeContainer nodes;
    nodes.Create (6);

    WifiHelper wifi;
    wifi.SetStandard (WIFI_STANDARD_80211a);

    YansWifiPhyHelper wifiPhyRadio1;
    YansWifiChannelHelper wifiChannelRadio1 = YansWifiChannelHelper::Default ();
    wifiPhyRadio1.SetChannel (wifiChannelRadio1.Create ());
    wifiPhyRadio1.Set ("TxPowerStart", DoubleValue (3.0));
    wifiPhyRadio1.Set ("TxPowerEnd",   DoubleValue (3.0));

    YansWifiPhyHelper wifiPhyRadio2;
    YansWifiChannelHelper wifiChannelRadio2 = YansWifiChannelHelper::Default ();
    wifiPhyRadio2.SetChannel (wifiChannelRadio2.Create ());
    wifiPhyRadio2.Set ("TxPowerStart", DoubleValue (3.0));
    wifiPhyRadio2.Set ("TxPowerEnd",   DoubleValue (3.0));

    WifiMacHelper wifiMac;
    wifiMac.SetType ("ns3::AdhocWifiMac");

    NetDeviceContainer devicesRadio1 = wifi.Install (wifiPhyRadio1, wifiMac, nodes);
    NetDeviceContainer devicesRadio2 = wifi.Install (wifiPhyRadio2, wifiMac, nodes);

    MobilityHelper mobility;
    mobility.SetPositionAllocator ("ns3::GridPositionAllocator",
                                   "MinX",      DoubleValue (0.0),
                                   "MinY",      DoubleValue (0.0),
                                   "DeltaX",    DoubleValue (distance),
                                   "DeltaY",    DoubleValue (distance),
                                   "GridWidth", UintegerValue (3),
                                   "LayoutType", StringValue ("RowFirst"));
    mobility.SetMobilityModel ("ns3::ConstantPositionMobilityModel");
    mobility.Install (nodes);

    InternetStackHelper internet;
    OlsrHelper olsr;
    internet.SetRoutingHelper (olsr);
    internet.Install (nodes);

    Ipv4AddressHelper ipv4;
    ipv4.SetBase ("10.1.1.0", "255.255.255.0");
    Ipv4InterfaceContainer interfacesRadio1 = ipv4.Assign (devicesRadio1);

    ipv4.SetBase ("10.1.2.0", "255.255.255.0");
    Ipv4InterfaceContainer interfacesRadio2 = ipv4.Assign (devicesRadio2);

    ncDestAddr = interfacesRadio1.GetAddress (5);
    ncDestPort = 7777;

    if (enableNC)
    {
        Ptr<Socket> sock = Socket::CreateSocket (nodes.Get (3),
                                                 UdpSocketFactory::GetTypeId ());
        sock->Bind ();
        ncTxSocket = sock;

        UdpEchoServerHelper ncServer (ncDestPort);
        ApplicationContainer ncServerApp = ncServer.Install (nodes.Get (5));
        ncServerApp.Start (Seconds (1.0));
        ncServerApp.Stop  (Seconds (simTime));
    }

    uint16_t port = 9;
    UdpEchoServerHelper server (port);
    ApplicationContainer serverApps = server.Install (nodes.Get (5));

    if (enableCross)
    {
        UdpEchoServerHelper crossServer (port + 1);
        serverApps.Add (crossServer.Install (nodes.Get (4)));
    }

    serverApps.Start (Seconds (1.0));
    serverApps.Stop  (Seconds (simTime));

    UdpEchoClientHelper client (interfacesRadio1.GetAddress (5), port);
    client.SetAttribute ("MaxPackets", UintegerValue (maxPackets));
    client.SetAttribute ("Interval",   TimeValue (Seconds (interval)));
    client.SetAttribute ("PacketSize", UintegerValue (packetSize));

    ApplicationContainer clientApps = client.Install (nodes.Get (0));
    clientApps.Start (Seconds (20.0));

    if (enableCross && crossInterval > 0)
    {
        UdpEchoClientHelper crossClient (interfacesRadio1.GetAddress (4), port + 1);
        crossClient.SetAttribute ("MaxPackets", UintegerValue (maxPackets));
        crossClient.SetAttribute ("Interval",   TimeValue (Seconds (crossInterval)));
        crossClient.SetAttribute ("PacketSize", UintegerValue (packetSize));
        clientApps.Add (crossClient.Install (nodes.Get (1)));
    }

    clientApps.Stop (Seconds (simTime));

    Config::ConnectWithoutContext (
        "/NodeList/3/DeviceList/*/$ns3::WifiNetDevice/Mac/MacRx",
        MakeCallback (&InterceptAndEncode));
    Config::ConnectWithoutContext (
        "/NodeList/5/DeviceList/*/$ns3::WifiNetDevice/Mac/MacRx",
        MakeCallback (&InterceptAndDecode));

    FlowMonitorHelper flowmon;
    Ptr<FlowMonitor> monitor = flowmon.InstallAll ();

    Simulator::Stop (Seconds (simTime));
    Simulator::Run ();

    monitor->SerializeToXmlFile ("flowmon-results.xml", true, true);

    Simulator::Destroy ();
    return 0;
}
