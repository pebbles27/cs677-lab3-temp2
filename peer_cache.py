# peer_cache.py

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
from queue import  Queue
from dataclasses import dataclass, field
from typing import Any 


@dataclass(order=True)
class PrioritizedItem:
    clock_value: int
    request: Any = field(compare=False)  
    role: Any= field(compare= False)
    trader_id: Any=field(compare=False)  
    # Represents a prioritized item for handling requests in the system
    def __iter__(self):
        # Allows unpacking attributes of the class
        yield self.clock_value
        yield self.request
        yield self.role
        yield self.trader_id

class LamportClock:
    # Implements Lamport logical clock for event ordering in distributed systems
    def __init__(self, node_id):
        self.value = 0
        self.node_id = node_id
        

    def tick(self):
            # Increments the clock value for an internal event
            self.value += 1
            # print(f"Node {self.node_id} - Lamport Clock Tick: {self.value}")
            return self.value 

    def update(self, received_value):
            # Updates the clock value based on a received timestamp
            self.value = max(self.value, received_value)
            # print(f"Node {self.node_id} - Received Clock: {received_value}, Updated Clock: {self.value}")
            return self.value

class BullyElectionService(bully_pb2_grpc.BullyElectionServicer):
    # Handles distributed election logic and manages trading operations
    def __init__(self, node_id, neighbors, role, log_file, no_of_nodes, opt_out=False):

        # Initializes election service with node-specific attributes, locks, and configurations
        self.node_id = node_id
        self.neighbors = neighbors
        self.leader_id = None
        self.in_election = False
        self.election_lock = threading.BoundedSemaphore(1)
        self.db_lock = threading.BoundedSemaphore(1)
        self.active_traders_lock = threading.BoundedSemaphore(1)
        self.opt_out = opt_out
        self.nodes = [i for i in range(1, no_of_nodes+1)]
        self.role = role
        self.active_traders = []
        self.lamport_clock = LamportClock(node_id)
        self.clock_lock= threading.BoundedSemaphore(1)
        self.log_lock= threading.BoundedSemaphore(1)
        self.log_file= log_file
        
        # self.request_queue = []
        # self.request_queue_lock = threading.BoundedSemaphore(1) 
        # self.seller_queue=[]
        # self.seller_queue_lock = threading.BoundedSemaphore(1) 
        self.requests_processed=0 
        self.is_election_running= True 
        self.warehouse_port= 5051
        self.heartbeat_reply_semaphore = threading.BoundedSemaphore(1)
        self.heartbeat_flag= True
        self.base_directory="/Users/aishwarya/Downloads/cs677-lab3"
        self.no_of_elections=0
        self.cache={"boar":0, "fish":0, "salt":0}
        self.cache_lock= threading.BoundedSemaphore(1)

        # Paths and locks for handling product-specific queues
        self.boar_queue_path= self.base_directory+f"/boarqueue{node_id}.pkl"
        self.fish_queue_path= self.base_directory+f"/fishqueue{node_id}.pkl"
        self.salt_queue_path= self.base_directory+f"/saltqueue{node_id}.pkl"
        self.boar_queue=[]
        self.fish_queue=[]
        self.salt_queue=[] 

        # Lock and tracking for underselling and overselling faults
        self.boar_queue_lock= threading.BoundedSemaphore(1)
        self.salt_queue_lock= threading.BoundedSemaphore(1)
        self.fish_queue_lock= threading.BoundedSemaphore(1)
        
        self.faults_lock= threading.BoundedSemaphore(1)
        self.faults={"underselling":0, "overselling":0}

    def ClockUpdate(self, request, context):
        # Updates the Lamport clock with a received value
        with self.clock_lock:
                self.lamport_clock.update(request.clock_value)
        return bully_pb2.ClockUpdateResponse(message="Clock updated")
        
    def broadcast_lamport_clock(self, clock_value):
        # Sends Lamport clock updates to all other nodes
        for node in self.nodes:
            if node!= self.node_id:
                try:
                    channel = grpc.insecure_channel(f'localhost:{5000 + node}')
                    stub = bully_pb2_grpc.BullyElectionStub(channel)
                    stub.ClockUpdate(bully_pb2.ClockMessage(clock_value=clock_value))
                except grpc.RpcError as e:
                    print(f"Node {self.node_id} failed to send clock update to Node {node}") 
    
    # Handles notifications of trader failure and updates active nodes and traders
    def TraderFailure(self, request, context): 
        print(f"Received message that {request.trader_id} has failed at time {datetime.now()}")
        with self.active_traders_lock:
            self.active_traders.remove(request.trader_id)
            self.nodes.remove(request.trader_id) 
        print("Active nodes are:",self.nodes,"Active traders are:",self.active_traders )
        return bully_pb2.AckMessage(message="Acknowledged Failure")


    ## TRADER - GRPC methods ##

    # Handles the request from seller to register a product 
    def SyncCache(self, request, context):
        print(f"Cache synced at time:{datetime.now()}")
        with self.cache_lock:
              self.cache["boar"]= request.boar 
              self.cache["fish"]= request.fish
              self.cache["salt"]= request.salt 
        return bully_pb2.AckMessage(message="Acknowleded")
        
    def RegisterProduct(self, request, context):
        # Handles product registration from sellers
        print(f"Registration Request: seller_id: {request.seller_id}, registration_no: {request.registration_no}, product {request.product}, quantity: {request.quantity} at {datetime.now()}")

        # Update Lamport clock for this event
        with self.clock_lock:
            clock_value=self.lamport_clock.update(request.clock)
        
        # Add the product to the respective queue based on type
        if request.product=="boar":
            with self.boar_queue_lock:
                heapq.heappush(self.boar_queue, PrioritizedItem(clock_value, request,"seller", self.node_id))
                # Persist updated queue to file
                try:
                    with open(self.boar_queue_path, "wb") as file:
                                pickle.dump(self.boar_queue, file, pickle.HIGHEST_PROTOCOL)
                except Exception as e:
                    print(e)
        if request.product=="fish":
            with self.fish_queue_lock:
                heapq.heappush(self.fish_queue, PrioritizedItem(clock_value, request,"seller", self.node_id))
                try:
                    with open(self.fish_queue_path, "wb") as file:
                                pickle.dump(self.fish_queue, file, pickle.HIGHEST_PROTOCOL)
                except Exception as e:
                    print(e)
        if request.product=="salt":
            with self.salt_queue_lock:
                heapq.heappush(self.salt_queue, PrioritizedItem(clock_value, request,"seller", self.node_id))
            
                try:
                    with open(self.salt_queue_path, "wb") as file:
                                pickle.dump(self.salt_queue, file, pickle.HIGHEST_PROTOCOL)
                except Exception as e:
                    print(e)

        # Confirm registration
        return bully_pb2.RegisterResponse(message="Received") 
    
    # Handles the request from a buyer to purchase a product
    def BuyRequest(self, request, context):
        print(f"Purchase Request: buyer_id: {request.buyer_id}, request_no: {request.request_no}, product {request.product}, quantity: {request.quantity} at {datetime.now()}")
        # Handles purchase requests from buyers
        # Update Lamport clock for the received request
        with self.clock_lock:
            clock_value=self.lamport_clock.update(request.clock)
        
        # Add the request to the respective product queue
        if request.product=="boar":
            with self.boar_queue_lock:
                heapq.heappush(self.boar_queue, PrioritizedItem(clock_value, request,"buyer", self.node_id))
                
                # Persist the updated boar queue
                try:
                    with open(self.boar_queue_path, "wb") as file:
                                pickle.dump(self.boar_queue, file, pickle.HIGHEST_PROTOCOL)
                except Exception as e:
                    print(e)
        
        if request.product=="fish":
            with self.fish_queue_lock:
                heapq.heappush(self.fish_queue, PrioritizedItem(clock_value, request,"buyer", self.node_id))
                
                # Persist the updated fish queue
                try:
                    with open(self.fish_queue_path, "wb") as file:
                                pickle.dump(self.fish_queue, file, pickle.HIGHEST_PROTOCOL)
                except Exception as e:
                    print(e)
        
        if request.product=="salt":
            with self.salt_queue_lock:
                heapq.heappush(self.salt_queue, PrioritizedItem(clock_value, request,"buyer", self.node_id))
                
                # Persist the updated salt queue
                try:
                    with open(self.salt_queue_path, "wb") as file:
                                pickle.dump(self.salt_queue, file, pickle.HIGHEST_PROTOCOL)
                except Exception as e:
                    print(e)
             
        return bully_pb2.BuyReturnResponse(message="Product Purchase Request Received")   
    
    # Heartbeat Protocol
    def HeartBeat(self, request, context):
        # print("Heartbeat", request)
        return bully_pb2.PingMessage(message="Alive!")
    
    # Helper methods 
    # Forwards buyer request to the warehouse 
    def forward_buyer_request_to_warehouse(self, buyer_id, product, quantity, clock, request_no, tid, message): 
        try:
            # print(f"Forwarding Request to warehouse: buyer_id: {buyer_id}, request_no: {request_no}, product: {product}, quantity: {quantity} at {datetime.now()}, trader: {tid}")
            channel = grpc.insecure_channel(f'localhost:{self.warehouse_port}')
            stub = bully_pb2_grpc.BullyElectionStub(channel)
            response=stub.WarehouseCommunicationBuyer(bully_pb2.WCBMessage(
                        buyer_id=buyer_id, product=product, quantity=quantity, request_no= request_no, trader_id= self.node_id, status= message
                    )) 
           
            t_message= response.message
            if message!= t_message:
                with self.faults_lock:

                    if message=="Available" and t_message=="Unavailable":
                        
                            self.faults["overselling"]+=1
                            print(f"Overselling: buyer_id: {buyer_id}, request_no: {request_no}, product: {product}, quantity: {quantity} at {datetime.now()}, trader: {tid}")
                    if message=="Unavailable" and t_message=="Available":
                        self.faults["underselling"]+=1
                        print(f"Underselling: buyer_id: {buyer_id}, request_no: {request_no}, product: {product}, quantity: {quantity} at {datetime.now()}, trader: {tid}")
                
            # channel = grpc.insecure_channel(f'localhost:{5000 + int(buyer_id)}')
            # stub = bully_pb2_grpc.BullyElectionStub(channel)
            # stub.PurchaseProcessed(bully_pb2.PurchaseMessage(
            #     message=message, buyer_id=buyer_id,product=product,quantity=quantity,request_no=request_no
            # )) 
        except Exception as e:
             print(e)
    
    # Forwards the seller request to the warehouse 
    def forward_seller_request_to_warehouse(self, seller_id, product, quantity, registration_no, tid):
        # print(f"Forwarding request to warehouse: seller_id: {seller_id}, registration_no: {registration_no}, product: {product}, quantity: {quantity}, trader:{tid} ")
        
        #forwarding the request to the trader 
        channel = grpc.insecure_channel(f'localhost:{self.warehouse_port}')
        stub = bully_pb2_grpc.BullyElectionStub(channel)
        response=stub.WarehouseCommunicationSeller(bully_pb2.WCSMessage(
                    seller_id=seller_id, product=product, quantity=quantity, registration_no= registration_no, trader_id= self.node_id
                ))   
        
        #forwarding the response to the seller 
        # channel = grpc.insecure_channel(f'localhost:{5000 + int(seller_id)}')
        # stub = bully_pb2_grpc.BullyElectionStub(channel)
        # stub.RegistrationProcessed(bully_pb2.RegisterResponse(
        #          seller_id=response.seller_id, product=response.product, quantity=response.quantity, registration_no= response.registration_no, amount_credited= response.amount_credited, message= response.message
        #     )) 
    
    #serves requests from the queue 

    def serve_request_boar(self):
        # Processes boar-related requests from buyers and sellers in the queue
        role=None
        time.sleep(20)   # Initial delay before starting request handling
        while True:
            with self.boar_queue_lock:
                if self.boar_queue:
                    # Fetch the next request from the boar queue
                    clock_value, request, role,tid= heapq.heappop(self.boar_queue) 
                        
                    if role== "buyer":
                        # Handle buyer request
                        with self.cache_lock:
                            if self.cache["boar"]>=request.quantity:       
                                self.cache["boar"]-= request.quantity 
                                message="Available" 
                            else:
                                 message="Unavailable"
                        
                        # Notify the buyer about the request status
                        channel = grpc.insecure_channel(f'localhost:{5000 + int(request.buyer_id)}')
                        stub = bully_pb2_grpc.BullyElectionStub(channel)
                        stub.PurchaseProcessed(bully_pb2.PurchaseMessage(
                            message=message, buyer_id=request.buyer_id,product=request.product,quantity=request.quantity,request_no=request.request_no
                        )) 
                        
                        # Forward the buyer request to the warehouse
                        threading.Thread(target= self.forward_buyer_request_to_warehouse, args=(request.buyer_id,request.product, request.quantity, 0, request.request_no,tid, message)).start() 
                    if role=="seller":
                        # Handle seller registration
                        with self.cache_lock:
                             self.cache["boar"]+= request.quantity
                        
                        # Notify the seller of successful registration
                        channel = grpc.insecure_channel(f'localhost:{5000 + int(request.seller_id)}')
                        stub = bully_pb2_grpc.BullyElectionStub(channel)
                        stub.RegistrationProcessed(bully_pb2.RegisterResponse(
                                seller_id=request.seller_id, product=request.product, quantity=request.quantity, registration_no= request.registration_no, amount_credited= 10, message= "OK"
                            )) 
                        
                        # Forward the seller request to the warehouse
                        threading.Thread(target= self.forward_seller_request_to_warehouse, args=(request.seller_id,request.product, request.quantity, request.registration_no, tid)).start() 
                         
                    # Save the updated queue state
                    with open(self.boar_queue_path, "wb") as file:
                            pickle.dump(self.boar_queue, file)
            
    def serve_request_fish(self):
        #  if self.node_id==5:
        #     time.sleep(1000)
        
        # Processes fish-related requests from buyers and sellers in the queue
        role=None
        time.sleep(20) # Initial delay before starting request handling
        while True:
            with self.fish_queue_lock:
                if self.fish_queue:
                    # Fetch the next request from the fish queue
                    clock_value, request, role,tid= heapq.heappop(self.fish_queue) 
                        
                    if role== "buyer":
                        # Handle buyer request
                        with self.cache_lock:
                            if self.cache["fish"]>=request.quantity:       
                                self.cache["fish"]-= request.quantity 
                                message="Available" 
                            else:
                                 message="Unavailable"
                        
                        # Notify the buyer about the request status
                        channel = grpc.insecure_channel(f'localhost:{5000 + int(request.buyer_id)}')
                        stub = bully_pb2_grpc.BullyElectionStub(channel)
                        stub.PurchaseProcessed(bully_pb2.PurchaseMessage(
                            message=message, buyer_id=request.buyer_id,product=request.product,quantity=request.quantity,request_no=request.request_no
                        )) 
                        
                        # Forward the buyer request to the warehouse
                        threading.Thread(target= self.forward_buyer_request_to_warehouse, args=(request.buyer_id,request.product, request.quantity, 0, request.request_no,tid, message)).start() 
                    if role=="seller":
                        with self.cache_lock:
                             self.cache["fish"]+= request.quantity
                        
                        # Notify the seller of successful registration
                        channel = grpc.insecure_channel(f'localhost:{5000 + int(request.seller_id)}')
                        stub = bully_pb2_grpc.BullyElectionStub(channel)
                        stub.RegistrationProcessed(bully_pb2.RegisterResponse(
                                seller_id=request.seller_id, product=request.product, quantity=request.quantity, registration_no= request.registration_no, amount_credited= 10, message= "OK"
                            )) 
                        threading.Thread(target= self.forward_seller_request_to_warehouse, args=(request.seller_id,request.product, request.quantity, request.registration_no, tid)).start() 

                    # Save the updated queue state   
                    with open(self.fish_queue_path, "wb") as file:
                            pickle.dump(self.fish_queue, file)
            
           
    def serve_request_salt(self):
        #  if self.node_id==5:
        #     time.sleep(1000)
        role=None
        time.sleep(20)
        while True:
            with self.salt_queue_lock:
                if self.salt_queue:
                    clock_value, request, role,tid= heapq.heappop(self.salt_queue) 
                        
                    if role== "buyer":
                        with self.cache_lock:
                            if self.cache["salt"]>=request.quantity:       
                                self.cache["salt"]-= request.quantity 
                                message="Available" 
                            else:
                                 message="Unavailable"
                            
                        channel = grpc.insecure_channel(f'localhost:{5000 + int(request.buyer_id)}')
                        stub = bully_pb2_grpc.BullyElectionStub(channel)
                        stub.PurchaseProcessed(bully_pb2.PurchaseMessage(
                            message=message, buyer_id=request.buyer_id,product=request.product,quantity=request.quantity,request_no=request.request_no
                        )) 
                        threading.Thread(target= self.forward_buyer_request_to_warehouse, args=(request.buyer_id,request.product, request.quantity, 0, request.request_no,tid, message)).start() 
                    if role=="seller":
                        with self.cache_lock:
                             self.cache["salt"]+= request.quantity
                        
                        channel = grpc.insecure_channel(f'localhost:{5000 + int(request.seller_id)}')
                        stub = bully_pb2_grpc.BullyElectionStub(channel)
                        stub.RegistrationProcessed(bully_pb2.RegisterResponse(
                                seller_id=request.seller_id, product=request.product, quantity=request.quantity, registration_no= request.registration_no, amount_credited= 10, message= "OK"
                            )) 
                        threading.Thread(target= self.forward_seller_request_to_warehouse, args=(request.seller_id,request.product, request.quantity, request.registration_no, tid)).start() 
    
                    # Save the updated queue state
                    with open(self.salt_queue_path, "wb") as file:
                            pickle.dump(self.salt_queue, file)
 
    # Loop to monitor nodes 
    def monitoring_nodes(self):
        time.sleep(5)
        
        while self.heartbeat_flag:
            other_traders= [trader for trader in self.active_traders if self.node_id != trader ]
            # print(other_traders)
            for node in other_traders:  
                channel = grpc.insecure_channel(f'localhost:{5000 + node}')
                stub = bully_pb2_grpc.BullyElectionStub(channel)
                try:
                    response=stub.HeartBeat(bully_pb2.PingMessage( message="Are you there?"), timeout=5) 
                
                except grpc.RpcError as e:
                    with self.active_traders_lock:
                        self.active_traders.remove(node) 
                        self.heartbeat_flag= False 
                
            time.sleep(5) 
        
        self.trader_failure(other_traders[0])  # Handle failure of another trader

        # Merge boar queue from the failed trader
        with self.boar_queue_lock:
            print("Merging queue of boar")
            
            file_name= f"{self.base_directory}/boarqueue{other_traders[0]}.pkl"
            with open(file_name, "rb") as file:
                    pq = pickle.load(file) 
            print("requests before:",self.boar_queue)    
        
            merged_pq = pq+ self.boar_queue
            heapq.heapify(merged_pq) 
           
            self.boar_queue= merged_pq   
            print("requests after:",self.boar_queue)  
            with open(self.boar_queue_path, "wb") as file:
                            pickle.dump(self.boar_queue, file, pickle.HIGHEST_PROTOCOL) 
        
        # Merge fish queue from the failed trader
        with self.fish_queue_lock:
            print("Merging queue of fish")
            file_name= f"{self.base_directory}/fishqueue{other_traders[0]}.pkl"
            with open(file_name, "rb") as file:
                    pq = pickle.load(file) 
            print("requests before:",self.fish_queue)    
    
            merged_pq = pq+ self.fish_queue
            heapq.heapify(merged_pq) 
           
            self.fish_queue= merged_pq   
            print("requests after:",self.fish_queue)  
            with open(self.fish_queue_path, "wb") as file:
                            pickle.dump(self.fish_queue, file, pickle.HIGHEST_PROTOCOL)
        
        # Merge salt queue from the failed trader
        with self.salt_queue_lock:
            print("Merging queue of salt")
            file_name= f"{self.base_directory}/saltqueue{other_traders[0]}.pkl"
            with open(file_name, "rb") as file:
                    pq = pickle.load(file) 
            print("requests before:",self.salt_queue)    
        

            merged_pq = pq+ self.salt_queue
            heapq.heapify(merged_pq) 
           
            self.salt_queue= merged_pq   
            print("requests after:",self.salt_queue)  
            with open(self.salt_queue_path, "wb") as file:
                            pickle.dump(self.salt_queue, file, pickle.HIGHEST_PROTOCOL)
       
    # Notify other nodes about the failure of a trader
    def trader_failure(self, failed_trader_id):
        for node in self.nodes:
            if node not in self.active_traders and node!=failed_trader_id:
                channel = grpc.insecure_channel(f'localhost:{5000 + node}')
                stub = bully_pb2_grpc.BullyElectionStub(channel)
                response=stub.TraderFailure(bully_pb2.FailedTraderMessage( message="Trader failure announcement", trader_id= failed_trader_id), timeout=3)

    # Notify the warehouse about the failed trader for cache adjustments
        # will be useful for cached approach to tell the warehouse not to push anything to the failed trader
        channel = grpc.insecure_channel(f'localhost:{self.warehouse_port}')
        stub = bully_pb2_grpc.BullyElectionStub(channel)
        response=stub.TraderFailure(bully_pb2.FailedTraderMessage( message="Trader failure announcement", trader_id= failed_trader_id), timeout=3) 
  
    
    ## SELLER - GRPC methods ##
   
    def RegistrationProcessed(self, request, context):
        # Acknowledges successful registration of a seller's product
        print(f"Trader Acknowledgment: seller_id: {request.seller_id}, registration_no: {request.registration_no}, product: {request.product}, quantity: {request.quantity} at time {datetime.now()} ")
        return bully_pb2.AckMessage(message="Acknowledged")

    def register_product(self):
        # Simulates product registration by the seller
        time.sleep(10) # Initial delay before starting registration
        for i in range(50):
                # Increment Lamport clock and broadcast the updated value
                with self.clock_lock:
                    try:
                        _=self.lamport_clock.tick()
                        clock_value= self.lamport_clock.value
                        threading.Thread(target=self.broadcast_lamport_clock, args=(clock_value,)).start()
                    except:
                         pass
               
               # Randomly select a product and quantity for registration
                product = random.choice(["salt", "boar", "fish"])
                quantity = random.randint(5, 20)
                
                # Choose an active trader to handle the registration
                with self.active_traders_lock:
                    trader= random.choice(self.active_traders)
                # if trader==5:
                #      quantity=0
                print(f"Registration {i}: seller_id: {self.node_id}, product: {product}, quantity: {quantity}, trader: {trader} at time {datetime.now()}")
                
                # Send the registration request to the selected trader
                channel = grpc.insecure_channel(f'localhost:{5000 + trader}')
                stub = bully_pb2_grpc.BullyElectionStub(channel)
                try:
                    response=stub.RegisterProduct(bully_pb2.ProductDetails(
                        seller_id=self.node_id, product=product, quantity=quantity, registration_no=i, clock= self.lamport_clock.value
                    ))
                except grpc.RpcError as e:
                    pass
                
                # sleep_time=random.randint(10,30)
                time.sleep(5)  # Delay between successive registrations              
                        
    
    ## BUYER - GRPC methods ##

    def PurchaseProcessed(self, request, context):
        # Logs the transaction details after processing a purchase request
        print(f"Transaction: message: {request.message},buyer_id: {request.buyer_id}, request_no: {request.request_no}, product: {request.product}, quantity: {request.quantity} at time {datetime.now()}")
        return bully_pb2.PurchaseResponse(message="Okay")

    def buy_product(self):
        # Simulates a buyer making product purchase requests
        sleep_time = 10 * self.node_id - 4 # Initial delay based on node ID
        time.sleep(sleep_time)
        for i in range(50):
            # Increment Lamport clock and broadcast the updated value
            with self.clock_lock:
                try:
                    _=self.lamport_clock.tick()
                    clock_value= self.lamport_clock.value
                    threading.Thread(target=self.broadcast_lamport_clock, args=(clock_value,)).start()
                except:
                     pass
            # Select a random active trader to handle the purchase
            with self.active_traders_lock:
                trader= random.choice(self.active_traders)
            
            # Select a random product and quantity for purchase
            product = random.choice(["salt", "boar", "fish"])
            quantity=random.randint(1,3)
            
            # Establish a connection with the selected trader
            channel = grpc.insecure_channel(f'localhost:{5000 + trader}')
            stub = bully_pb2_grpc.BullyElectionStub(channel)
            
            # Log the purchase request details
            print(f"Request: buyer_id:{self.node_id}, request_no:{i}, product:{product}, quantity:{quantity}, trader:{trader} at time {datetime.now()}")
            
            # Send the purchase request to the trader
            try:
                response=stub.BuyRequest(bully_pb2.BuyRequestMessage(
                            buyer_id=self.node_id, product=product, quantity=quantity, clock=self.lamport_clock.value, request_no= i
                        ))  
            except Exception as e:
                    pass
            # print(response)

            # Delay between successive purchase requests
            sleep_time=random.randint(10,30)+ self.node_id
            time.sleep(10) 
    
    # Bully Election Algorithm for Trader Election
    def ElectionMessage(self, request, context):
        # Handles an incoming election request from another node
        self.is_election_running= True
        sender_id = request.sender_id
        print(f"Node {self.node_id} received election request from Node {sender_id} at time {datetime.now()}")

        # Opt out of the election if the node is already a trader
        if self.opt_out:
            print(f"Node {self.node_id} is opting out of the election because it is already a trader.")
            self.forward_election(request.node_id)
            return bully_pb2.ElectionResponse(acknowledgment=False)

        # Participate in the election if the node ID does not match the request ID
        if request.node_id !=self.node_id:
            print(f"Node {self.node_id} is participating in the election. Sending acknowledgment.")
            self.start_election()
            return bully_pb2.ElectionResponse(acknowledgment=True)

        # Default response for invalid or redundant election requests
        return bully_pb2.ElectionResponse(acknowledgment=False)

    def AnnounceLeader(self, request, context):
        # Handles leader announcement during the election process
        self.no_of_elections+=1
        if self.node_id!= request.leader_id:
            # Add the new leader to the list of active traders
            with self.active_traders_lock:
                    self.active_traders.append(request.leader_id)
            print(f"Node {self.node_id} acknowledged new trader: Node {request.leader_id} at time {datetime.now()}")
            print("The active traders are : ", self.active_traders)
           
        if self.no_of_elections==2:
            # If election count is 2, handle roles based on node status           
            if self.role == "seller" and self.node_id not in self.active_traders:             
                threading.Thread(target=self.register_product).start() # Start product registration   
            if self.role=="buyer" and self.node_id not in self.active_traders:
                threading.Thread(target=self.buy_product).start() # Start buying process
            if self.node_id in self.active_traders:
                # Clear queues for active traders
                with open(self.boar_queue_path, "wb") as file:
                            pickle.dump([], file, pickle.HIGHEST_PROTOCOL)
                with open(self.fish_queue_path, "wb") as file:
                            pickle.dump([], file, pickle.HIGHEST_PROTOCOL)
                with open(self.salt_queue_path, "wb") as file:
                            pickle.dump([], file, pickle.HIGHEST_PROTOCOL)
                
                # Start monitoring and request serving threads
                threading.Thread(target=self.monitoring_nodes).start()
                threading.Thread(target= self.serve_request_boar).start()
                threading.Thread(target= self.serve_request_fish).start()
                threading.Thread(target= self.serve_request_salt).start()       
        else:
            # Restart election if conditions are met
            if self.node_id==3:
                threading.Thread(target=self.start_election).start()
        return bully_pb2.LeaderResponse(message="Leader acknowledged")

    def start_election(self):
        # Initiates the election process for the node
        if self.no_of_elections==1 and self.node_id==3:
            time.sleep(6)
            print("Second election")
        # Prevent concurrent elections
        if not self.election_lock.acquire(blocking=False):
            return
        try:
            self.in_election = True
            print(f"Node {self.node_id} is starting an election at time {datetime.now()}")
            
            # Identify neighbors with higher IDs
            higher_neighbors = [n for n in self.neighbors if n > self.node_id]

            # If no higher neighbors exist and not opting out, declare leadership
            if not higher_neighbors and not self.opt_out:
                self.election_lock.release()
                self.announce_leader()
                return

            # If no higher neighbors exist and opting out, contact the lowest node
            if not higher_neighbors and self.opt_out:
                time.sleep(20)
                channel = grpc.insecure_channel(f'localhost:{5000 + 1}')
                stub = bully_pb2_grpc.BullyElectionStub(channel)
                response = stub.ElectionMessage(bully_pb2.ElectionRequest(node_id=self.node_id, sender_id=self.node_id))
                if response.acknowledgment:
                        received_ack = True
                        self.in_election = False
                        self.election_lock.release()
                        return 
            # Notify higher neighbors about the election
            received_ack = False
            for neighbor in higher_neighbors:
                try:
                    channel = grpc.insecure_channel(f'localhost:{5000 + neighbor}')
                    stub = bully_pb2_grpc.BullyElectionStub(channel)
                    response = stub.ElectionMessage(bully_pb2.ElectionRequest(node_id=self.node_id, sender_id=self.node_id))
                    if response.acknowledgment:
                        received_ack = True
                        self.in_election = False
                        self.election_lock.release()
                        return
                except grpc.RpcError as e:
                    print(f"Node {self.node_id} failed to contact Node {neighbor}: {e}")

            # Declare leadership if no acknowledgment is received
            if not received_ack:
                self.election_lock.release()
                self.announce_leader()
        except:
            print("error")
     

    def forward_election(self, initiator_id):
        # Forwards the election request to higher-ranked neighbors
        higher_neighbors = [n for n in self.neighbors if n > self.node_id]
        for neighbor in higher_neighbors:
            try:
                channel = grpc.insecure_channel(f'localhost:{5000 + neighbor}')
                stub = bully_pb2_grpc.BullyElectionStub(channel)
                stub.ElectionMessage(bully_pb2.ElectionRequest(node_id=initiator_id, sender_id=self.node_id))
            except grpc.RpcError as e:
                print(f"Node {self.node_id} failed to forward election request to Node {neighbor}: {e}")

    def announce_leader(self):
        # Declares the current node as the leader and notifies relevant entities
        # self.leader_id = self.node_id
        with self.active_traders_lock:
             self.active_traders.append(self.node_id)
        print(f"Node {self.node_id} is a trader. Election conluded at time {datetime.now()}")
        print("The active traders are: ", self.active_traders)
        self.is_election_running= False
        self.opt_out= True # Mark the node as a trader
        
        # Notify the warehouse about the new leader
        channel = grpc.insecure_channel(f'localhost:{self.warehouse_port}')
        stub = bully_pb2_grpc.BullyElectionStub(channel)
        stub.AnnounceLeader(bully_pb2.LeaderAnnouncement(leader_id=self.node_id))

        for neighbor in self.nodes:
            # if neighbor != self.node_id:
                # print(neighbor)
                try:
                    # Notify all nodes about the new leader
                    channel = grpc.insecure_channel(f'localhost:{5000 + neighbor}')
                    stub = bully_pb2_grpc.BullyElectionStub(channel)
                    stub.AnnounceLeader(bully_pb2.LeaderAnnouncement(leader_id=self.node_id))
                except grpc.RpcError as e:
                    print(f"Node {self.node_id} failed to announce leader to Node {neighbor}: {e}") 

