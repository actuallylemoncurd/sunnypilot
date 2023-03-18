from tools.lib.logreader import MultiLogIterator
import os
import codecs
import cereal.messaging as messaging
from common.realtime import Ratekeeper
codecs.register_error("strict", codecs.backslashreplace_errors)

# can 0 is our feed data onto CAR PT can
# can 1 is our gateway receive can
# can 2 is our extended receive can

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

def can_capnp_to_can_list(can, src_filter=1):
  ret = []
  for msg in can:
    if src_filter is None or msg.src in src_filter:
      if msg.address in ACC_GRA:
        ret.append((msg.address, msg.busTime, msg.dat, 2))
      if msg.address in GRA_Neu:
        ret.append((msg.address, msg.busTime, msg.dat, 1))
      else:
        ret.append((msg.address, msg.busTime, msg.dat, 0))
      #ret.append((msg.address, msg.busTime, msg.dat, msg.src))
  return ret

logs = sorted(os.listdir("new-logs"))[2:]
lr = MultiLogIterator([f"new-logs/{log}" for log in logs], sort_by_time=True)

sendcan = messaging.pub_sock('sendcan')

CAN_MSGS = []
CAN_MSGS += [msg for msg in lr if msg.which() == 'can' or msg.which() == 'sendcan']

print("replay in process ..")
rk = Ratekeeper(100)
for msg in CAN_MSGS:
    # convert can messages to sendcan
    if msg.which() == 'can':
        msg = can_list_to_can_capnp(can_capnp_to_can_list(msg.can), msgtype='sendcan')
    else:
        msg = msg.as_builder()
    sendcan.send(msg.to_bytes())
    rk.keep_time()

print("replay done.")
