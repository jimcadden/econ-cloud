
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

  def shop(self, work):

    """ this iterates all instances offered by the prider and selects the one
    which is the most cost effective (cost / work / time ) """
    prev = 0
    for inst in self.sim.instances:
      #print "checking instance:", inst.name
      data = inst.analyize(work)
      tmp = data['cpr'] 
      #print "w", work,"[", inst.name,"-", inst.desc, "]:", tmp, "|$", data['cost'], \
      #  "cost, ", data['time'], "time"
      if tmp >= prev or prev == 0:
        prev = tmp
        rtn = data
        rtn['inst'] = inst
    # mark this instance as "invoked"
    rtn['inst'].invoked += 1
   # print "======================================"
   # print rtn['inst'].results()
   # print "======================================"
    return rtn

  """ purchase resource based on the results of financial analysis """
  def purchase(self):
    while self.rmdr > 0:
      data = self.shop(self.rmdr)

      self.spent += data['cost']
      self.rmdr = data['rmdr']
      yield hold, self, data['time'] #
    self.finish = self.sim.now()


class Marketplace_2DRY(Marketplace):
  def __init__(self, name, instances, consumer_count, maxwork, maxtime):
    Marketplace.__init__(self, name, instances, consumer_count, maxwork, maxtime)
    self.listing = Store(name="reseller list", unitName="units",
        monitored=True)

  def spawn_consumers(self):
    """ spawn and activate consumers for simulation """
    for i in range(self.consumer_count):
      con = Consumer_2DRY(name="con_%s"%i, work=self.generate_work(), \
          start=self.generate_start(), sim=self)
      self.consumers.append(con)
      self.activate(con, con.purchase(), at=con.start)

# fin.