def serve(node_id, neighbors, role, log_file, no_of_nodes, opt_out):
    # Initializes and starts the gRPC server for the node
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    service = BullyElectionService(node_id, neighbors, role,log_file, no_of_nodes, opt_out)
    bully_pb2_grpc.add_BullyElectionServicer_to_server(service, server)
    server.add_insecure_port(f'[::]:{5000 + node_id}')
    server.start() 
    print(f"Node {node_id} started.")
    
    # Start election if this is the initiating node
    time.sleep(10)
    if node_id == 2:
        # print(f"Node {node_id} starting election at time {datetime.now()}")
        threading.Thread(target=service.start_election).start()
    server.wait_for_termination()

if __name__ == "__main__":
    # Entry point for initializing and running the node
    node_id = int(sys.argv[1])  # Node ID from command-line arguments
    role = sys.argv[2]  # Role (buyer, seller, trader) from command-line arguments
    no_of_nodes = int(sys.argv[3])  # Total number of nodes in the system

    # File paths for stock, logs, and topology
    stock_file= "/Users/aishwarya/Downloads/cs677-lab3/stock.json"
    log_file= "/Users/aishwarya/Downloads/cs677-lab3/logs.csv"
    topology_file= f"/Users/aishwarya/Downloads/cs677-lab3/topology{no_of_nodes}.json" 
    
    # Load network topology
    with open(topology_file, "r") as file:
        topology = json.load(file)
    
    # Get neighbors for the node
    neighbors = topology[str(node_id)]
    opt_out = node_id == 11

    # Start the server for the node
    serve(node_id, neighbors, role, log_file, no_of_nodes, opt_out)
