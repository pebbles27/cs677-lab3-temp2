
import grpc
import threading
import sys
import json
import random
import time
import bully_pb2
import bully_pb2_grpc
from concurrent import futures 
import csv
import heapq
import pickle
import os 
from datetime import datetime 

class LamportClock:
    def __init__(self, node_id):
        self.value = 0
        self.node_id = node_id
        # self.cache_thread = threading.Thread(target=self.constant_function, daemon=True)
        

    def tick(self):
       
            self.value += 1
            # print(f"Node {self.node_id} - Lamport Clock Tick: {self.value}")
            return self.value 

    def update(self, received_value):
        
            self.value = max(self.value, received_value)
            # print(f"Node {self.node_id} - Received Clock: {received_value}, Updated Clock: {self.value}")
            return self.value

class BullyElectionService(bully_pb2_grpc.BullyElectionServicer):
    def __init__(self, node_id, stock_file):
        self.node_id = node_id
        self.db_lock = threading.BoundedSemaphore(1)
        self.role = "Warehouse"
        self.stock_file = stock_file
        self.lamport_clock = LamportClock(node_id)
        self.clock_lock= threading.BoundedSemaphore(1)
        self.active_traders=[]
        self.active_traders_lock= threading.BoundedSemaphore(1)
      
    
    def update_inventory(self, seller_id, product_name, stock, price=1):
        
        if product_name=="boar":
            price=3 
        elif product_name=="fish":
            price=1 
        else:
            price=4
        
        with self.db_lock:
            with open(self.stock_file, "r") as file:
                data = json.load(file)
                if product_name not in data:
                    data[product_name]={"quantity":0, "price":price} 
                
                data[product_name]["quantity"]+= stock
                data[product_name]["price"]=price
            
            with open(self.stock_file, 'w') as json_file:
                json.dump(data, json_file, indent=4) 
        # threading.Thread(target=self.sync_cache, daemon=True).start()
        
        return stock*price
    
    def process_request(self, product, quantity, buyer_id):
        with self.db_lock:
            with open(self.stock_file, "r+") as file:
                data = json.load(file) 
            
            if product in data.keys():
                if data[product]["quantity"]>=quantity:
                    message=True
                    data[product]["quantity"]=data[product]["quantity"]- quantity
                    with open(self.stock_file, "w") as json_file:
                        json.dump(data, json_file, indent=4) 
                
                else:
                    message=False
               
            else:
                 message=False
        # threading.Thread(target=self.sync_cache, daemon=True).start()
        return message
    
    def sync_cache(self):
        try:
            with self.db_lock: 
                with open(self.stock_file, "r") as file:
                    data = json.load(file)
                for node in self.active_traders: 
                    channel = grpc.insecure_channel(f'localhost:{5000 + node}')
                    stub = bully_pb2_grpc.BullyElectionStub(channel)
                    response=stub.SyncCache(bully_pb2.CacheState(boar= data["boar"]["quantity"], fish=data["fish"]["quantity"], salt=data["salt"]["quantity"] ), timeout=3)  
        except:
           pass
    
   
    def WarehouseCommunicationBuyer(self,request, context):
       
        status= self.process_request(request.product, request.quantity, request.buyer_id)
        if status:
            message="Available"
        else:
            message= "Unavailable"
        print(f"Warehouse has processed request from Buyer: {request.buyer_id} for {request.product} with {request.request_no} at time {datetime.now()} through trader: {request.trader_id} status:{message} ")

        return bully_pb2.PurchaseMessage(message=message, buyer_id= request.buyer_id, product= request.product, quantity= request.quantity, request_no= request.request_no) 
             
               
    
    
    def WarehouseCommunicationSeller(self,request, context): 
        amount_credit=self.update_inventory(str(request.seller_id), request.product, request.quantity)
        print(f"Warehouse registered Seller {request.seller_id} selling {request.product} with stock {request.quantity} with registration no {request.registration_no} at time {datetime.now()} through trader: {request.trader_id}")
        return bully_pb2.RegisterResponse(seller_id= request.seller_id, product=request.product, quantity= request.quantity, registration_no= request.registration_no, amount_credited=amount_credit,message="Registered" )  
    
    def TraderFailure(self, request, context): 
        print(f"Received message that {request.trader_id} has failed at time {datetime.now()}")
        with self.active_traders_lock:
            self.active_traders.remove(request.trader_id)
          
        print(self.active_traders )
        return bully_pb2.AckMessage(message="Acknowledged Failure")
    
    def AnnounceLeader(self, request, context):
        with self.active_traders_lock:
            self.active_traders.append(request.leader_id)
        print(f"Warehouse is aware of trader: {request.leader_id} at time {datetime.now()}")
        return bully_pb2.LeaderResponse(message="Leader acknowledged")



         
        


def serve(node_id,stock_file):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    service = BullyElectionService(node_id, stock_file)
    bully_pb2_grpc.add_BullyElectionServicer_to_server(service, server)
    server.add_insecure_port(f'[::]:{5000 + node_id}')
    server.start() 
    print(f"Warehouse process has started at port {5000 + node_id}.")
    time.sleep(10) 
    server.wait_for_termination()

if __name__ == "__main__":
    node_id = int(sys.argv[1])
    stock_file= "/Users/aishwarya/Downloads/cs677-lab3/stock.json"
    serve(node_id, stock_file)
