
""" This is a basic simulation of consumer-producer market model using the
SimPY library. """

'''

TODO:
 * consider a consumer motivated by time, or deadline (optional?) 
   * this requires the incorporation of a consumer deadline and different
   * clearly, a minimal time chooses machine with most capacity
 * consider consumer utilization % (assumer 100% now)
 * Monitoring / Data collection on consumers, resources
   - total money spent
   - total work done
   - income to provider
   - average job cost
   - average job length
   - average price per unit

 * wrap your head about how simulation steps relate to time.
   - a simulation step can represent anything: secs -> mins -> hours
   - time-per-step ratio should be global
   - time-per-step must be <= min unit time

'''
import math
import random
import csv, codecs, cStringIO
from SimPy.Simulation import *
from CSVUtility import *

# Props ##################################################################### 

class Unit():
  """ compute unit - capacity over time """
  def __init__(self, capacity, time, cost):
    self.capacity = capacity  # work capacity (CPU throughput)
    self.time  = time         # the number of simulation steps a unit costs " 
    self.cost  = cost         # base (on-demand) cost of unit 

class Lease():
  """ lease duration and costs """
  """ on-demand instances have a zero length and down payment """
  def __init__(self, length, downp, puc):
    self.length = length  # required length (0 = no limit)
    self.downp = downp    # down payment
    self.puc = puc        # percentage unit cost

class Instance(): 
  """ an compute instance """
  def __init__(self, name, desc, unit, lease):
    self.name = name
    self.desc = desc
    self.unit = unit       # unit classes
    self.lease = lease     # package class
    self.invoked = 0       # statistics

  def maxunits(self, l=self.lease, u=self.unit):
    return math.floor(l.length / u.time)
  #max work?
  
  """
  we are given a requested amount of work.  Return the work completed, work
  remaining, total cost and efficiency for this instance 
  """
  def analyize(self, work):
    # partial units consumed are billed as a full unit 
    req_units = math.ceil(work / self.unit.capacity) # requested units
    max_units = maxunits() #math.floor(self.lease.length / self.unit.time)  
    rmdr = 0
    rtime = 0 # remaining time on lease
    # on-demand leases have a zero length 
    if (self.lease.length > 0):
      # a fixed lease can processes limited number of units
      if (req_units > max_units):
        req_units = max_units
        rmdr = work - (max_units * self.unit.capacity)
        work = max_units * self.unit.capacity
      # endif
      rtime = self.lease.lenth - (req_units * self.unit.time)
    # cost = downpayment + (units# * basecost * discount)
    cost =  self.lease.downp + req_units * self.unit.cost * self.lease.puc
    time = req_units * self.unit.time
    rate = work / time # work rate
    cpr = rate / cost # cost efficency 

    #print self.name, " analysis:", cost, req_units, rmdr, time
    return {'cost': cost, 'time': time, 'work':work, 'rmdr': rmdr,
        'rate':rate, 'cpr':cpr, 'rtime':rtime}
  
  """ list the data for instance """
  def results(self):
    return [self.invoked, self.desc, self.unit.capacity, self.unit.time, \
        self.unit.cost, self.lease.puc, (self.unit.cost * self.lease.puc),\
        self.lease.length, self.lease.downp] 
    

## actors  ########################################################### 

class Consumer(Process):
  """ a basic consumer motivated by overall cost """
  def __init__(self, name, work, start, sim):
    Process.__init__(self, name=name, sim=sim)
    self.work =  work
    self.rmdr =  work
    self.spent = 0
    self.start = start
    self.finish = 0

  """ search list best cost efficiency """
  def shop(self, work, instance_list):
    prev = 0
    for inst in instance_list: 
      # there has to be a better way code this...
      data = inst.analyize(work)
      tmp = data['cpr'] 
      if tmp >= prev or prev == 0:
        prev = tmp
        rtn = data
        rtn['inst'] = inst
    rtn['inst'].invoked += 1
   # print "======================================\n", rtn['inst'].results()
    return rtn

  """ purchase resource based on the results of financial analysis """
  def purchase(self):
    while self.rmdr > 0:
      data = self.shop(self.rmdr, self.sim.instances)
      self.spent += data['cost']
      self.rmdr = data['rmdr']
      yield hold, self, data['time']
    self.finish = self.sim.now()

  def results(self):
    """ return consumer data list """
    return [self.name, self.work, self.spent, self.start, self.finish] 


## stage ############################################################# 

class Marketplace(Simulation):
  def __init__(self, name, instances, consumer_count, maxwork, maxtime):
    Simulation.__init__(self)
    self.name = name
    self.instances = instances 
    self.consumer_count = consumer_count
    self.maxwork = maxwork
    self.maxtime = maxtime
    self.consumers = []

  def generate_work(self):
    """ generate a random work amount for consumer """
    return random.randint(1, self.maxwork) # replace with a gaussian range? 

  def generate_start(self):
    """ generate a random arrival time for consumer """
    return random.randint(0, self.maxtime - self.maxwork) # we may need min unit-val 

  def generate_deadline(self):
    """ generate a random deadline for consumer """
    return random.randint(0, 1) # this is very wrong

  def spawn_consumers(self):
    """ spawn and activate consumers for simulation """
    for i in range(self.consumer_count):
      con = Consumer(name="con_%s"%i, work=self.generate_work(), \
          start=self.generate_start(), sim=self)
      self.consumers.append(con)
      self.activate(con, con.purchase(), at=con.start)

  def start(self):
    self.initialize()
    print self.now(), ':', self.name, 'started',self.consumer_count,'consumers'
    self.spawn_consumers()
    self.simulate(until=self.maxtime)

  def finish(self):
    print self.now(), ':', self.name, 'finished.'

  def results(self, filename):
    filea = self.name+"_inst";
    inst_out = CSVExport(filea)
    fileb = self.name+"_cons";
    cons_out = CSVExport(fileb)
    # ---  
    for inst in self.instances:
      inst_out.writerow(inst.results())
    for cons in self.consumers:
      cons_out.writerow(cons.results())
# fin.
