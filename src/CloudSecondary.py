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
from CloudMarketplace import *

class Consumer_2DRY(Consumer, Process):
  """ a basic consumer motivated by overall cost """
  def __init__(self, name, work, start, sim):
    Consumer.__init__(self, name, work, start, sim)
    self.posted = 0
    self.sold = 0
    self.marked = 0 # resale purchase marker
    self.recent = {}

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

  def optimal_instance(self, work, instance_list):
    """ return the most effiecent instance for the given work amount"""
    peff = 0
    for inst in instance_list: 
      data = inst.analyize(work) # get instance report for data
      if data['rmdr'] == 0 and data['rtime'] > 0: 
        resale = self.analyize_resale_value(data, inst, instance_list)
        if resale['eff'] > data['eff']:
          data['eff'] = resale['eff']
      """ update our reture instance if null or we found better"""
      if data['eff'] >= peff or peff == 0: 
        peff = data['eff']
        rtn = data
        rtn['inst'] = inst #FIXME: verify this does notmodify buffer 
    #end for
    return rtn
  
  def pull_listing(self, instance_list):
    """ query the secondary listing for an id """
    result = []
    for inst in instance_list:
        if inst.name == self.marked:
          result.append(inst)
    return result

  def bookkeeping_2DRY(self, rtn):
    return 0

  def purchase(self, work, instance_list):
    print "WE HAR HERE!"
    """ purchase resource based on effiency analysis """
    self.marked = 0 # clear resale marker
    primary = self.optimal_instance(work, instance_list)
    secondary = Consumer.optimal_instance(self, work, 
        self.sim.resale_list.theBuffer)
    # FIXME: strategy does not buy secondary to resell, but should
    if secondary['eff'] > primary['eff']:
      """ purchase from secondary """ 
      yield get, self, self.sim.resale_list, self.pull_listing  
      self.recent = secondary
      self.recent['inst'] = self.got
      """ secondary market stats """
      self.sim.resale_total += self.recent['lease'].downp
    else:
      """ primary market stats """
      Consumer.bookkeeping(self, rtn) 
      self.recent = primary['inst']

  def process(self):
    """ process work by purchasing instances """
    while self.rmdr > 0:
      self.purchase(self.rmdr, self.sim.instances)
      yield hold, self, 100 #self.recent['time']
    # end while
    """ We have leftover allocation we can resell """
    # FIXME: lets set a minimum allowed to resell
    if self.rtime > 0:
      data = self.got
      inst = data['inst']
      resell = self.analyize_resale_value( data, inst, instance_list)
      tosell = Instance( name=self.name, desc=inst.desc,  \
          unit = inst.unit, \
          lease = Lease(length = self.rtime, downp = resell['price'] , puc=inst.lease.puc)) 
      """ place listing into resale store (SimPY)"""
      yield put, self.sim, self.sim.resale_list,[tosell]
    self.finish = self.sim.now()
    self.sim.finished += 1

  def results(self):
    """ return consumer data list """
    time = self.finish - self.start # total time
    rate = self.work / self.spent # work per dollar
    eff = rate / time # 
    return [self.name, self.work, self.spent, time,  self.start, self.finish,
        rate, eff, self.rtime] 

class Marketplace_2DRY(Marketplace):
  def __init__(self, name, instances, consumers, maxtime=100000000, resale_fee=0.12):
    Marketplace.__init__(self, name, instances, consumers, maxtime)
    self.resale_fee = resale_fee
    self.resale_list = Store(name="reseller list", sim=self, unitName="units",
        monitored=True)

  def spawn_consumers(self, specs):
    """ spawn and activate consumers for simulation """
    for i in range(len(specs['work'])):
      con = Consumer_2DRY(name="con_%s"%i, work=specs['work'][i], \
          start=specs['start_time'][i], sim=self)
      self.consumers.append(con)
      self.activate(con, con.process(), at=con.start)

  def finish(self):
    print self.now(), ':', self.name, 'finished.'
    self.results_secondary()
    

  def results_secondary(self):
    print "Secondary Market Stats"
    print ':',[x.name for x in self.resale_list.theBuffer]
    
# fin.
