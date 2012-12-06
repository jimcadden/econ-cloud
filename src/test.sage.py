from sage.all import *
import numpy as np
import matplotlib.mlab as mlab
import matplotlib.pyplot as plt

import csv, codecs, cStringIO
from CSVUtility import *
from CloudMarketplace import *
from CloudSecondary import *

ec2_full = CSVImport('/home/jmcadden/workspace/econ-cloud/src/ec2rates-useast_11-09-12.csv')
ec2_nopar = CSVImport('/home/jmcadden/workspace/econ-cloud/src/ec2rates-useast_11-09-12_nopar.csv')
ec2_std = CSVImport('/home/jmcadden/workspace/econ-cloud/src/ec2rates-useast_11-09-12_standard.csv')

############################################

MAXWORK = 100000
MAXTIME = 100000000
CONS = 10000
RDEPTH = 0 # recursion depth

############################################

# Instances    
def instances(data):
  ilist = []
  count = 0
  # build three instances for each node type: on-demand, 1yr, 3yr
  for row in data:
    desc =  row['Level']+row['Utilization']+row['Instance Type']
    puc1YR =  float(row['Rate 1YR']) / float(row['Rate On-demand'])
    puc3YR = float(row['Rate 3YR']) / float(row['Rate On-demand'])
    lod = Lease(length = 0, downp = 0, puc = 1)
    l1Y = Lease(length = 8760, downp = float(row['Upfront 1YR']), puc = puc1YR) 
    l3Y = Lease(length = 26280, downp = float(row['Upfront 3YR']), puc = puc3YR) 
    nunit = Unit(capacity = float(row['Compute Units']), time = 1, 
        cost = float(row['Rate On-demand']))
    ilist.append( Instance( name=count, desc=desc+" OD", unit=nunit, lease = lod))
    count += 1
    ilist.append( Instance( name=count, desc=desc+" 1Y", unit=nunit, lease = l1Y))
    count += 1
    ilist.append( Instance( name=count, desc=desc+" 3Y", unit=nunit, lease = l3Y))
    count += 1
  return ilist
  
# Consumers
# X = work-distribution, Y = start time, Z = confidence
def loadconsumers(group, count=10, X=RealDistribution('uniform',[0,1]), 
    Z=RealDistribution('uniform',[0,1]), Y=RealDistribution('gaussian',0.275)):
  wtmp = []
  time = []
  actu = []
  # populate distribution list
  for i in range(count):
    wtmp.append(X.get_random_element())
    actu.append(Y.get_random_element()+1)
    time.append(Z.get_random_element())
    
  # normalize distribution & apply values
  wmax = max(wtmp)
  work = [x/(wmax*1.0)*MAXWORK for x in wtmp]
  ttmp = time
  tmax = max(time)
  time = [x/(tmax*1.0)*(MAXTIME - MAXWORK) for x in ttmp]
  
  atmp = actu
  count = 0
  for x in atmp:
      if x > 0: #and x <= 1:
          actu[count] = work[count] * actu[count]
      else: 
          actu[count] = 0 # total fail
      count += 1
  return {'group':group,'start_time':time, 'work':work, 'actual':actu}


def ugly_inst_print(insts):
  print "Lever | Instance Size | Utilization | Capacity | Base Rate | Lease Discount (1Y, 3Y) | Downpayment (1Y, 3Y) "
  for row in insts.data:
    print row['Level'], "|" ,row['Instance Type'], "|" , row['Utilization'], "|", row['Compute Units'], "| ", row['Rate On-demand'], "| (" , row['Rate 1YR'], ",", row['Rate 3YR'], ") | (", row['Upfront 1YR'],",",row['Upfront 3YR'], ")"
    

def con_res_print(res):
  print "\n\nCONSULTANT RESULTS"
  print "Work"
  print "Actual / Expected", (mean(res['actual']) /
      mean(res['work'])*100),"%"
  print "Mean (expected)", mean(res['work'])
  print "Median (expected)", median(res['work'])
  print "Mean (actual)", mean(res['actual'])
  print "Median (actual)", median(res['actual'])
  print "Rate (actual)", (mean(res['actual']) / mean(res['time']))
  print "Cost"
  print "Mean", mean(res['cost'])
  print "Median", median(res['cost'])
  print "Time"
  print "Mean", mean(res['time'])
  print "Median", median(res['time'])
  print "Remaing Time", sum(res['rtime'])

def ins_res_print(res):
  None

def sim_res_print(res):
  print "\n MARKEY RESULTRS FOR", res['name']
  print "CONSUMERS"
  print "Started", res['consumers']
  print "Finished",res['finished']
  print "Income", res['income']
  print "Remaing Time", res['rtime']
  print "Cache", res['cache']
  
def sim_print(sim):
  print "##########################"
  sim_res_print(sim['mrkt'])
  ins_res_print(sim['inst'])
  con_res_print(sim['cons'])

  
#bsim_fullconspec = {}
#bsim_fullconspec['work'] = bsim1_conspecs['work'] + bsim2_conspecs['work'] + bsim3_conspecs['work']
#bsim_fullconspec['start_time'] = bsim1_conspecs['start_time'] + bsim2_conspecs['start_time'] + bsim3_conspecs['start_time']
#bsim_fullconspec['actual'] = bsim1_conspecs['actual'] + bsim2_conspecs['actual'] + bsim3_conspecs['actual']

#bsim1 = Marketplace_2DRY( name = "EC2: group 1", instances = ec2_insts, consumers = bsim1_conspecs)
#bsim2 = Marketplace_2DRY( name = "EC2: group 2", instances = ec2_insts, consumers = bsim2_conspecs)
#bsim3 = Marketplace_2DRY( name = "EC2: group 3", instances = ec2_insts, consumers = bsim3_conspecs)

ec2 = []
ec2.append(instances(ec2_full.data))
ec2.append(instances(ec2_nopar.data))
ec2.append(instances(ec2_std.data))

def run_3gsim_p(name="Sim", cdist=0.75, count=CONS, iidx=1, poprate=0.12): 
  conspecs = loadconsumers(group=1, count=CONS,
      X=RealDistribution('lognormal', [0, poprate]))
  sim1 = Marketplace_2DRY( name=name, instances=ec2[iidx], consumers = conspecs,
      rdepth= RDEPTH)
  sim1.start()
  rtn = {}
  rtn['inst'] =  sim1.results_inst()
  rtn['cons'] =  sim1.results_cons()
  rtn['mrkt'] =  sim1.results_primary()
  sim1.finish()
  return rtn 

###########################

sim1 = run_3gsim_p("Group 1", 0.75, 2)
sim_print(sim1)
