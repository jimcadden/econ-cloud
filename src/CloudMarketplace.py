""" This is a basic simulation of consumer-producer market model using the
SimPY library. """
'''
TODO:
 * consider a consumer motivated by time, or deadline (optional?) 
   * this requires the incorporation of a consumer deadline and different
   * clearly, a minimal time chooses machine with most capacity
 * wrap your head about how simulation steps relate to time.
   - a simulation step can represent anything: secs -> mins -> hours
   - time-per-step ratio should be global
   - time-per-step must be <= min unit time
'''
import math
from SimPy.Simulation import *

DEBUG = 0

# Props ##################################################################### 

class Unit():
  """ compute unit - capacity over time """
  def __init__(self, capacity, time, cost):
    self.capacity = capacity  # work capacity (CPU throughput)
    self.time  = time         # the number of simulation steps a unit costs " 
    self.cost  = cost         # base (on-demand) cost of unit 

class Lease():
  def __init__(self, length, downp, puc):
    """ lease duration and costs """
    self.length = length  # required length (0 = no limit)
    self.downp = downp    # down payment
    self.puc = puc        # percentage unit cost

class Instance(): 
  def __init__(self, name, desc, unit, lease):
    """ an compute instance """
    self.name = name
    self.desc = desc
    self.unit = unit       # unit classes
    self.lease = lease     # package class

  def analyize(self, work, prvwork=0, prvtime=0, prvcost=0):
    """
    Return the amount completed, work remaining, total cost and 
    efficiency rating for a given amount of work
    """
    rmdr = 0  # remaning work
    rtime = 0 # remaining time on lease
    req_units = math.ceil(work / self.unit.capacity) # no partial units
    max_units = math.floor(self.lease.length / self.unit.time)  
    """ on-demand leases have a zero length """
    if (self.lease.length > 0):
      if (req_units > max_units): #we need more work than lease allows
        req_units = max_units
        rmdr = work - (max_units * self.unit.capacity)
        work = max_units * self.unit.capacity
      # endif
      rtime = self.lease.length - (req_units * self.unit.time)
    #endif
    cost =  self.lease.downp + (req_units * (self.unit.cost * self.lease.puc))
    time = req_units * self.unit.time
    eff  = self.efficiency(work+prvtime, cost+prvcost, time+prvtime) 

    if DEBUG: print "|w,rw,c,t,rm,ef", self.desc,":", work,rmdr, cost, time, rtime, eff
    return {'cost':cost, 'time':time, 'work':work, 'rmdr':rmdr, 'eff':eff,
        'rtime':rtime}

  def efficiency(self, work, cost, time):
      return work / cost / time

  """ list the data for instance """
  def results(self):
    return [self.name, self.desc, self.unit.capacity, self.unit.time, \
        self.unit.cost, self.lease.puc, (self.unit.cost * self.lease.puc),\
        self.lease.length, self.lease.downp] 
    
## actors  ########################################################### 

class Consumer(Process):
  def __init__(self, name, work, start, actual, sim):
    """ a basic consumer motivated by overall cost """
    Process.__init__(self, name=name, sim=sim)
    self.work =  work
    self.actual = actual
    self.start = start
    self.purchases = []
    self.finish = 0
    self.comp = 0 # completed work
    self.rtime = 0 # remaing time
    self.spent = 0 # money spent

  def optimal_instance(self, work, instance_list, rdepth=0, prvwork=0, prvcost=0,
      prvtime=0, depth=0):
    """ A recursive search of list instances that considers (depth) steps into
    the future and returns the best immediate puchase 
    """

    if work <= 0:
      if DEBUG: print "shit this happened!@!"
      return prvwork / prvcost / prvtime

    """
    Recusive analysis scan of available isntances
    """
    max_eff = inst = 0
    for i in instance_list:
      data = i.analyize(work) 
      if depth < rdepth:
        """ recusive check of next-purchases """
        if data['rmdr'] > 0:
          if DEBUG: print "++ depth",depth,", rmdr",data['rmdr'],"++"
          """ check the hash for best data """
          try:
            data = self.sim.cache[data['work']*self.sim.cache_bucket(work)]
            if DEBUG: print "@ cache hit:", self.sim.cache_bucket(work),"round",data['work']
          except KeyError:
            if DEBUG: print "@ cache miss:",self.sim.cache_bucket(work),"round",data['work']
            data = self.optimal_instance(data['rmdr'], instance_list,rdepth, data['work']+prvwork,
                data['cost']+prvcost, data['time']+prvtime, depth+1)
            """ check the hash for best data """
            self.sim.cache[data['work']*self.sim.cache_bucket(work)] = data

      if data['eff'] >= max_eff:
        if DEBUG: "d:",depth,"max eff updated:",i.desc, data['eff']
        """ if we've found a path with a better efficiency """
        max_eff = data['eff']
        best_inst  = i

    """ get a fresh results """ 
    rtn = best_inst.analyize(work)
    rtn['inst'] = best_inst
    return rtn

