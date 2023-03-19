from panda import Panda
import cereal.messaging as messaging
from common.realtime import Ratekeeper
from enum import IntEnum
import codecs
codecs.register_error("strict", codecs.backslashreplace_errors)

ACC_GRA = [1386]
GRA_Neu = [906]

def can_list_to_can_capnp(can_msgs, msgtype='can'):
  dat = messaging.new_message(msgtype, len(can_msgs))
  for i, can_msg in enumerate(can_msgs):
    if msgtype == 'sendcan':
      cc = dat.sendcan[i]
    else:
      cc = dat.can[i]
    cc.address = can_msg[0]
    cc.busTime = can_msg[1]
    cc.dat = bytes(can_msg[2])
    cc.src = can_msg[3]
  return dat

p = Panda()
p.set_safety_mode(Panda.SAFETY_ALLOUTPUT) # Activating output

logcan = messaging.pub_sock('can')
sendcan = messaging.sub_sock('sendcan')

def can_capnp_to_can_list(can, src_filter=None):
  ret = []
  for msg in can:
    if src_filter is None or msg.src in src_filter:
      if msg.address in ACC_GRA:
        ret.append((msg.address, msg.busTime, msg.dat, 2))
      if msg.address in GRA_Neu:
        ret.append((msg.address, msg.busTime, msg.dat, 1))
      else:
        ret.append((msg.address, msg.busTime, msg.dat, 0))
  return ret

print("boardd started ..")
rk = Ratekeeper(100)
while True:
    # tx
    can_msgs = p.can_recv()
    dat = can_list_to_can_capnp(can_msgs)
    logcan.send(dat.to_bytes())
    print("TX: "+dat)
    
    # rx
    send_can_msgs = messaging.recv_sock(sendcan)
    if send_can_msgs is not None:
        msg_list = can_capnp_to_can_list(send_can_msgs.sendcan)
        p.can_send_many(msg_list)
        print("RX: "+msg_list)
    
    rk.keep_time()
