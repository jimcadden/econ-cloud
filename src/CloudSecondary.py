""" 
Reseller Marketplace (Store?)
 * Buy
   - check each entry in the database for the best "price effiency" (after
     computing best offer from amz). Including fee
   - on purchase, remove listing from store, pay fee to privider
 # Sell 
   - price efficency should take into account the abililty to resell
   - total cost - resell cost
   - resell cost <= market rate (i.e. already posted)
   - or, "slightly" better "price effiency" that  amazon (i.e., priced at the
     minimum rate of all three amz instance types. Including fee)
""" 

import math
import random
import sys
try:
  from CloudMarketplace import *
except ImportError:
  None

class Instance_2DRY(Instance): 
  def __init__(self, name, desc, unit, lease, oid):
    Instance.__init__(self, name, desc, unit, lease)
    self.oid = oid #orignal instance id

class Consumer_2DRY(Consumer):
  """ a basic consumer motivated by overall cost """
  def __init__(self, name, work, start, actual, sim):
    Consumer.__init__(self, name, work, start, actual, sim)
    self.posted = 0
    self.sold = 0
    self.marked = 0 # what is this used for? 
    self.recent = {} #bookmark of the most-recently purchased instance

  def analyize_resale_value(self, data, inst, instance_list):
    """ evaluate market competition, return a price that undersells the
    current best offer """
    unit_potential = math.floor(data['rtime'] / inst.unit.time) # no partial unit?
    work_potential = unit_potential * inst.unit.capacity
    cost_potential = unit_potential * inst.unit.cost * inst.lease.puc

    """ competition from the primary marketplace """
    resale1 = Consumer.optimal_instance(self, work_potential, instance_list,
        self.sim.rdepth)
    if DEBUG:
      rtn=resale1
      print "#! RESALE:", inst.desc,  unit_potential, work_potential, cost_potential
      print ">>",self.name,"to sell",work_potential," COMPETITION:", rtn['inst'].desc,\
        rtn['cost'],rtn['eff'], rtn['rtime'], rtn['rmdr']

    """ find the best rated offering on the secondary market """
    if self.sim.resale_list.getnrBuffered() > 0 :
      if DEBUG:
        print "#@! Scanning secondary offerings "
      resale2 = Consumer.optimal_instance(self, work_potential, 
        self.sim.resale_list.theBuffer)
      if DEBUG: 
        print "#@! Finished  secondary offerings "
      best_eff =  resale1['eff'] if (resale1['eff']>resale2['eff']) else resale2['eff']
    else:
      best_eff = resale1['eff']

    """ calculate eff of resale amount, and updated effiency """
    rs1_adj_cost = work_potential /  (best_eff * data['rtime'])
    resale_max_price = rs1_adj_cost - cost_potential - 1 

    # I donno about this... 
    if resale_max_price < 0:
      resale_max_price = 1  

    resale_income = resale_max_price * (1 - self.sim.resale_fee)
    """ our adjusted eff includes reseller income """
    eff = data['work'] / (data['cost'] - resale_income) / data['time']
    if DEBUG:
      print "$$$$ cost-pot, adj-cost", cost_potential, rs1_adj_cost
      print "$$$$ sale price / income", resale_max_price, resale_income

    return {'price':resale_max_price, 'eff':eff}

  def optimal_instance(self, work, instance_list, rdepth=0, prvwork=0, prvcost=0,
      prvtime=0, depth=0):

    if work <= 0:
      if DEBUG: print "THIS SHOULkDNT HAPPED! OHNNO!"
      try: prvwork / prvcost / prvtime
      except ZeroDivisionError:
        sys.exit(0)
    """
    Recusive analysis scan of available isntances
    """
    max_eff = inst = 0
    for i in instance_list:
      #if DEBUG: print "| loop:,", prvwork
      data = i.analyize(work) 
      if depth < rdepth: # restiction of recusive depth
        if data['rmdr'] > 0:
          if DEBUG: print "++ depth",depth,", rmdr",data['rmdr'],"++"
          """ check the hash for best data """
          try:
            data = self.sim.cache[data['work']*self.sim.cache_bucket(work)]
            if DEBUG: 
              print "@ cache hit:", self.sim.cache_bucket(work), "round",data['work']
          except KeyError:
            if DEBUG: print "@ cache miss:",self.sim.cache_bucket(work),"round",data['work']
            data = self.optimal_instance(data['rmdr'], instance_list, rdepth, data['work']+prvwork,
                data['cost']+prvcost, data['time']+prvtime, depth+1)
            """ check the hash for best data """
            self.sim.cache[data['work']*self.sim.cache_bucket(work)] = data

      # this maybe fucked when we're pulling rtime /inst data from cache.. (?)
      # if we're out of work and have left over time.. lets see what is worth!"
      if data['rmdr'] == 0 and data['rtime'] > 0: 
        resale = self.analyize_resale_value(data, i, instance_list)
        if resale['eff'] > data['eff']:
          #resale eff is a combined eff?
          data['eff'] = resale['eff']

      if data['eff'] >= max_eff:
        if DEBUG: "d:",depth,"max eff updated:",i.desc, data['eff']
        """ if we've found a path with a better efficiency """
        max_eff = data['eff']
        best_inst  = i

    """ get a fresh results """ 
    rtn = best_inst.analyize(work)
    rtn['inst'] = best_inst
    return rtn

  def purchase(self, work, instance_list):
    """ Aquire resource based on effiency analysis 
      Process:
        1. Get a bid from the primary market
          1.1 Consider the resale value of instance
        2. If a secondary market had offeres, get a bid
          - TODO: no resale consideration
        3. Compare offers, buy the best one

      FIXME: returns primary only
    """
    self.marked = 0 # clear resale marker

    """ optimal primary market instance (considers resale value) """
    rtn = self.optimal_instance(work, instance_list, self.sim.rdepth)

    """ consider a purchase from secondary market """
    if self.sim.resale_list.nrBuffered > 0 :
      secondary = Consumer.optimal_instance(self, work,
          self.sim.resale_list.theBuffer, 0)
     # # FIXME: strategy does not buy secondary w/ intent to resell, but should
      if secondary['eff'] > rtn['eff']:
        """ purchase from secondary """ 
        print "THIS LINE WILL NT PRINT", secondary['inst'].results()
        rtn = secondary
        self.marked = secondary['inst'].name

    if DEBUG:
      print ">>",self.name,"todo",work,"PURCHASED:", rtn['inst'].name, rtn['inst'].desc,\
        rtn['cost'],rtn['eff'], rtn['rtime'], rtn['rmdr']
    self.recent = rtn
    self.purchases.append(rtn['inst'].name)
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
      if self.marked != 0:
        self.bookkeeping(data)
        print "pulling from store??:"
        yield get, self, self.sim.resale_list, self.sim.pulllisting  
        print self.got, "%%%"
        yield hold, self, data['time']
      else:
        Consumer.bookkeeping(self, data) #record puchase details
        yield hold, self, data['time']
    #end while
    if data['rtime'] > 0: #global remaining time
      self.sim.rtime += data['rtime']

    """ secondary """
    """ We have leftover allocation we can resell """
    if data['rtime'] >= data['inst'].unit.capacity * data['inst'].unit.time:
      if DEBUG:
        print "We have leftovers to sell", data['rtime'], data['inst'].desc
      inst = data['inst']
      resell = self.analyize_resale_value( data, inst, self.sim.instances)
      tosell = Instance_2DRY( oid=inst.name, name=self.name, desc=inst.desc,  \
          unit = inst.unit, \
          lease = Lease(length = self.rtime, downp = resell['price'] , puc=inst.lease.puc)) 
      """ place listing into resale store (SimPY)"""
      yield put, self, self.sim.resale_list,[tosell]
    self.finished()

  def finished(self):
    self.finish = self.sim.now()
    self.sim.finished += 1
  
  def bookkeeping(self, data):
    """ this is an update for a secondary market purchase """
    rtn = data
    """ consumer data """
    self.rmdr = rtn['rmdr']
    self.spent += rtn['cost']
    self.comp += rtn['work']
    self.rtime = rtn['rtime']
    #TODO signal / pay waiting process (also, cause processes to wait)
    """ market data """
    self.sim.income_2dry += rtn['inst'].lease.downp * self.sim.resale_fee 
    self.sim.income += rtn['cost'] - rtn['inst'].lease.downp
    """ instance data """
    #TODO a way to lookup the instance record for this resold inst
    self.sim.books[rtn['inst'].oid]['resold'] += 1
    self.sim.books[rtn['inst'].oid]['income'] += rtn['cost'] - \
      rtn['inst'].lease.downp
    self.sim.books[rtn['inst'].oid]['work'] += rtn['work']
    self.sim.books[rtn['inst'].oid]['time'] += rtn['time']
    self.sim.books[rtn['inst'].oid]['rtime'] += rtn['rtime']

  def results(self):
    """ return consumer data list """
    time = self.finish - self.start # total time
    return [self.name, self.work, self.actual, self.comp, self.spent, 
        time, self.start, self.finish, self.rtime, self.purchases] 


