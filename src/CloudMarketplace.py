
""" This is a basic simulation of consumer-producer market model using the
SimPY library. """

'''
TODO:
 * consider a consumer motivated by time 
   * this requires the incorporation of a consumer deadline and different
   * unit (i.e. more power/time) at variable prices
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

'''
import math
import random
import csv, codecs, cStringIO
from SimPy.Simulation import *
from CSVUtility import *
  
## experimental data  ################################################ 

class CSVExport:
    """
    A CSV writer which will write rows to CSV file "f",
    """
    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        # Redirect output to a queue
        self.writer = csv.writer(open(f,'wb'), dialect=dialect, **kwds)

    def writerow(self, row):
        self.writer.writerow([s for s in row])

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)


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

  def analyize(self, work):
    """ we are given a requested amount of work. 
        Return the work completed, work remaining, total cost and efficency 
        for this instance 
    """
    # partial units consumed are billed as a full unit 
    req_units = math.ceil(work / self.unit.capacity) # requested units
    max_units = math.floor(self.lease.length / self.unit.time)  
    rmdr = 0
    # a fixed lease can only limited number of units
    if req_units > max_units and max_units != 0:
      req_units = max_units
      rmdr = work - (max_units * self.unit.capacity)
      work = max_units * self.unit.capacity
    cost =  self.lease.downp + req_units * self.unit.cost * self.lease.puc
    time = req_units * self.unit.time
    rate = work / time # work rate
    cpr = rate / cost # cost efficency 
    #print self.name, " analysis:", cost, req_units, rmdr, time
    return {'cost': cost, 'time': time, 'work':work, 'rmdr': rmdr,
        'rate':rate, 'cpr':cpr}
  
  def results(self):
    """ list the data for instance """
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

  def shop(self, work):
    """ check the economic landscape and decide product to purchase. """
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

  def purchase(self):
    """ purchase resource based on the results of financial analysis """
    while self.rmdr > 0:
      data = self.shop(self.rmdr)
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


######################################################################### 
#  Start the show!  ##################################################### 
######################################################################### 

### UTILITY

class CSVImport:
    """
    Read in market configuration data from a CSV file
    """
    def __init__(self, filename):
        self.fd = open(filename, 'rb')
        self.data = csv.DictReader(self.fd)

    def __iter__(self):
       return self

    def instances(self):
      ilist = []
      count = 0
      # build three instances for each node type: on-demand, 1yr, 3yr
      for row in self.data:
        desc =  row['Level']+row['Utilization']+row['Instance Type']
        puc1YR = float(row['Rate 1YR']) / float(row['Rate On-demand'])
        puc3YR = float(row['Rate 3YR']) / float(row['Rate On-demand'])
        
        #TODO: year/time as a constant
        lod = Lease(length = 0, downp = 0, puc = 1)
        l1Y = Lease(length = 8760, downp = float(row['Upfront 1YR']), puc = puc1YR) 
        l3Y = Lease(length = 26280, downp = float(row['Upfront 3YR']), puc = puc3YR) 
        nunit = Unit(capacity = float(row['Compute Units']), time = 1, \
            cost = float(row['Rate On-demand']))

        ilist.append( Instance( name=count, desc=desc+" OD", unit=nunit, 
          lease = lod))
        count += 1
        ilist.append( Instance( name=count, desc=desc+" 1Y", unit=nunit,
          lease = l1Y))
        count += 1
        ilist.append( Instance( name=count, desc=desc+" 3Y", unit=nunit,
          lease = l3Y))
        count += 1
      return ilist

    def dump(self):
      for i in self.data:
        print i
# fin.
