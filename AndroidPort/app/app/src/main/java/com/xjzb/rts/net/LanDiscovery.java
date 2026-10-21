package com.xjzb.rts.net;

import com.xjzb.rts.core.LanBeacon;

import java.net.DatagramPacket;
import java.net.DatagramSocket;
import java.net.InetAddress;
import java.net.InetSocketAddress;
import java.net.NetworkInterface;
import java.util.Collections;
import java.util.Enumeration;

/**
 * v2.37: finding a room on the LAN. A thin transport around core/LanBeacon.
 *
 * The beacon itself -- its text, its parsing, its version filter -- is in core/
 * and asserted headlessly (see [v233]); what is here is only the socket work,
 * because a DatagramSocket cannot exist on the desktop harness.
 *
 * Broadcast rather than multicast on purpose: it works on the ad-hoc hotspots
 * and cheap routers a phone-vs-phone match actually happens on, without needing
 * a multicast-capable AP or an IGMP querier. It is chatty but this is a
 * two-phone LAN, not a fleet.
 */
public final class LanDiscovery {

    /** The port a host announces on. A single fixed port keeps joining trivial. */
    public static final int DISCOVERY_PORT = 45918;

    private DatagramSocket socket;
    private Thread listener;
    private volatile boolean running;
    private Listener listener_;
    private String myVersion_ = "";

    /** Broadcast one beacon. Fire and forget: a lost beacon is just a later try. */
    public static void broadcast(LanBeacon beacon) {
        DatagramSocket s = null;
        try {
            s = new DatagramSocket();
            s.setBroadcast(true);
            byte[] data = (beacon.encode() + "\n").getBytes("UTF-8");
            InetAddress[] targets = {
                InetAddress.getByName("255.255.255.255"),
                broadcastAddress(),
            };
            for (InetAddress a : targets) {
                if (a == null) continue;
                try {
                    s.send(new DatagramPacket(data, data.length, a, DISCOVERY_PORT));
                } catch (Exception ignored) {
                    // Some APs refuse one of the two forms; the other still lands.
                }
            }
        } catch (Exception ignored) {
        } finally {
            if (s != null) s.close();
        }
    }

    /**
     * The subnet-directed broadcast for the interface we would actually use, or
     * null. 255.255.255.255 is often dropped by Android's own stack on some
     * devices, so this is the form that tends to work.
     */
    private static InetAddress broadcastAddress() {
        try {
            Enumeration<NetworkInterface> nis = NetworkInterface.getNetworkInterfaces();
            for (NetworkInterface ni : Collections.list(nis)) {
                if (!ni.isUp() || ni.isLoopback()) continue;
                for (java.net.InterfaceAddress ia : ni.getInterfaceAddresses()) {
                    if (ia.getBroadcast() != null) return ia.getBroadcast();
                }
            }
        } catch (Exception ignored) {
        }
        return null;
    }

    /** Callback for each beacon that parses and is from our own build. */
    public interface Listener {
        void onBeacon(LanBeacon beacon);
    }

    /**
     * Listen for beacons. Beacons that do not parse, or come from another build,
     * are dropped by LanBeacon.decode and the version filter -- the same rules
     * the desktop assertion pins, so a colleague's phone on the same wifi is a
     * non-event rather than a crash.
     */
    public void listen(final String myVersion, final Listener cb) {
        stop();
        running = true;
        listener_ = cb;
        myVersion_ = myVersion;
        listener = new Thread(() -> {
            DatagramSocket s = null;
            try {
                s = new DatagramSocket(null);
                s.setReuseAddress(true);
                s.setBroadcast(true);
                s.bind(new InetSocketAddress(DISCOVERY_PORT));
                socket = s;
                byte[] buf = new byte[512];
                while (running) {
                    DatagramPacket p = new DatagramPacket(buf, buf.length);
                    s.receive(p);
                    String line = new String(p.getData(), p.getOffset(), p.getLength(), "UTF-8");
                    LanBeacon b = LanBeacon.decode(line);
                    if (b == null || !b.joinable(myVersion_)) continue;
                    listener_.onBeacon(b);
                }
            } catch (Exception ignored) {
                // A socket that cannot bind (port in use, no wifi) ends the
                // listener; the lobby simply shows no rooms.
            } finally {
                if (s != null) s.close();
                socket = null;
            }
        }, "xjzb-net-discover");
        listener.setDaemon(true);
        listener.start();
    }

    public void stop() {
        running = false;
        DatagramSocket s = socket;
        if (s != null) s.close();
        if (listener != null) listener.interrupt();
        listener = null;
    }
}