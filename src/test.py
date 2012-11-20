"""
 Main test file 
"""
import csv, codecs, cStringIO
from CSVUtility import *
from CloudMarketplace import *
from CloudSecondary import *

MAX_CONSUMERS = 100
MAXWORK = 50
MAXTIME  = 1000000

def instances(data):
  ilist = []
  count = 0
  # build three instances for each node type: on-demand, 1yr, 3yr
  for row in data:
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

def loadconsumers():
  ilist = []
  ilist.append({'work':1000, 'start':0})
  ilist.append({'work':1000, 'start':0})
  ilist.append({'work':1000, 'start':0})
  return ilist

def main():
  ec2 = CSVImport('ec2rates-useast_11-09-12.csv')
  ec2_nopar = CSVImport('ec2rates-useast_11-09-12_nopar.csv')
# def __init__(self, name, instances, consumers):
  sim1 = Marketplace( name = "basic", \
      instances = instances(ec2_nopar.data), consumers = loadconsumers())
  sim1.start()
  print sim1.results_inst()
  print sim1.results_cons()
  sim1.finish()

# standard boilerplate
if __name__ == '__main__':
  main()
# fin.
