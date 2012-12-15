from sage.all import *

from CloudMarketplace import *
from CloudSecondary import *

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
    Z=RealDistribution('uniform',[0,1]), Y=RealDistribution('gaussian',0.275),
    MAXWORK = 10, MAXTIME=1000):
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