#  def optimal_instance(self, work, instance_list):
#    """ search list for best cost efficiency, i.e, most work per dollar  """
#    rtn = 0
#    peff = 0
#    for inst in instance_list: 
#      data = inst.analyize(work) # get instance report for data
#      teff = data['eff'] 
#      if teff >= peff or peff == 0:
#        peff = teff
#        rtn = data
#        rtn['inst'] = inst
#    return rtn

  def purchase(self, work, instance_list):
    """ shop for efficiency """
    rtn = self.optimal_instance(work, instance_list, self.sim.rdepth)
    self.purchases.append(rtn['inst'].name)
    if DEBUG:
      print ">>",self.name,"todo",work,"PURCHASED:", rtn['inst'].desc,\
        rtn['cost'],rtn['eff'], rtn['rtime'], rtn['rmdr']
    return rtn

  def process(self):
    """ process work by purchasing instances
    case 1: overshoot: completed work > expected work. We treat actual work
       as our new 'high' expectation
    case 2: undershoot: job end unexpectely 
    """
    # shouldnt happen, but just incase
    if self.actual == 0: 
      self.comp = -1
    if DEBUG: 
      print ">>>", self.name,"START | exp:",self.work," actual:",self.actual
    while self.actual > self.comp:
      data = self.process_inner()
      self.bookkeeping(data) #record puchase details
      yield hold, self, data['time']
    #end while
    if data['rtime'] > 0: #global remaining time
      self.sim.rtime += data['rtime']
    self.finished()

  def process_inner(self):
    exp_rem = self.work - self.comp
    act_rem = self.actual - self.comp
    if DEBUG: 
      print ">>> REMAINDER: exp:", exp_rem, "act:", act_rem, "comp:",self.comp 
    """ Case 1 """
    if self.comp >= self.work:
      exp_rem = act_rem
    """ select our instance to purchase """
    data = self.purchase(exp_rem, self.sim.instances) # purchase instance 
    """ Case 2 """
    if data['work'] > act_rem: 
      if DEBUG: 
        print "job ended unexpectedly"
      instance = data['inst']
      data = instance.analyize(act_rem)
      data['inst'] = instance
    return data

  def bookkeeping(self, data):
    """ update our simulation stats """
    rtn = data
    """ consumer data """
    self.rmdr = rtn['rmdr']
    self.spent += rtn['cost']
    self.comp += rtn['work']
    self.rtime = rtn['rtime']
    """ market data """
    self.sim.income += rtn['cost']
    """ instance data """
    self.sim.books[rtn['inst'].name]['invoked'] += 1
    self.sim.books[rtn['inst'].name]['income'] += rtn['cost']
    self.sim.books[rtn['inst'].name]['work'] += rtn['work']
    self.sim.books[rtn['inst'].name]['time'] += rtn['time']
    self.sim.books[rtn['inst'].name]['rtime'] += rtn['rtime']

  def finished(self):
    self.finish = self.sim.now()
    self.sim.finished += 1

  def results(self):
    """ return consumer data list """
    time = self.finish - self.start # total time
    return [self.name, self.work, self.actual, self.comp, self.spent, 
        time, self.start, self.finish, self.rtime, self.purchases] 

## stage ############################################################# 

class Marketplace(Simulation):
  def __init__(self, name, instances, consumers, rdepth=2, maxtime=100000000):
    Simulation.__init__(self)
    self.name = name
    self.instances = instances 
    self.rdepth = rdepth
    self.books = {}
    self.consumer_specs = consumers
    self.consumer_count = len(consumers['work'])
    self.maxtime = maxtime
    self.maxwork =  max(consumers['work'])
    self.consumers = []
    self.income = 0
    self.finished = 0 # jobs completed 
    self.rtime = 0 # unused hours
    self.cache = {}
    empty_book = {'invoked':0,'income':0,'time':0,'rtime':0,'work':0}
    """ populate our record datastruct """
    for inst in instances:
      self.books[inst.name] = empty_book
    
  def start(self):
    self.initialize()
    print self.now(), ':', self.name, 'started',self.consumer_count,'consumers'
    self.spawn_consumers(self.consumer_specs)
    self.simulate(until=self.maxtime)

  def finish(self):
    print self.name,'finished @',self.now()
    #self.results_primary()

  def cache_bucket(self, x, buckets=1000):
    base = int(self.maxwork / buckets)
    return int(base * round(float(x)/ base))

  def spawn_consumers(self, specs):
    """ spawn and activate consumers for simulation """
    for i in range(len(specs['work'])):
      con = Consumer(name="con_%s"%i, work=specs['work'][i], \
          start=specs['start_time'][i], actual=specs['actual'][i], sim=self)
      self.consumers.append(con)
      self.activate(con, con.process(), at=con.start)

  def results_primary(self):
    rtn = {}
    rtn['name'] = self.name
    rtn['consumers'] = self.consumer_count
    rtn['finished'] = self.finished
    rtn['income'] = self.income
    rtn['rtime'] = self.rtime
    rtn['cache'] = len(self.cache)
    return rtn

  def results_inst(self):
    #empty_book = {'invoked':0,'income':0,'time':0,'rtime':0,'work':0}
    return_set = {'name':[],'work':[],'income':[], 'time':[],'rtime':[]}
    for inst in self.instances:
      return_set['name'].append(inst.name)
      return_set['work'].append(self.books[inst.name]['work'])
      return_set['income'].append(self.books[inst.name]['income'])
      return_set['time'].append(self.books[inst.name]['time'])
      return_set['rtime'].append(self.books[inst.name]['rtime'])
    return return_set

  def results_cons(self):
    return_set = {'name':[],'work':[],'cost':[], 'time':[],
        'start':[],'finish':[], 'comp':[], 'rtime':[], 'actual':[]}
    for cons in self.consumers:
      i = cons.results()
      return_set['name'].append(i[0])
      return_set['work'].append(i[1])
      return_set['actual'].append(i[2])
      return_set['comp'].append(i[3])
      return_set['cost'].append(i[4])
      return_set['time'].append(i[5])
      return_set['start'].append(i[6])
      return_set['finish'].append(i[7])
      return_set['rtime'].append(i[8])
      """ for now, lets just print the pruchases"""
      if DEBUG: print "PURCHASES FOR",cons.name,"(",cons.work,",",cons.actual,"):",cons.purchases
    return return_set

# fin.
