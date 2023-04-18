#####################################################################
# testHsmsEquipmentHandler.py
#
# (c) Copyright 2013-2016, Benjamin Parzella. All rights reserved.
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#####################################################################

import threading
import unittest

import secsgem.hsms

from test_connection import HsmsTestServer


class TestHsmsProtocolHandlerPassive(unittest.TestCase):
    def setUp(self):
        self.server = HsmsTestServer()

        self.client = secsgem.hsms.HsmsProtocol("127.0.0.1", 5000, False, 0, "test", self.server)

        self.server.start()
        self.client.enable()

    def tearDown(self):
        self.server.stop()
        self.client.disable()

    def testSystemCounterWrapping(self):
        self.client._system_counter = ((2 ** 32) - 1)

        self.assertEqual(self.client.get_next_system_counter(), 0)

    def testLinktestTimer(self):
        self.client.disable()
        
        self.client._linktest_timeout = 0.1
        self.client.enable()

        self.server.simulate_connect()

        packet = self.server.expect_packet(s_type=0x05)

        self.assertIsNot(packet, None)
        self.assertEqual(packet.header.s_type, 0x05)
        self.assertEqual(packet.header.session_id, 0xffff)

        self.server.simulate_packet(secsgem.hsms.HsmsPacket(secsgem.hsms.HsmsLinktestRspHeader(packet.header.system)))

        packet = self.server.expect_packet(s_type=0x05)

        self.assertIsNot(packet, None)
        self.assertEqual(packet.header.s_type, 0x05)
        self.assertEqual(packet.header.session_id, 0xffff)

    def testSelect(self):
        self.server.simulate_connect()

        system_id = self.server.get_next_system_counter()
        self.server.simulate_packet(secsgem.hsms.HsmsPacket(secsgem.hsms.HsmsSelectReqHeader(system_id)))

        packet = self.server.expect_packet(system_id=system_id)

        self.assertIsNot(packet, None)
        self.assertEqual(packet.header.s_type, 0x02)
        self.assertEqual(packet.header.session_id, 0xffff)


    def testSelectWhileDisconnecting(self):
        self.server.simulate_connect()

        # set the connection to disconnecting by brute force
        self.client._connection.disconnecting = True

        system_id = self.server.get_next_system_counter()
        self.server.simulate_packet(secsgem.hsms.HsmsPacket(secsgem.hsms.HsmsSelectReqHeader(system_id)))

        packet = self.server.expect_packet(system_id=system_id)

        self.assertIsNot(packet, None)
        self.assertEqual(packet.header.s_type, 0x07)
        self.assertEqual(packet.header.session_id, 0xffff)

    def testDeselect(self):
        self.server.simulate_connect()

        system_id = self.server.get_next_system_counter()
        self.server.simulate_packet(secsgem.hsms.HsmsPacket(secsgem.hsms.HsmsSelectReqHeader(system_id)))

        packet = self.server.expect_packet(system_id=system_id)

        self.assertIsNot(packet, None)
        self.assertEqual(packet.header.s_type, 0x02)
        self.assertEqual(packet.header.session_id, 0xffff)

        system_id = self.server.get_next_system_counter()
        self.server.simulate_packet(secsgem.hsms.HsmsPacket(secsgem.hsms.HsmsDeselectReqHeader(system_id)))

        packet = self.server.expect_packet(system_id=system_id)

        self.assertIsNot(packet, None)
        self.assertEqual(packet.header.s_type, 0x04)
        self.assertEqual(packet.header.session_id, 0xffff)

    def testDeselectWhileDisconnecting(self):
        self.server.simulate_connect()

        system_id = self.server.get_next_system_counter()
        self.server.simulate_packet(secsgem.hsms.HsmsPacket(secsgem.hsms.HsmsSelectReqHeader(system_id)))

        packet = self.server.expect_packet(system_id=system_id)

        self.assertIsNot(packet, None)
        self.assertEqual(packet.header.s_type, 0x02)
        self.assertEqual(packet.header.session_id, 0xffff)

        # set the connection to disconnecting by brute force
        self.client._connection.disconnecting = True

        system_id = self.server.get_next_system_counter()
        self.server.simulate_packet(secsgem.hsms.HsmsPacket(secsgem.hsms.HsmsDeselectReqHeader(system_id)))

        packet = self.server.expect_packet(system_id=system_id)

        self.assertIsNot(packet, None)
        self.assertEqual(packet.header.s_type, 0x07)
        self.assertEqual(packet.header.session_id, 0xffff)

    def testLinktest(self):
        self.server.simulate_connect()

        # set the connection to disconnecting by brute force
        self.client._connection.disconnecting = True

        system_id = self.server.get_next_system_counter()
        self.server.simulate_packet(secsgem.hsms.HsmsPacket(secsgem.hsms.HsmsLinktestReqHeader(system_id)))

        packet = self.server.expect_packet(system_id=system_id)

        self.assertIsNot(packet, None)
        self.assertEqual(packet.header.s_type, 0x07)
        self.assertEqual(packet.header.session_id, 0xffff)

    def testLinktestWhileDisconnecting(self):
        self.server.simulate_connect()

        system_id = self.server.get_next_system_counter()
        self.server.simulate_packet(secsgem.hsms.HsmsPacket(secsgem.hsms.HsmsLinktestReqHeader(system_id)))

        packet = self.server.expect_packet(system_id=system_id)

        self.assertIsNot(packet, None)
        self.assertEqual(packet.header.s_type, 0x06)
        self.assertEqual(packet.header.session_id, 0xffff)

    def testRepr(self):
        self.server.simulate_connect()

        print(self.client)


