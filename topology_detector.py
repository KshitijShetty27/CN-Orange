"""
SDN Topology Change Detector
=============================
Project: SDN Mininet-based Simulation – Orange Problem (Task 21)
Author : [Your Name]
Course : Computer Networks

Description:
    Implements a real-time Topology Change Detector using the POX SDN controller
    and Mininet. The controller listens for OpenFlow switch/link events and
    dynamically maintains an up-to-date topology map, logging every change.

Controller: POX (openflow.discovery module)
Topology  : Linear, 3 switches (s1–s2–s3), 3 hosts (h1–h3)
"""

from pox.core import core
import pox.openflow.discovery
from pox.lib.revent import EventMixin
import logging

log = core.getLogger()

# ─── Suppress noisy packet / DNS warnings ────────────────────────────────────
logging.getLogger("packet").setLevel(logging.CRITICAL)
logging.getLogger("pox.lib.packet").setLevel(logging.CRITICAL)

# ─── Global topology store ───────────────────────────────────────────────────
# Each entry is a sorted tuple (dpid_a, dpid_b) so that the same link is never
# stored twice (e.g. both "1→2" and "2→1" collapse to (1, 2)).
topology = []


class TopologyDetector(EventMixin):
    """
    POX component that monitors OpenFlow switch-connection and link events.

    Events handled
    --------------
    _handle_ConnectionUp : fired when a switch connects to the controller.
    _handle_LinkEvent    : fired by openflow.discovery when a link is added
                           or removed between two switches.
    """

    def __init__(self):
        # Register for both OpenFlow and discovery events
        core.openflow.addListeners(self)
        core.openflow_discovery.addListeners(self)
        log.info("Topology Detector Started (Final Version)")

    # ── Switch connection ─────────────────────────────────────────────────────
    def _handle_ConnectionUp(self, event):
        """
        Called each time a switch establishes a connection with the controller.
        Logs the datapath ID (dpid) of the newly connected switch.
        """
        log.info("Switch Connected: %s", event.dpid)

    # ── Link add / remove ─────────────────────────────────────────────────────
    def _handle_LinkEvent(self, event):
        """
        Called by openflow.discovery whenever a link between two switches is
        detected (added) or disappears (removed / timed-out).

        The link is normalised as a sorted tuple so that the same physical link
        is not stored twice regardless of which direction was discovered first.
        """
        global topology

        # Normalise: always store the smaller dpid first
        link = tuple(sorted([event.link.dpid1, event.link.dpid2]))

        if event.added:
            if link not in topology:
                topology.append(link)
                log.info("Link Added: %s -> %s", link[0], link[1])
                log.info("Current Topology: %s", topology)

        elif event.removed:
            if link in topology:
                topology.remove(link)
                log.info("Link Removed: %s -> %s", link[0], link[1])
                log.info("Current Topology: %s", topology)


def launch():
    """
    POX entry-point.  Called automatically when the module is loaded via:
        python3 pox.py openflow.discovery topology_detector
    """
    TopologyDetector()
