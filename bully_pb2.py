# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# NO CHECKED-IN PROTOBUF GENCODE
# source: bully.proto
# Protobuf Python Version: 5.27.2
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(
    _runtime_version.Domain.PUBLIC,
    5,
    27,
    2,
    '',
    'bully.proto'
)
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x0b\x62ully.proto\x12\x05\x62ully\"6\n\nCacheState\x12\x0c\n\x04\x62oar\x18\x01 \x01(\x05\x12\x0c\n\x04\x66ish\x18\x02 \x01(\x05\x12\x0c\n\x04salt\x18\x03 \x01(\x05\"9\n\x13\x46\x61iledTraderMessage\x12\x11\n\ttrader_id\x18\x01 \x01(\x05\x12\x0f\n\x07message\x18\x02 \x01(\t\"\x1d\n\nAckMessage\x12\x0f\n\x07message\x18\x01 \x01(\t\"\x1e\n\x0bPingMessage\x12\x0f\n\x07message\x18\x01 \x01(\t\"x\n\nWCBMessage\x12\x10\n\x08\x62uyer_id\x18\x01 \x01(\x05\x12\x0f\n\x07product\x18\x02 \x01(\t\x12\x10\n\x08quantity\x18\x03 \x01(\x05\x12\x12\n\nrequest_no\x18\x04 \x01(\x05\x12\x11\n\ttrader_id\x18\x05 \x01(\x05\x12\x0e\n\x06status\x18\x06 \x01(\t\"n\n\nWCSMessage\x12\x11\n\tseller_id\x18\x01 \x01(\x05\x12\x0f\n\x07product\x18\x02 \x01(\t\x12\x10\n\x08quantity\x18\x03 \x01(\x05\x12\x17\n\x0fregistration_no\x18\x04 \x01(\x05\x12\x11\n\ttrader_id\x18\x05 \x01(\x05\"\x1c\n\tREMessage\x12\x0f\n\x07message\x18\x01 \x01(\t\"\x1d\n\nREResponse\x12\x0f\n\x07message\x18\x01 \x01(\t\"#\n\x0c\x43lockMessage\x12\x13\n\x0b\x63lock_value\x18\x01 \x01(\x05\"&\n\x13\x43lockUpdateResponse\x12\x0f\n\x07message\x18\x01 \x01(\t\"k\n\x11\x42uyRequestMessage\x12\x10\n\x08\x62uyer_id\x18\x01 \x01(\x05\x12\x0f\n\x07product\x18\x02 \x01(\t\x12\x10\n\x08quantity\x18\x03 \x01(\x05\x12\r\n\x05\x63lock\x18\x04 \x01(\x05\x12\x12\n\nrequest_no\x18\x05 \x01(\x05\"$\n\x11\x42uyReturnResponse\x12\x0f\n\x07message\x18\x01 \x01(\t\"k\n\x0fPurchaseMessage\x12\x0f\n\x07message\x18\x01 \x01(\t\x12\x10\n\x08\x62uyer_id\x18\x02 \x01(\x05\x12\x0f\n\x07product\x18\x03 \x01(\t\x12\x10\n\x08quantity\x18\x04 \x01(\x05\x12\x12\n\nrequest_no\x18\x05 \x01(\x05\"#\n\x10PurchaseResponse\x12\x0f\n\x07message\x18\x01 \x01(\t\"\x8c\x01\n\x12TransactionMessage\x12\x10\n\x08\x62uyer_id\x18\x01 \x01(\x05\x12\x0f\n\x07product\x18\x02 \x01(\t\x12\x10\n\x08quantity\x18\x03 \x01(\x05\x12\x17\n\x0f\x61mount_credited\x18\x04 \x01(\x02\x12\x14\n\x0cout_of_stock\x18\x05 \x01(\t\x12\x12\n\nrequest_no\x18\x06 \x01(\x05\"&\n\x13TransactionResponse\x12\x0f\n\x07message\x18\x01 \x01(\t\"5\n\x0f\x45lectionRequest\x12\x0f\n\x07node_id\x18\x01 \x01(\x05\x12\x11\n\tsender_id\x18\x02 \x01(\x05\"*\n\x10\x45lectionResponse\x12\x16\n\x0e\x61\x63knowledgment\x18\x01 \x01(\x08\"\'\n\x12LeaderAnnouncement\x12\x11\n\tleader_id\x18\x01 \x01(\x05\"!\n\x0eLeaderResponse\x12\x0f\n\x07message\x18\x01 \x01(\t\"n\n\x0eProductDetails\x12\x11\n\tseller_id\x18\x01 \x01(\x05\x12\x0f\n\x07product\x18\x02 \x01(\t\x12\x10\n\x08quantity\x18\x03 \x01(\x05\x12\x17\n\x0fregistration_no\x18\x04 \x01(\x05\x12\r\n\x05\x63lock\x18\x05 \x01(\x05\"\x8b\x01\n\x10RegisterResponse\x12\x11\n\tseller_id\x18\x01 \x01(\x05\x12\x0f\n\x07product\x18\x02 \x01(\t\x12\x10\n\x08quantity\x18\x03 \x01(\x05\x12\x17\n\x0fregistration_no\x18\x04 \x01(\x05\x12\x17\n\x0f\x61mount_credited\x18\x05 \x01(\x02\x12\x0f\n\x07message\x18\x06 \x01(\t2\xe0\x06\n\rBullyElection\x12\x42\n\x0f\x45lectionMessage\x12\x16.bully.ElectionRequest\x1a\x17.bully.ElectionResponse\x12\x42\n\x0e\x41nnounceLeader\x12\x19.bully.LeaderAnnouncement\x1a\x15.bully.LeaderResponse\x12\x41\n\x0fRegisterProduct\x12\x15.bully.ProductDetails\x1a\x17.bully.RegisterResponse\x12@\n\nBuyRequest\x12\x18.bully.BuyRequestMessage\x1a\x18.bully.BuyReturnResponse\x12>\n\x0b\x43lockUpdate\x12\x13.bully.ClockMessage\x1a\x1a.bully.ClockUpdateResponse\x12\x44\n\x11PurchaseProcessed\x12\x16.bully.PurchaseMessage\x1a\x17.bully.PurchaseResponse\x12\x43\n\x15RegistrationProcessed\x12\x17.bully.RegisterResponse\x1a\x11.bully.AckMessage\x12\x39\n\x12RestartingElection\x12\x10.bully.REMessage\x1a\x11.bully.REResponse\x12H\n\x1bWarehouseCommunicationBuyer\x12\x11.bully.WCBMessage\x1a\x16.bully.PurchaseMessage\x12J\n\x1cWarehouseCommunicationSeller\x12\x11.bully.WCSMessage\x1a\x17.bully.RegisterResponse\x12\x33\n\tHeartBeat\x12\x12.bully.PingMessage\x1a\x12.bully.PingMessage\x12>\n\rTraderFailure\x12\x1a.bully.FailedTraderMessage\x1a\x11.bully.AckMessage\x12\x31\n\tSyncCache\x12\x11.bully.CacheState\x1a\x11.bully.AckMessageb\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'bully_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
  DESCRIPTOR._loaded_options = None
  _globals['_CACHESTATE']._serialized_start=22
  _globals['_CACHESTATE']._serialized_end=76
  _globals['_FAILEDTRADERMESSAGE']._serialized_start=78
  _globals['_FAILEDTRADERMESSAGE']._serialized_end=135
  _globals['_ACKMESSAGE']._serialized_start=137
  _globals['_ACKMESSAGE']._serialized_end=166
  _globals['_PINGMESSAGE']._serialized_start=168
  _globals['_PINGMESSAGE']._serialized_end=198
  _globals['_WCBMESSAGE']._serialized_start=200
  _globals['_WCBMESSAGE']._serialized_end=320
  _globals['_WCSMESSAGE']._serialized_start=322
  _globals['_WCSMESSAGE']._serialized_end=432
  _globals['_REMESSAGE']._serialized_start=434
  _globals['_REMESSAGE']._serialized_end=462
  _globals['_RERESPONSE']._serialized_start=464
  _globals['_RERESPONSE']._serialized_end=493
  _globals['_CLOCKMESSAGE']._serialized_start=495
  _globals['_CLOCKMESSAGE']._serialized_end=530
  _globals['_CLOCKUPDATERESPONSE']._serialized_start=532
  _globals['_CLOCKUPDATERESPONSE']._serialized_end=570
  _globals['_BUYREQUESTMESSAGE']._serialized_start=572
  _globals['_BUYREQUESTMESSAGE']._serialized_end=679
  _globals['_BUYRETURNRESPONSE']._serialized_start=681
  _globals['_BUYRETURNRESPONSE']._serialized_end=717
  _globals['_PURCHASEMESSAGE']._serialized_start=719
  _globals['_PURCHASEMESSAGE']._serialized_end=826
  _globals['_PURCHASERESPONSE']._serialized_start=828
  _globals['_PURCHASERESPONSE']._serialized_end=863
  _globals['_TRANSACTIONMESSAGE']._serialized_start=866
  _globals['_TRANSACTIONMESSAGE']._serialized_end=1006
  _globals['_TRANSACTIONRESPONSE']._serialized_start=1008
  _globals['_TRANSACTIONRESPONSE']._serialized_end=1046
  _globals['_ELECTIONREQUEST']._serialized_start=1048
  _globals['_ELECTIONREQUEST']._serialized_end=1101
  _globals['_ELECTIONRESPONSE']._serialized_start=1103
  _globals['_ELECTIONRESPONSE']._serialized_end=1145
  _globals['_LEADERANNOUNCEMENT']._serialized_start=1147
  _globals['_LEADERANNOUNCEMENT']._serialized_end=1186
  _globals['_LEADERRESPONSE']._serialized_start=1188
  _globals['_LEADERRESPONSE']._serialized_end=1221
  _globals['_PRODUCTDETAILS']._serialized_start=1223
  _globals['_PRODUCTDETAILS']._serialized_end=1333
  _globals['_REGISTERRESPONSE']._serialized_start=1336
  _globals['_REGISTERRESPONSE']._serialized_end=1475
  _globals['_BULLYELECTION']._serialized_start=1478
  _globals['_BULLYELECTION']._serialized_end=2342
# @@protoc_insertion_point(module_scope)
