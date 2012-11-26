
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

class Consumer_2DRY(Consumer):
  """ a basic consumer motivated by overall cost """
  def __init__(self, name, work, start, sim):
    Consumer.__init__(self, name, work, start, sim)
    self.posted = 0
    self.sold = 0

  """ return the best rate w/ assured resale """
  def shop_for_cpr(self, work, instance_list):
    prev = 0
    for inst in instance_list: 
      data = inst.analyize(work) # get instance report for data
      tmp = data['cpr'] 
      """ find the resale value of leftover time
          - if we've completed the work and have time remaining on our lease
            we can resell that time in the secondary market. This, however,
            incure additional expensives beyond the income from the resale.
          - We will compute an updated  cost effectiveness with 100% condifence 
            the extra time will sell, and this sale will incure a fixed % fee.
          - We want to price resale to be slightly less expensive than the 
            most cost effective offering from the marketplaces.  
      """
      if data['rmdr'] == 0 and data['rtime'] > 0: 
        print "Considering a resale..."
        """ the potentials of our remaining partial instance """
        work_potential = math.floor(rtime / inst.unit.time) * inst.unit.capacity
        unit_potential = math.ceil(work_potential / inst.unit.capacity)
        cost_potential = unit_potential * (inst.unit.cost * inst.lease.puc)
        """ competition from the primary marketplace """
        resale1 = Consumer.shop_for_cpr(work_potential, instance_list) 
        """ competition from the secondary marketplace """
        #resale2 = self.secondary_cpr(work_potenial)
        #experimental cpr finder
        rs1_adj_cost = work_potential /  (resale1['cpr'] * data['rtime'])
        resale_price = (rs1_adj_cost - cost_potential - 1) 
        resale_income = resale_price * (1 - self.sim.resale_fee)
        #experimential cpr converter
        tmp = data['work'] / (data['cost'] - resale_income) / data['time']

      if tmp >= prev or prev == 0: # this instance is potentially better
        prev = tmp
        rtn = data
        rtn['inst'] = inst
    return rtn
    

  """ purchase resource based on the results of financial analysis """
  def purchase(self, work, instance_list):
    """ shop for the highest cost effectivness """
    rtn = self.shop_for_cpr(work, instance_list)
    #print "PURCHASED:", rtn['inst'].desc, rtn['cost'],rtn['cpr']
    """ update simulation statistics """
    self.sim.income += rtn['cost']
    rtn['inst'].invoked += 1
    rtn['inst'].income += rtn['cost']
    rtn['inst'].work +=   rtn['work']
    rtn['inst'].time +=   rtn['time']
    rtn['inst'].unused += rtn['rtime']
    self.spent += rtn['cost']
    self.rtime += rtn['rtime']
    self.rmdr = rtn['rmdr']
    return rtn

  """ process work by purchasing instances """
  def process(self):
    while self.rmdr > 0:
      data = self.purchase(self.rmdr, self.sim.instances)
      yield hold, self, data['time']
    self.finish = self.sim.now()

  def results(self):
    """ return consumer data list """
    time = self.finish - self.start # total time
    rate = self.work / self.spent # work per dollar
    cpr = rate / time # 
    return [self.name, self.work, self.spent, time,  self.start, self.finish,
        rate, cpr, self.rtime] 

  """ check the economic landscape and decide instance to purchase. """
  """ 
  - we computer the cost effectiveness of a node, but we do not yet account
    for the resell value (of extra / leftover time)
    With the cost effectiveness, also return the total cost and unused time.
    With this... 
      - get the effectivness of the remaining time
      - get what the provider would charge the remaining time (& effectiveness!)
      - best option: minimised cost while maximises effective ness. 
  """


class Marketplace_2DRY(Marketplace):
  def __init__(self, name, instances, consumer_count, maxwork, maxtime):
    Marketplace.__init__(self, name, instances, consumer_count, maxwork, maxtime)
    self.resalefee = 0.12
    self.listing = Store(name="reseller list", unitName="units",
        monitored=True)

  def spawn_consumers(self):
    """ spawn and activate consumers for simulation """
    for i in range(self.consumer_count):
      con = Consumer_2DRY(name="con_%s"%i, work=self.generate_work(), \
          start=self.generate_start(), sim=self)
      self.consumers.append(con)
      self.activate(con, con.process(), at=con.start)

# fin.
