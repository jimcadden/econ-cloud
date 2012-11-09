
""" This is a basic simulation of consumer-producer market model using the
SimPY library. """

'''
TODO:
  * consider a consumer motivated by time over money
    * this requires the incorporation of a consumer deadline and different
    * unit sizes (i.e. more power/time) at variable prices
  * look into monitoring on consumers, resources
    - money spent by consumers (total, average)
    - income to resource 

'''
import math
from SimPy.Simulation import *
  
## experimental data  ################################################ 

CONSUMER_COUNT = 5
MAX_CONSUMERS = 5
MAX_WORK = 1000000
MAXTIME  = 1000000

# Props ##################################################################### 

class Unit():
  """ compute unit - capacity over time """
  def __init__(self, capacity, time):
    self.capacity = capacity  # work capacity
    self.time  = time         # the number of simulation steps a unit costs " 

class Lease():
  """ lease duration and costs """
  """ on-demand instances have a zero length and downpayment """
  def __init__(self, length, downp, cpu):
    self.length = length  # required length (0 = no limit)
    self.downp = downp    # down payment
    self.cpu = cpu        # cost per unit

class Instance(): 
""" an compute instance """
  def __init__(self, name, unit, lease):
    self.name = name
    self.unit = unit      # unit classes
    self.lease = lease    # package class

  def analyze(self, work):
    """ return the cost required """
    req_units = work / self.unit.capacity   # units required
    max_units = self.lease.length / self.unit.time
    if max_units < req_units and max_units != 0 :
      req_units = max_units
    # Partial instance-time consumed are billed as a full unit 
    cost =  self.lease.dpayment + (math.ceil(req_units) * self.lease.cpu)
    remainder = (work / self.unit.capacity) - req_units
    time = req_units * self.unit.time
    return {'cost': cost, 'rem': rem, 'time': time}


## actors  ########################################################### 

class Consumer_a(Process):
  """ a basic consumer, only work, motivated to minimise cost """
  def __init__(self, name, work, sim):
    Process.__init__(self, name=name, sim=sim)
    self.work =  work
    self.cost = 0

  def analysis(self, work):
    """ check the economic landscape and return which product to purchase. """
    prev = 0
    for inst in self.sim.instances:
      print "checking instance:", inst.name
      tmp = inst.cost(work)
      if tmp <= prev or prev == 0:
        rinst = inst
        prev = tmp
    print "cost for", work, "work will be", rinst.cost(work), " with ", rinst.name
    return rinst

  def purchase(self):
    """ purchase resource based on the results of financial analysis"""
    print self.sim.now(), self.name, 'Starting'
    while self.work > 0:
      inst = self.analysis(self.work)
      self.cost = self.cost + inst.cost(self.work);
      self.work = inst.remainder(self.work)
      yield hold, self, 100
    print self.sim.now(), self.name, 'Finished Work. Cost:', self.cost


## stage ############################################################# 

class Marketplace(Simulation):
  def __init__(self, name, instances):
    Simulation.__init__(self)
    self.name = name
    self.instances = instances 
    self.p_income = 0 # provider income THIS MIGHT NOT LAST..

  def spawn_consumers(self):
    """ spawn consumers for simulation """
    for i in range(CONSUMER_COUNT):
      con = Consumer_a(name="con_%s"%i, work=GWORK, sim=self)
      self.activate(con, con.purchase())

  """ i wonder if we can get away with just a single a store that lists
  both the the provider and the resellers availability"""
  """ or no store at all, since the only real benefit is the monitor which
  dosent tell us much... I am going to have to find a way to capture more/all
  data"""
  def set_resouce(self):
    """ """
    None

  def start(self):
    self.initialize()
    self.spawn_consumers()
    self.simulate(until=MAXTIME)


## Start the show!  ##################################################### 

if __name__=="__main__":
  ## this is all temporary, to be replaced w/ CSV import
  on_demand   = {'name':"small on-demand", 'len':0, 'dp':0, 'cpu':.065,
      'time':60, 'cap':1}
  one_year   = {'name':"small one-year", 'len':8760, 'dp':195, 'cpu':.016,
      'time':60, 'cap':1}
  three_year   = {'name':"small three-year", 'len':(8760*3), 'dp':300,
      'cpu':.013, 'time':60, 'cap':1}
  
  ## TODO: move this into maketplace, move the above list to global 
  def gen_instance(config):
    """ config = dict{name, lenght, downpayment, cpu} """
    l = Lease(config['len'], config['dp'], config['cpu'])
    u = Unit(config['cap'], config['time'])
    return Instance(config['name'], u, l) 

  #TODO: 
  ilist = []
  ilist.append(gen_instance(on_demand))
  ilist.append(gen_instance(one_year))
  ilist.append(gen_instance(three_year))

  sim1 = Marketplace( name = "basic simulation", instances = ilist)
  sim1.start()
  print sim1.now()

# fin.