class TestHsmsProtocolActive(unittest.TestCase):
    def setUp(self):
        self.server = HsmsTestServer()

        self.client = secsgem.hsms.HsmsProtocol("127.0.0.1", 5000, True, 0, "test", self.server)

        self.server.start()
        self.client.enable()

    def tearDown(self):
        self.server.stop()
        self.client.disable()

    def testSelect(self):
        self.server.simulate_connect()

        packet = self.server.expect_packet(s_type=0x01)

        self.assertIsNot(packet, None)
        self.assertEqual(packet.header.s_type, 0x01)
        self.assertEqual(packet.header.session_id, 0xffff)

        self.server.simulate_packet(secsgem.hsms.HsmsPacket(secsgem.hsms.HsmsSelectRspHeader(packet.header.system)))

    def testSelectSendError(self):
        self.server.fail_next_send()

        self.server.simulate_connect()

    def testDeselect(self):
        self.server.simulate_connect()

        packet = self.server.expect_packet(s_type=0x01)

        self.assertIsNot(packet, None)
        self.assertEqual(packet.header.s_type, 0x01)
        self.assertEqual(packet.header.session_id, 0xffff)

        self.server.simulate_packet(secsgem.hsms.HsmsPacket(secsgem.hsms.HsmsSelectRspHeader(packet.header.system)))

        clientCommandThread = threading.Thread(target=self.client.send_deselect_req, name="TestHsmsProtocolActive_testDeselect")
        clientCommandThread.daemon = True  # make thread killable on program termination
        clientCommandThread.start()

        packet = self.server.expect_packet(s_type=0x03)

        self.assertIsNot(packet, None)
        self.assertEqual(packet.header.s_type, 0x03)
        self.assertEqual(packet.header.session_id, 0xffff)

        self.server.simulate_packet(secsgem.hsms.HsmsPacket(secsgem.hsms.HsmsDeselectRspHeader(packet.header.system)))

        clientCommandThread.join(1)
        self.assertFalse(clientCommandThread.is_alive())

    def testDeselectWhileDisconnecting(self):
        self.server.simulate_connect()

        system_id = self.server.get_next_system_counter()
        self.server.simulate_packet(secsgem.hsms.HsmsPacket(secsgem.hsms.HsmsSelectReqHeader(system_id)))

        packet = self.server.expect_packet(system_id=system_id)

        self.assertIsNot(packet, None)
        self.assertEqual(packet.header.s_type, 0x02)
        self.assertEqual(packet.header.session_id, 0xffff)

        # set the connection to disconnecting by brute force
        self.client._connection.disconnecting = True

        system_id = self.server.get_next_system_counter()
        self.server.simulate_packet(secsgem.hsms.HsmsPacket(secsgem.hsms.HsmsDeselectReqHeader(system_id)))

        packet = self.server.expect_packet(system_id=system_id)

        self.assertIsNot(packet, None)
        self.assertEqual(packet.header.s_type, 0x07)
        self.assertEqual(packet.header.session_id, 0xffff)

    def testLinktest(self):
        self.server.simulate_connect()

        # set the connection to disconnecting by brute force
        self.client._connection.disconnecting = True

        system_id = self.server.get_next_system_counter()
        self.server.simulate_packet(secsgem.hsms.HsmsPacket(secsgem.hsms.HsmsLinktestReqHeader(system_id)))

        packet = self.server.expect_packet(system_id=system_id)

        self.assertIsNot(packet, None)
        self.assertEqual(packet.header.s_type, 0x07)
        self.assertEqual(packet.header.session_id, 0xffff)


    def testLinktestWhileDisconnecting(self):
        self.server.simulate_connect()

        system_id = self.server.get_next_system_counter()
        self.server.simulate_packet(secsgem.hsms.HsmsPacket(secsgem.hsms.HsmsLinktestReqHeader(system_id)))

        packet = self.server.expect_packet(system_id=system_id)

        self.assertIsNot(packet, None)
        self.assertEqual(packet.header.s_type, 0x06)
        self.assertEqual(packet.header.session_id, 0xffff)

    def testRepr(self):
        self.server.simulate_connect()

        print(self.client)

    def testSecsPacketWithoutSecsDecode(self):
        self.server.simulate_connect()

        packet = self.server.expect_packet(s_type=0x01)

        self.assertIsNot(packet, None)
        self.assertEqual(packet.header.s_type, 0x01)
        self.assertEqual(packet.header.session_id, 0xffff)

        self.server.simulate_packet(secsgem.hsms.HsmsPacket(secsgem.hsms.HsmsSelectRspHeader(packet.header.system)))

        system_id = self.server.get_next_system_counter()
        self.server.simulate_packet(self.server.generate_stream_function_packet(system_id, secsgem.secs.functions.SecsS01F01()))

        print(self.client)

    def testPacketSendingFailed(self):
        self.server.simulate_connect()

        self.server.fail_next_send()

        self.assertEqual(self.client.send_and_waitfor_response(secsgem.secs.functions.SecsS01F01()), None)

    def testSelectReqSendingFailed(self):
        self.server.simulate_connect()

        self.server.fail_next_send()

        self.assertEqual(self.client.send_select_req(), None)

    def testLinktestReqSendingFailed(self):
        self.server.simulate_connect()

        self.server.fail_next_send()

        self.assertEqual(self.client.send_linktest_req(), None)

    def testDeselectReqSendingFailed(self):
        self.server.simulate_connect()

        self.server.fail_next_send()

        self.assertEqual(self.client.send_deselect_req(), None)

    def testPacketSendingTimeout(self):
        self.server.simulate_connect()

        self.client.timeouts.t3 = 0.1

        self.assertEqual(self.client.send_and_waitfor_response(secsgem.secs.functions.SecsS01F01()), None)

    def testSelectReqSendingTimeout(self):
        self.server.simulate_connect()

        self.client.timeouts.t6 = 0.1

        self.assertEqual(self.client.send_select_req(), None)

    def testLinktestReqSendingTimeout(self):
        self.server.simulate_connect()

        self.client.timeouts.t6 = 0.1

        self.assertEqual(self.client.send_linktest_req(), None)

    def testDeelectReqSendingTimeout(self):
        self.server.simulate_connect()

        self.client.timeouts.t6 = 0.1

        self.assertEqual(self.client.send_deselect_req(), None)

