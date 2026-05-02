#include "ns3/core-module.h"
#include "ns3/network-module.h"
#include "ns3/internet-module.h"
#include "ns3/wifi-module.h"
#include "ns3/mobility-module.h"
#include "ns3/applications-module.h"
#include "ns3/olsr-helper.h"

using namespace ns3;

NS_LOG_COMPONENT_DEFINE ("DualRadioTopology");

void InterceptPacket (Ptr<const Packet> packet)
{
    std::cout << "[NETWORK CODING] No 3 interceptou pacote. Tamanho: " << packet->GetSize () << " bytes. Pronto para operacao XOR." << std::endl;
}

int main (int argc, char *argv[])
{
    LogComponentEnable ("UdpEchoClientApplication", LOG_LEVEL_INFO);
    LogComponentEnable ("UdpEchoServerApplication", LOG_LEVEL_INFO);

    NodeContainer nodes;
    nodes.Create (6);

    WifiHelper wifi;
    wifi.SetStandard (WIFI_STANDARD_80211a);

    YansWifiPhyHelper wifiPhyRadio1;
    YansWifiChannelHelper wifiChannelRadio1 = YansWifiChannelHelper::Default ();
    wifiPhyRadio1.SetChannel (wifiChannelRadio1.Create ());

    YansWifiPhyHelper wifiPhyRadio2;
    YansWifiChannelHelper wifiChannelRadio2 = YansWifiChannelHelper::Default ();
    wifiPhyRadio2.SetChannel (wifiChannelRadio2.Create ());

    WifiMacHelper wifiMac;
    wifiMac.SetType ("ns3::AdhocWifiMac");

    NetDeviceContainer devicesRadio1 = wifi.Install (wifiPhyRadio1, wifiMac, nodes);
    NetDeviceContainer devicesRadio2 = wifi.Install (wifiPhyRadio2, wifiMac, nodes);

    MobilityHelper mobility;
    mobility.SetPositionAllocator ("ns3::GridPositionAllocator",
                                   "MinX", DoubleValue (0.0),
                                   "MinY", DoubleValue (0.0),
                                   "DeltaX", DoubleValue (50.0),
                                   "DeltaY", DoubleValue (50.0),
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

    uint16_t port = 9;
    UdpEchoServerHelper server (port);
    ApplicationContainer serverApps = server.Install (nodes.Get (5));
    serverApps.Start (Seconds (1.0));
    serverApps.Stop (Seconds (10.0));

    UdpEchoClientHelper client (interfacesRadio1.GetAddress (5), port);
    client.SetAttribute ("MaxPackets", UintegerValue (5));
    client.SetAttribute ("Interval", TimeValue (Seconds (1.0)));
    client.SetAttribute ("PacketSize", UintegerValue (1024));

    ApplicationContainer clientApps = client.Install (nodes.Get (0));
    clientApps.Start (Seconds (2.0));
    clientApps.Stop (Seconds (10.0));

    wifiPhyRadio1.EnablePcap ("dual-radio-node0", devicesRadio1.Get (0));
    wifiPhyRadio1.EnablePcap ("dual-radio-node5", devicesRadio1.Get (5));

    Config::ConnectWithoutContext ("/NodeList/3/DeviceList/*/$ns3::WifiNetDevice/Mac/MacRx", MakeCallback (&InterceptPacket));

    Simulator::Stop (Seconds (10.0));
    Simulator::Run ();
    Simulator::Destroy ();

    return 0;
}