class Marketplace_2DRY(Marketplace):
  """ Secondary Marketplace """
  def __init__(self, name, instances, consumers, rdepth=2, maxtime=100000000,
      resale_fee=0.12):
    Marketplace.__init__(self, name, instances, consumers, rdepth, maxtime)
    """ secondary market objects """
    self.resale_list = Store(name="reseller list", sim=self, unitName="units",
        monitored=False) # store of available resale instances
    self.resale_fee = resale_fee
    self.income_2dry = 0
    """ extend records for secondary data """
    for inst in instances:
      self.books[inst.name]['resell'] = 0 # attempt
      self.books[inst.name]['resold'] = 0 # achieved

  def pulllisting(self, buff):
    """ query the secondary listing for an id """
    """ search function for simulation store """
    print "!!!!!!!!!!!!!!!!!!!"
    result = []
    for i in buff:
      if i.name:
        result.append(i)
    return result 

  def spawn_consumers(self, specs):
    """ spawn and activate consumers for simulation """
    for i in range(len(specs['work'])):
      con = Consumer_2DRY(name="con_%s"%i, work=specs['work'][i], \
          start=specs['start_time'][i], actual=specs['actual'][i], sim=self)
      self.consumers.append(con)
      self.activate(con, con.process(), at=con.start)

  def results_secondary(self):
    # THIS SUCKS -> return dict
    print "Secondary Market Stats:"
    print "# of entries:", self.resale_list.nrBuffered
    print ':',[x.name for x in self.resale_list.theBuffer]
    
  def finish(self):
    print self.name,'finished @',self.now()
    self.results_secondary()
# fin.
