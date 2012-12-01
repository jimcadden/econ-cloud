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
from SimPy.Simulation import *

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

  def analyize(self, work):
    """
    we are given a requested amount of work.  For this instance, return the work 
    completed, work remaining, total cost and efficiency rating
    """
    # partial units consumed are billed as a full unit 
    req_units = math.ceil(work / self.unit.capacity) # requested units
    max_units = math.floor(self.lease.length / self.unit.time)  
    rmdr = 0 # remaning work
    rtime = 0 # remaining time on lease
    """ on-demand leases have a zero length """
    if (self.lease.length > 0):
      """ a fixed lease can processes limited number of units"""
      if (req_units > max_units): #we need more work than lease allows
        req_units = max_units
        rmdr = work - (max_units * self.unit.capacity)
        work = max_units * self.unit.capacity
      # endif
      rtime = self.lease.length - (req_units * self.unit.time)
    #endif
    cost =  self.lease.downp + (req_units * (self.unit.cost * self.lease.puc))
    time = req_units * self.unit.time
    rate = work / cost
    eff = work / cost / time # instance efficency 
    print "|", self.desc,":", cost, eff, rtime
    return {'cost': cost, 'time': time, 'work':work, 'rmdr': rmdr,
        'rate':rate, 'eff':eff, 'rtime':rtime}
  
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
    self.finish = 0
    self.comp = 0 # completed work
    self.rtime = 0 # remaing time
    self.spent = 0 # money spent

  def optimal_instance(self, work, instance_list):
    """ search list for best cost efficiency, i.e, most work per dollar  """
    rtn = 0
    peff = 0
    for inst in instance_list: 
      data = inst.analyize(work) # get instance report for data
      teff = data['eff'] 
      if teff >= peff or peff == 0:
        peff = teff
        rtn = data
        rtn['inst'] = inst
    return rtn

  def purchase(self, work, instance_list):
    """ shop for efficiency """
    rtn = self.optimal_instance(work, instance_list)
    print ">",self.name,"todo",work,"PURCHASED:", rtn['inst'].desc,\
    rtn['cost'],rtn['eff'], rtn['rtime'], rtn['rmdr']
    return rtn

  def process(self):
    """ process work by purchasing instances """
    if self.actual <= 0: # just incase
      self.comp = -1

    print ">>>", self.name,":",self.work," actual:",self.actual

    while self.actual != self.comp:
      exp_rem = self.work - self.comp
      act_rem = self.actual - self.comp
      """ when completed work > expected work 
        We treat actual work as our new 'high' expectation """
      if self.comp >= self.work:
        exp_rem = act_rem
      """ make purchase of instance """
      data = self.purchase(exp_rem, self.sim.instances)
      """ unexpected end to job """
      if data['work'] > act_rem: 
        instance = data['inst']
        data = instance.analyize(act_rem)
        data['inst'] = instance
      self.bookkeeping(data)
      yield hold, self, data['time']
      #end while
    self.finish = self.sim.now()

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

  def results(self):
    """ return consumer data list """
    time = self.finish - self.start # total time
    return [self.name, self.work, self.actual, self.comp, self.spent, time, self.start, self.finish,
        self.rtime] 


## stage ############################################################# 

class Marketplace(Simulation):
  def __init__(self, name, instances, consumers, maxtime=100000000):
    Simulation.__init__(self)
    self.name = name
    self.instances = instances 
    self.books = {}
    self.consumer_specs = consumers
    self.consumer_count = len(consumers['work'])
    self.maxtime = maxtime
    self.consumers = []
    self.income = 0
    self.finished = 0 # jobs completed 
    """ populate our record books """
    empty_book = {'invoked':0,'income':0,'time':0,'rtime':0,'work':0}
    for inst in instances:
      self.books[inst.name] = empty_book
    
 # def ondemand_instance(self, instance_list):
 #   result = []
 #   for i in instance_list:
 #     if i.lease.downp == 0
 #       result.append(i)
 #   return result
  
  def spawn_consumers(self, specs):
    """ spawn and activate consumers for simulation """
    for i in range(len(specs['work'])):
      con = Consumer(name="con_%s"%i, work=specs['work'][i], \
          start=specs['start_time'][i], actual=specs['actual'][i], sim=self)
      self.consumers.append(con)
      self.activate(con, con.process(), at=con.start)

  def results_primary(self):
    print "Primary Market Stats"

  def results_inst(self):
    return_list = []
    for inst in self.instances:
      return_list.append(inst.results())
    return return_list

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
    return return_set

  def start(self):
    self.initialize()
    print self.now(), ':', self.name, 'started',self.consumer_count,'consumers'
    self.spawn_consumers(self.consumer_specs)
    self.simulate(until=self.maxtime)

  def finish(self):
    print self.now(), ':', self.name, 'finished.'

# fin.
