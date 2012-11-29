
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
    """ find the resale value of leftover time
        - if we've completed the work and have time remaining on our lease
          we can resell that time in the secondary market. This, however,
          incure additional expensives beyond the income from the resale.
        - We will compute an updated  cost effectiveness with 100% condifence 
          the extra time will sell, and this sale will incure a fixed % fee.
        - We want to price resale to be slightly less expensive than the 
          most cost effective offering from the marketplaces.  
    """
    prev = 0
    for inst in instance_list: 
      data = inst.analyize(work) # get instance report for data
      tmp = data['cpr'] 
      if data['rmdr'] == 0 and data['rtime'] > 0: 
        print "$$$$$$$$$ Remaing Time. Resell? $$$$$$$$$$$$$"
        """ the potentials of our remaining partial instance """
        unit_potential = math.floor(data['rtime'] / inst.unit.time) # no partial unit?
        work_potential = unit_potential * inst.unit.capacity
        cost_potential = unit_potential * inst.unit.cost * inst.lease.puc
        """ competition from the primary marketplace """
        resale1 = Consumer.shop_for_cpr(self, work_potential, instance_list) 
        """ competition from the secondary marketplace """
        #resale2 = self.secondary_cpr(work_potenial)
        """ evaluate time effiency/effectivness of competition 
          - cpr = work / cost / time. 
            aka. work per dollar across duration
          - from our work potential, we find the best cpr from the primary
            market 
          - calculate an adjusted overall cost given the found cpr and our own
            timeline (i.e. what to charge to aquire the same CPR rating)
          - max price (to sell our instance for) is 1 minus the difference
            between the expected costs of our instance and the best price from
            the primary (which may include downpayments)
          - our "income" is this calculated sale cost minus the reseller
            market fee
          - TODO: This assumes a 100% guarentee that the unit will sell in the
            secondary market. 
        """
        # cpr = work/cost/time. cost' = work / 
        rs1_adj_cost = work_potential /  (resale1['cpr'] * data['rtime'])
        resale_max_price = (rs1_adj_cost - cost_potential - 1) 
        resale_income = resale_max_price * (1 - self.sim.resale_fee)
        """ our adjusted CPR including reseller income """
        tmp = data['work'] / (data['cost'] - resale_income) / data['time']
        print "$$$$ updated CPR:",tmp
        print "$$$$ cost-pot, adj-cost", cost_potential, rs1_adj_cost
        print "$$$$ sale price / income", resale_max_price, resale_income
      """ 
      As written, this is expected to flood the secondary market will
      partial sales of the largers instance. Since 1) there is a 100%
      condifence the instance will sell, 2) No adjustment for the current
      status of the market and 3) Noone currently buys from the 2nd market
      """
      if tmp >= prev or prev == 0: # this instance is potentially better
        prev = tmp
        rtn = data
        rtn['inst'] = inst
    #end for
    return rtn
    

  """ purchase resource based on the results of financial analysis """
  def purchase(self, work, instance_list):
    """ shop for the highest cost effectivness """
    rtn = self.shop_for_cpr(work, instance_list)
    print self.name, "PURCHASED: (spent, cpr, rtime)", rtn['inst'].desc, rtn['cost'],rtn['cpr'],rtn['rtime']
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
    # end while
    """ 
      We have leftover allocation we can resell
        - create a new instance type of the product 
    """
    if self.rtime > 0:
      tosell = Instance( name=self.name, desc=self.name, \
          unit = Unit(capacity=float(1.00), time=1, cost=0.1), \
          lease = Lease(length = self.rtime, downp = 100, puc=1)) 

    #TODO: minimul resale
      yield put, self.sim, self.sim.listing,[tosell]
    self.finish = self.sim.now()
    self.sim.finished += 1

  def results(self):
    """ return consumer data list """
    time = self.finish - self.start # total time
    rate = self.work / self.spent # work per dollar
    cpr = rate / time # 
    return [self.name, self.work, self.spent, time,  self.start, self.finish,
        rate, cpr, self.rtime] 

class Marketplace_2DRY(Marketplace):
  def __init__(self, name, instances, consumers, maxtime=100000000, resale_fee=0.12):
    Marketplace.__init__(self, name, instances, consumers, maxtime)
    self.resale_fee = resale_fee
    self.listing = Store(name="reseller list", sim=self, unitName="units",
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
    print ':',[x.name for x in self.listing.theBuffer]
    
# fin.
