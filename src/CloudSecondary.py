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
try:
  from CloudMarketplace import *
except ImportError:
  None

class Consumer_2DRY(Consumer, Process):
  """ a basic consumer motivated by overall cost """
  def __init__(self, name, work, start, actual, sim):
    Consumer.__init__(self, name, work, start, actual, sim)
    self.posted = 0
    self.sold = 0
    self.marked = 0 # what is this used for? 
    self.recent = {} #and this?

  def analyize_resale_value(self, data, inst, instance_list):
    """ evaluate market competition, return a price that undersells the
    current best offer """
    """ find the best rated offering on the secondary market """
    unit_potential = math.floor(data['rtime'] / inst.unit.time) # no partial unit?
    work_potential = unit_potential * inst.unit.capacity
    cost_potential = unit_potential * inst.unit.cost * inst.lease.puc
    """ competition from the primary marketplace """
    resale1 = Consumer.optimal_instance(self, work_potential, instance_list)
    """ competition from the secondary marketplace """
    if self.sim.resale_list.nrBuffered > 0 :
      resale2 = Consumer.optimal_instance(self, work_potential, 
        self.sim.resale_list.theBuffer)
    """ calculate eff of resale amount, and updated effiency """
    rs1_adj_cost = work_potential /  (resale1['eff'] * data['rtime'])
    resale_max_price = (rs1_adj_cost - cost_potential - 1) 
    resale_income = resale_max_price * (1 - self.sim.resale_fee)
    """ our adjusted eff includes reseller income """
    eff = data['work'] / (data['cost'] - resale_income) / data['time']
    #print "$$$$ updated CPR:",tmp
    #print "$$$$ cost-pot, adj-cost", cost_potential, rs1_adj_cost
    #print "$$$$ sale price / income", resale_max_price, resale_income
    return {'price':resale_max_price, 'eff':eff}

  def optimal_instance(self, work, instance_list, rdepth=0, prvwork=0, prvcost=0,
      prvtime=0, depth=1):

    if work <= 0:
      if DEBUG: print "shit this happened!@!"
      return prvwork / prvcost / prvtime

    max_eff = 0
    inst = 0
    for i in instance_list:
      if DEBUG: print "| loop:,", prvwork
      data = i.analyize(work) 
      if depth < rdepth:
        if data['rmdr'] > 0:
          if DEBUG: print "++ depth",depth,", rmdr",data['rmdr'],"++"
          """ check the hash for best data """
          try:
            data = self.sim.cache[data['work']*self.sim.cache_bucket(work)]
            if DEBUG: print "@ cache hit:", self.sim.cache_bucket(work),"round",data['work']
          except keyerror:
            if DEBUG: print "@ cache miss:",self.sim.cache_bucket(work),"round",data['work']
            data = self.optimal_instance(data['rmdr'], instance_list, data['work']+prvwork,
                data['cost']+prvcost, data['time']+prvtime, depth+1)
            """ check the hash for best data """
            self.sim.cache[data['work']*self.sim.cache_bucket(work)] = data

      # this maybe fucked when we're pulling rtime /inst data from cache.. (?)
      #" if we're out of work and have left over time.. lets sell it!"
      #if data['rmdr'] == 0 and data['rtime'] > 0: 
      #  resale = self.analyize_resale_value(data, data['inst'], instance_list)
      #  if resale['eff'] > data['eff']:
      #    #resale eff is a combined eff?
      #    data['eff'] = resale['eff']

      if data['eff'] >= max_eff:
        if DEBUG: "d:",depth,"max eff updated:",i.desc, data['eff']
        """ if we've found a path with a better efficiency """
        max_eff = data['eff']
        best_inst  = i

    """ get a fresh results """ 
    rtn = best_inst.analyize(work)
    rtn['inst'] = best_inst
    return rtn

  def pull_listing(self, instance_list):
    """ query the secondary listing for an id """
    result = []
    for inst in instance_list:
        if inst.name == self.marked:
          result.append(inst)
    return result

# we need to somehow 'mark' that data was purchase from the 2ndard
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

  def purchase(self, work, instance_list):
    """ purchase resource based on effiency analysis """
    self.marked = 0 # clear resale marker
    primary = self.optimal_instance(work, instance_list)
    if self.sim.resale_list.nrBuffered > 0 :
      secondary = Consumer.optimal_instance(self, work, 
          self.sim.resale_list.theBuffer, rdepth=0)
      # FIXME: strategy does not buy secondary w/ intent to resell, but should
      if secondary['eff'] > primary['eff']:
        """ purchase from secondary """ 
        print "THIS SHOULDNT HAPPEN SHIT SHIT SHIT!~"
        #yield get, self, self.sim.resale_list, self.pull_listing  
        #self.recent = secondary
        #self.recent['inst'] = self.got
        """ secondary market stats """
        self.sim.resale_total += self.recent['lease'].downp
      
    """ primary market stats """
    #Consumer.bookkeeping(self, primary) 
    self.recent = primary['inst']
    return primary

  def finished(self):
    self.finish = self.sim.now()
    self.sim.finished += 1
    """ process work by purchasing instances """
    """ We have leftover allocation we can resell """
    # FIXME: lets set a minimum allowed to resell
    if self.rtime > 0:
      print "We have leftovers to sell", self.rtime
      #yield put, self.sim, self.sim.resale_list,[tosell]
      #data = self.got
      #inst = data['inst']
      #resell = self.analyize_resale_value( data, inst, instance_list)
      #tosell = Instance( name=self.name, desc=inst.desc,  \
      #    unit = inst.unit, \
      #    lease = Lease(length = self.rtime, downp = resell['price'] , puc=inst.lease.puc)) 
      #""" place listing into resale store (SimPY)"""

  def results(self):
    """ return consumer data list """
    time = self.finish - self.start # total time
    return [self.name, self.work, self.actual, self.comp, self.spent, 
        time, self.start, self.finish, self.rtime, self.purchases] 

class Marketplace_2DRY(Marketplace):
  def __init__(self, name, instances, consumers, rdepth=2, maxtime=100000000,
      resale_fee=0.12):
    Marketplace.__init__(self, name, instances, consumers, rdepth, maxtime)
    """ secondary market objects """
    self.resale_fee = resale_fee
    self.resale_list = Store(name="reseller list", sim=self, unitName="units",
        monitored=True)
    """ extend our records """
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

  def results_secondary(self):
    # THIS SUCKS -> return dict
    print "Secondary Market Stats"
    print ':',[x.name for x in self.resale_list.theBuffer]
    
# fin.
