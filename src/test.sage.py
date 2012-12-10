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
ec2_min = CSVImport('/home/jmcadden/workspace/econ-cloud/src/ec2rates-useast_11-09-12_min.csv')

############################################

MAXWORK = 1000000
MAXTIME = 100000000
CONS = 100000
RDEPTH = 2 # recursion depth

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
  print "WORK"
  print "act/exp %", (mean(res['actual']) / mean(res['work'])*100),"%"
  print "mean (exp)", mean(res['work'])
  print "median (exp)", median(res['work'])
  print "mean (act)", mean(res['actual'])
  print "median (act)", median(res['actual'])
  print "mate (act)", (mean(res['actual']) / mean(res['time']))
  print "\nCOST"
  print "mean", mean(res['cost'])
  print "median", median(res['cost'])
  print "\nTIME"
  print "mean", mean(res['time'])
  print "median", median(res['time'])
  print "remaing time", sum(res['rtime'])

def ins_res_print2(rtn):
  for i in range(len(rtn['name'])):
     print i,rtn['name'][i],rtn['desc'][i]
     print "invoked:", rtn['invoked'][i]
     print "work:", rtn['work'][i]
     print "income:", rtn['income'][i]
     print "time:", rtn['time'][i]
     print "rtime:", rtn['rtime'][i]
     print "resell:", rtn['resell'][i]
     print "resold:", rtn['resold'][i]
     print "-----------------------------"

def ins_res_print(rtn):
  for i in range(len(rtn['name'])):
     print i,rtn['name'][i],rtn['desc'][i]
     print "work:", rtn['work'][i]
     print "income:", rtn['income'][i]
     print "time:", rtn['time'][i]
     print "rtime:", rtn['rtime'][i]
     print "-----------------------------"

def pmkt_res_print(res):
  print "started", res['consumers']
  print "finished",res['finished']
  print "income", res['income']
  print "remaing time", res['rtime']
  print "cache", res['cache']
  
def sdry_res_print(res):
  print "listed:", res['listed']
  print "sold:", res['sold']
  print "unsold:", res['unsold']
  print "fee:", res['resale_fee']
  print "income:", res['income_2dry']
  print "total income:", res['income_2dry'] + res['income']

def sim_print2(sim):
  print "====================================================================================="
  print "=== ",sim['mrkt']['name']," RESULTS" 
  print "====================================================================================="
  print "\nCONSULTANT"
  print "-----------------------------------------"
  con_res_print(sim['cons'])
  print "\nINSTANCES"
  print "-----------------------------------------"
  ins_res_print2(sim['inst'])
  print "\nPRIMARY MARKET"
  print "-----------------------------------------"
  pmkt_res_print(sim['mrkt'])
  print "\nSECONDARY MARKET"
  print "-----------------------------------------"
  sdry_res_print(sim['mrkt'])
  print "\n====================================================================================="
  print "====================================================================================="

def sim_print(sim):
  print "====================================================================================="
  print "=== ",sim['mrkt']['name']," RESULTS" 
  print "====================================================================================="
  print "\nCONSULTANT"
  print "-----------------------------------------"
  con_res_print(sim['cons'])
  print "\nINSTANCES"
  print "-----------------------------------------"
  ins_res_print(sim['inst'])
  print "\nPRIMARY MARKET"
  print "-----------------------------------------"
  pmkt_res_print(sim['mrkt'])
  print "\n====================================================================================="
  print "====================================================================================="
#bsim_fullconspec = {}
#bsim_fullconspec['work'] = bsim1_conspecs['work'] + bsim2_conspecs['work'] + bsim3_conspecs['work']
#bsim_fullconspec['start_time'] = bsim1_conspecs['start_time'] + bsim2_conspecs['start_time'] + bsim3_conspecs['start_time']
#bsim_fullconspec['actual'] = bsim1_conspecs['actual'] + bsim2_conspecs['actual'] + bsim3_conspecs['actual']

#bsim1 = Marketplace_2DRY( name = "EC2: group 1", instances = ec2_insts, consumers = bsim1_conspecs)
#bsim2 = Marketplace_2DRY( name = "EC2: group 2", instances = ec2_insts, consumers = bsim2_conspecs)
#bsim3 = Marketplace_2DRY( name = "EC2: group 3", instances = ec2_insts, consumers = bsim3_conspecs)

ec2 = []
ec2.append(instances(ec2_full.data)) #0
ec2.append(instances(ec2_nopar.data)) #1
ec2.append(instances(ec2_std.data)) #2
ec2.append(instances(ec2_min.data)) #3

def run_3gsim_p(name="Primary Market Test", idx=1, conspecs=0, rdepth=RDEPTH,
    cacheOn=False):
  sim1 = Marketplace( name=name, instances=ec2[idx], consumers = conspecs,
      rdepth= rdepth, cacheOn=cacheOn) 
  sim1.start()
  sim1.finish()
  return sim1.results()

def run_3gsim_2(name="Secondary Market Test", idx=1, conspecs=0, rdepth=RDEPTH): 
  sim1 = Marketplace_2DRY( name=name, instances=ec2[idx], consumers = conspecs,
      rdepth= rdepth, cacheOn=False, buy2sell=False)
  sim1.start()
  sim1.finish()
  return sim1.results()

###########################

cons = loadconsumers(group=1, count=CONS, X=RealDistribution('lognormal',
  [0, .75]))

sim_print(run_3gsim_p("PRIMARY", 3, cons))

print "CACHE ON!!!############################################"

sim_print(run_3gsim_p("PRIMARY", 3, cons, RDEPTH, True))
#sim_print2(run_3gsim_2("SECONDARY", 3, cons))
