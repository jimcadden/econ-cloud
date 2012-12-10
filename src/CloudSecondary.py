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

gbuy = "def"

def pulllisting(buff):
  """ query the secondary listing for an id """
  global gbuy
  result = []
  for i in buff:
    if i.name == gbuy:
      result.append(i)
  return result 

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
      rtn=resale1 # this is for the print (lazy)
      print "#! RESALE:", inst.desc,  unit_potential, work_potential, cost_potential
      print ">>",self.name,"to sell",work_potential," COMPETITION:", rtn['inst'].desc,\
        rtn['cost'],rtn['eff'], rtn['rtime'], rtn['rmdr']

    """ find the best rated offering on the secondary market """
    if self.sim.resale_list.getnrBuffered() > 0 and self.sim.price2sell :
      resale2 = Consumer.optimal_instance(self, work_potential, 
        self.sim.resale_list.theBuffer)
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
          if(self.sim.cacheOn):  
            try:
              data = self.sim.cache[data['work']*self.sim.cache_bucket(work)]
              if DEBUG: 
                print "@ cache hit:", self.sim.cache_bucket(work), "round",data['work']
            except KeyError:
              if DEBUG: print "@ cache miss:",self.sim.cache_bucket(work),"round",data['work']
              data = self.optimal_instance(data['rmdr'], instance_list,\
                  rdepth, data['work']+prvwork,\
                data['cost']+prvcost, data['time']+prvtime, depth+1)
              """ check the hash for best data """
              self.sim.cache[data['work']*self.sim.cache_bucket(work)] = data
          else:
            data = self.optimal_instance(data['rmdr'], instance_list, rdepth, data['work']+prvwork,
              data['cost']+prvcost, data['time']+prvtime, depth+1)


      # this maybe fucked when we're pulling rtime /inst data from cache.. (?)
      # if we're out of work and have left over time.. lets see what is worth!"
      if data['rmdr'] == 0 and data['rtime'] > 0 and self.sim.buy2sell: 
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
    rtn = best_inst.analyize(work, prvwork,prvtime,prvcost)
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
    global gbuy
    gbuy = "clr" # clear resale marker FIXME:!
    self.marked = 0

    """ optimal primary market instance (considers resale value) """
    rtn = self.optimal_instance(work, instance_list, self.sim.rdepth)

    """ consider a purchase from secondary market """
    if self.sim.resale_list.nrBuffered > 0 :
      secondary = Consumer.optimal_instance(self, work,
          self.sim.resale_list.theBuffer, 0)
     # # FIXME: strategy does not buy secondary w/ intent to resell, but should
      if secondary['eff'] > rtn['eff']:
        """ purchase from secondary """ 
        if DEBUG:
          print "Secondary Pruchase:", secondary['inst'].results()
        rtn = secondary
        gbuy = secondary['inst'].name
        self.marked = 1

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
        yield get, self, self.sim.resale_list,pulllisting  
        #yield get, self, self.sim.resale_list, 1
        data['inst'] = self.got.pop()
        data['inst'].name = data['inst'].oid
        self.sim.sold += 1
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
      self.sim.books[inst.name]['resell'] += 1
      self.sim.listed += 1
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

#  def results(self):
#    """ return consumer data list """
#    time = self.finish - self.start # total time
#    return [self.name, self.work, self.actual, self.comp, self.spent, 
#        time, self.start, self.finish, self.rtime, self.purchases] 


class Marketplace_2DRY(Marketplace):
  """ Secondary Marketplace """
  def __init__(self, name, instances, consumers, rdepth=2, maxtime=100000000,
      resale_fee=0.12, cacheOn=False, buy2sell=False, price2sell=True):
    Marketplace.__init__(self, name, instances, consumers, rdepth, maxtime,
        cacheOn)
    """ secondary market objects """
    self.resale_list = Store(name="reseller list", sim=self, unitName="units",
        monitored=True) # store of available resale instances
    self.resale_fee = resale_fee
    self.income_2dry = 0
    self.listed = 0
    self.sold = 0
    self.buy2sell = buy2sell
    self.price2sell = price2sell
    """ extend records for secondary data """
    for inst in instances:
      self.books[inst.name]['resell'] = 0 # attempt
      self.books[inst.name]['resold'] = 0 # achieved

  def spawn_consumers(self, specs):
    """ spawn and activate consumers for simulation """
    for i in range(len(specs['work'])):
      con = Consumer_2DRY(name="con_%s"%i, work=specs['work'][i], \
          start=specs['start_time'][i], actual=specs['actual'][i], sim=self)
      self.consumers.append(con)
      self.activate(con, con.process(), at=con.start)

  def results_mrkt(self):
    rtn = Marketplace.results_mrkt(self)
    #print "put queue", len(self.resale_list.putQ)
    #print "get queue", len(self.resale_list.getQ)
    #print 'Buff:',[x.name for x in self.resale_list.theBuffer]
    #print "GB", gbuy
    rtn['listed'] =  self.listed
    rtn['sold'] =  self.sold  
    rtn['unsold'] =  self.resale_list.nrBuffered
    rtn['resale_fee'] = self.resale_fee
    rtn['income_2dry'] = self.income_2dry
    return rtn
    
  def results_inst(self):
    #return_set = {'name':[],'work':[],'income':[], 'time':[],'rtime':[]}
    return_set = Marketplace.results_inst(self)
    return_set['resell'] = []
    return_set['resold'] = []
    for inst in self.instances:
      return_set['resell'].append(self.books[inst.name]['resell'])
      return_set['resold'].append(self.books[inst.name]['resold'])
    return return_set

  def finish(self):
    print self.name,'finished @',self.now()
# fin.
