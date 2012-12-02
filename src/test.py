"""
 Main test file 
"""
import csv, codecs, cStringIO
from CSVUtility import *
from CloudMarketplace import *
from CloudSecondary import *

MAXTIME  = 1000000

def instances(data):
  ilist = []
  count = 0
  # build three instances for each node type: on-demand, 1yr, 3yr
  for row in data:
    desc =  row['Level']+row['Utilization']+row['Instance Type']
    puc1YR = float(row['Rate 1YR']) / float(row['Rate On-demand'])
    puc3YR = float(row['Rate 3YR']) / float(row['Rate On-demand'])

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

def loadconsumers():
  ilist = [123456]#[100000,70000,50000, 9999]
  alist = [123456]#[100000,50000,60000, 7999]
  slist = [0]#[0,0,0,0]
  return {'work':ilist, 'start_time':slist, 'actual':alist}

def main():
  ec2 = CSVImport('ec2rates-useast_11-09-12.csv')
  ec2_nopar = CSVImport('ec2rates-useast_11-09-12_nopar.csv')
  ec2_std = CSVImport('ec2rates-useast_11-09-12_standard.csv')
  ec2_min = CSVImport('ec2rates-useast_11-09-12_min.csv')
# def __init__(self, name, instances, consumers):
#  sim1 = Marketplace( name = "b", instances = instances(ec2.data), consumers = loadconsumers())
  sim1 = Marketplace( name = "b", instances = instances(ec2_std.data), consumers = loadconsumers())
  sim1.start()
  print "CONSUMER RESULTS:\n",sim1.results_cons()
  print "INSTANCE RESULTS:\n",sim1.results_inst()
  sim1.finish()

# standard boilerplate
if __name__ == '__main__':
  main()
# fin.
