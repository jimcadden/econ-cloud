from sage.all import *
import numpy as np
import matplotlib.mlab as mlab
import matplotlib.pyplot as plt

import csv, codecs, cStringIO
from CSVUtility import *
from CloudMarketplace import *
from CloudSecondary import *

ec2 = CSVImport('/home/jmcadden/workspace/econ-cloud/src/ec2rates-useast_11-09-12.csv')
ec2_nopar = CSVImport('/home/jmcadden/workspace/econ-cloud/src/ec2rates-useast_11-09-12_nopar.csv')
ec2_std = CSVImport('/home/jmcadden/workspace/econ-cloud/src/ec2rates-useast_11-09-12_standard.csv')

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
    nunit = Unit(capacity = float(row['Compute Units']), time = 1, cost = float(row['Rate On-demand']))
    ilist.append( Instance( name=count, desc=desc+" OD", unit=nunit, lease = lod))
    count += 1
    ilist.append( Instance( name=count, desc=desc+" 1Y", unit=nunit, lease = l1Y))
    count += 1
    ilist.append( Instance( name=count, desc=desc+" 3Y", unit=nunit, lease = l3Y))
    count += 1
  return ilist
  
def ugly_inst_print(insts):
  print "Lever | Instance Size | Utilization | Capacity | Base Rate | Lease Discount (1Y, 3Y) | Downpayment (1Y, 3Y) "
  for row in insts.data:
    print row['Level'], "|" ,row['Instance Type'], "|" , row['Utilization'], "|", row['Compute Units'], "| ", row['Rate On-demand'], "| (" , row['Rate 1YR'], ",", row['Rate 3YR'], ") | (", row['Upfront 1YR'],",",row['Upfront 3YR'], ")"
    

# Consumers
# X = work-distribution, Y = start time, Z = confidence
def loadconsumers(group, count=10, X=RealDistribution('uniform',[0,1]), Z=RealDistribution('uniform',[0,1]), Y=RealDistribution('gaussian',0.275)):
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


MAXWORK = 10000
MAXTIME = 1000000000
CONS = 1


ec2_insts = instances(ec2.data)
ec2_insts_np = instances(ec2_nopar.data)
ec2_insts_std = instances(ec2_std.data)

bsim1_conspecs = loadconsumers(group=1, count=CONS, X=RealDistribution('lognormal', [0, .75]))
bsim2_conspecs = loadconsumers(group=2, count=CONS, X=RealDistribution('lognormal', [0, .45]))
bsim3_conspecs = loadconsumers(group=2, count=CONS, X=RealDistribution('lognormal', [0, .25]))

bsim_fullconspec = {}
bsim_fullconspec['work'] = bsim1_conspecs['work'] + bsim2_conspecs['work'] + bsim3_conspecs['work']
bsim_fullconspec['start_time'] = bsim1_conspecs['start_time'] + bsim2_conspecs['start_time'] + bsim3_conspecs['start_time']
bsim_fullconspec['actual'] = bsim1_conspecs['actual'] + bsim2_conspecs['actual'] + bsim3_conspecs['actual']

#bsim1 = Marketplace_2DRY( name = "EC2: group 1", instances = ec2_insts, consumers = bsim1_conspecs)
#bsim2 = Marketplace_2DRY( name = "EC2: group 2", instances = ec2_insts, consumers = bsim2_conspecs)
#bsim3 = Marketplace_2DRY( name = "EC2: group 3", instances = ec2_insts, consumers = bsim3_conspecs)
bsim1 = Marketplace( name = "EC2: group 1", instances = ec2_insts_np, consumers = bsim1_conspecs)
bsim2 = Marketplace( name = "EC2: group 2", instances = ec2_insts_np, consumers = bsim2_conspecs)
bsim3 = Marketplace( name = "EC2: group 3", instances = ec2_insts_np, consumers = bsim3_conspecs)
bsim1.start()
bsim2.start()
bsim3.start()
bsim1_res_i =  bsim1.results_inst()
bsim1_res_c =  bsim1.results_cons()
bsim2_res_i =  bsim2.results_inst()
bsim2_res_c =  bsim2.results_cons()
bsim3_res_i =  bsim3.results_inst()
bsim3_res_c =  bsim3.results_cons()
bsim1.finish()
bsim2.finish()
bsim3.finish()

print "\nGROUP A"
print "Work"
print "Mean", mean(bsim1_res_c['work'])
print "Median", median(bsim1_res_c['work'])
print "Rate", (mean(bsim1_res_c['work']) / mean(bsim1_res_c['time']))
print "Cost"
print "Mean", mean(bsim1_res_c['cost'])
print "Median", median(bsim1_res_c['cost'])
print "Time"
print "Mean", mean(bsim1_res_c['time'])
print "Median", median(bsim1_res_c['time'])


print "\nGROUP B"
print "Work"
print "Mean", mean(bsim2_res_c['work'])
print "Median", median(bsim2_res_c['work'])
print "Rate", (mean(bsim2_res_c['work']) / mean(bsim2_res_c['time']))
print "Cost"
print "Mean", mean(bsim2_res_c['cost'])
print "Median", median(bsim2_res_c['cost'])
print "Time"
print "Mean", mean(bsim2_res_c['time'])
print "Median", median(bsim2_res_c['time'])

print "\nGROUP C"
print "ork"
print "Mean", mean(bsim3_res_c['work'])
print "Median", median(bsim3_res_c['work'])
print "Rate", (mean(bsim3_res_c['work']) / mean(bsim3_res_c['time']))
print "Cost"
print "Mean", mean(bsim3_res_c['cost'])
print "Median", median(bsim3_res_c['cost'])
print "Time"
print "Mean", mean(bsim3_res_c['time'])
print "Median", median(bsim3_res_c['time'])
