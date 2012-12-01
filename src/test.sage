{\rtf1\ansi\ansicpg1252\cocoartf1187\cocoasubrtf340
{\fonttbl\f0\fswiss\fcharset0 Helvetica;}
{\colortbl;\red255\green255\blue255;}
\margl1440\margr1440\vieww25400\viewh13760\viewkind0
\pard\tx720\tx1440\tx2160\tx2880\tx3600\tx4320\tx5040\tx5760\tx6480\tx7200\tx7920\tx8640\pardirnatural

\f0\fs24 \cf0 \{\{\{id=40|\
import numpy as np\
import matplotlib.mlab as mlab\
import matplotlib.pyplot as plt\
\
load '/home/jmcadden/workspace/econ-cloud/src/CloudMarketplace.py'\
load '/home/jmcadden/workspace/econ-cloud/src/CloudSecondary.py'\
load '/home/jmcadden/workspace/econ-cloud/src/CSVUtility.py'\
\
ec2 = CSVImport('/home/jmcadden/workspace/econ-cloud/src/ec2rates-useast_11-09-12.csv')\
ec2_nopar = CSVImport('/home/jmcadden/workspace/econ-cloud/src/ec2rates-useast_11-09-12_nopar.csv')\
ec2_std = CSVImport('/home/jmcadden/workspace/econ-cloud/src/ec2rates-useast_11-09-12_standard.csv')\
///\
\}\}\}\
\
\{\{\{id=2|\
# Instances    \
def instances(data):\
  ilist = []\
  count = 0\
  # build three instances for each node type: on-demand, 1yr, 3yr\
  for row in data:\
    desc =  row['Level']+row['Utilization']+row['Instance Type']\
    puc1YR =  float(row['Rate 1YR']) / float(row['Rate On-demand'])\
    puc3YR = float(row['Rate 3YR']) / float(row['Rate On-demand'])\
    lod = Lease(length = 0, downp = 0, puc = 1)\
    l1Y = Lease(length = 8760, downp = float(row['Upfront 1YR']), puc = puc1YR) \
    l3Y = Lease(length = 26280, downp = float(row['Upfront 3YR']), puc = puc3YR) \
    nunit = Unit(capacity = float(row['Compute Units']), time = 1, cost = float(row['Rate On-demand']))\
    ilist.append( Instance( name=count, desc=desc+" OD", unit=nunit, lease = lod))\
    count += 1\
    ilist.append( Instance( name=count, desc=desc+" 1Y", unit=nunit, lease = l1Y))\
    count += 1\
    ilist.append( Instance( name=count, desc=desc+" 3Y", unit=nunit, lease = l3Y))\
    count += 1\
  return ilist\
  \
def ugly_inst_print(insts):\
  print "Lever | Instance Size | Utilization | Capacity | Base Rate | Lease Discount (1Y, 3Y) | Downpayment (1Y, 3Y) "\
  for row in insts.data:\
    print row['Level'], "|" ,row['Instance Type'], "|" , row['Utilization'], "|", row['Compute Units'], "| ", row['Rate On-demand'], "| (" , row['Rate 1YR'], ",", row['Rate 3YR'], ") | (", row['Upfront 1YR'],",",row['Upfront 3YR'], ")"\
    \
# Consumers\
# X = work-distribution, Y = start time, Z = confidence\
def loadconsumers(group, count=10, X=RealDistribution('uniform',[0,1]), Z=RealDistribution('uniform',[0,1]), Y=RealDistribution('gaussian',0.275)):\
  wtmp = []\
  time = []\
  actu = []\
  # populate distribution list\
  for i in range(count):\
    wtmp.append(X.get_random_element())\
    actu.append(Y.get_random_element()+1)\
    time.append(Z.get_random_element())\
    \
  # normalize distribution & apply values\
  wmax = max(wtmp)\
  work = [x/(wmax*1.0)*MAXWORK for x in wtmp]\
  ttmp = time\
  tmax = max(time)\
  time = [x/(tmax*1.0)*(MAXTIME - MAXWORK) for x in ttmp]\
  \
  atmp = actu\
  count = 0\
  for x in atmp:\
      if x > 0: #and x <= 1:\
          actu[count] = work[count] * actu[count]\
      else: \
          actu[count] = 0 # total fail \
      count += 1\
  return \{'group':group,'start_time':time, 'work':work, 'actual':actu\}\
///\
\}\}\}\
\
\{\{\{id=33|\
MAXWORK = 1000000\
MAXTIME = 1000000000\
CONS = 100\
///\
\}\}\}\
\
\{\{\{id=37|\
ec2_insts = instances(ec2.data)\
ec2_insts_np = instances(ec2_nopar.data)\
ec2_insts_std = instances(ec2_std.data)\
\
bsim1_conspecs = loadconsumers(group=1, count=CONS, X=RealDistribution('lognormal', [0, .75]))\
bsim2_conspecs = loadconsumers(group=2, count=CONS, X=RealDistribution('lognormal', [0, .45]))\
bsim3_conspecs = loadconsumers(group=2, count=CONS, X=RealDistribution('lognormal', [0, .25]))\
\
bsim_fullconspec = \{\}\
bsim_fullconspec['work'] = bsim1_conspecs['work'] + bsim2_conspecs['work'] + bsim3_conspecs['work']\
bsim_fullconspec['start_time'] = bsim1_conspecs['start_time'] + bsim2_conspecs['start_time'] + bsim3_conspecs['start_time']\
bsim_fullconspec['actual'] = bsim1_conspecs['actual'] + bsim2_conspecs['actual'] + bsim3_conspecs['actual']\
\
ugly_inst_print(ec2_nopar)\
///\
Lever | Instance Size | Utilization | Capacity | Base Rate | Lease Discount (1Y, 3Y) | Downpayment (1Y, 3Y) \
\}\}\}\
\
<h1><strong>Customer Distribution Graphs<br /></strong></h1>\
\
\{\{\{id=6|\
# the histogram of the worker group\
n, bins, patches = plt.hist(bsim_fullconspec['actual'], 50, facecolor='y', alpha=0.2)\
n, bins, patches = plt.hist(bsim1_conspecs['work'], 50, facecolor='g', alpha=0.8)\
n, bins, patches = plt.hist(bsim2_conspecs['work'], 50, facecolor='b', alpha=0.8)\
n, bins, patches = plt.hist(bsim3_conspecs['work'], 50, facecolor='r', alpha=0.8)\
\
plt.xlabel('Workload')\
plt.ylabel('Customers')\
plt.title("Workloads")\
plt.grid(True)\
plt.savefig('hist1')\
plt.close()\
\
\
\
plot1 = plt.plot(bsim_fullconspec['work'],bsim_fullconspec['actual'],'mo', linewidth=0, alpha=0.2)\
\
plt.xlabel('Expected')\
plt.ylabel('Actual')\
plt.title('Actual Work vs Expected Work')\
plt.grid(True)\
plt.savefig('plot1')\
plt.close()\
///\
\}\}\}\
\
<h1>Primary Market Simulation</h1>\
\
\{\{\{id=10|\
#bsim1 = Marketplace_2DRY( name = "EC2: group 1", instances = ec2_insts, consumers = bsim1_conspecs)\
#bsim2 = Marketplace_2DRY( name = "EC2: group 2", instances = ec2_insts, consumers = bsim2_conspecs)\
#bsim3 = Marketplace_2DRY( name = "EC2: group 3", instances = ec2_insts, consumers = bsim3_conspecs)\
bsim1 = Marketplace( name = "EC2: group 1", instances = ec2_insts, consumers = bsim1_conspecs)\
bsim2 = Marketplace( name = "EC2: group 2", instances = ec2_insts, consumers = bsim2_conspecs)\
bsim3 = Marketplace( name = "EC2: group 3", instances = ec2_insts, consumers = bsim3_conspecs)\
bsim1.start()\
bsim2.start()\
bsim3.start()\
bsim1_res_i =  bsim1.results_inst()\
bsim1_res_c =  bsim1.results_cons()\
bsim2_res_i =  bsim2.results_inst()\
bsim2_res_c =  bsim2.results_cons()\
bsim3_res_i =  bsim3.results_inst()\
bsim3_res_c =  bsim3.results_cons()\
bsim1.finish()\
bsim2.finish()\
bsim3.finish()\
///\
\}\}\}\
\
<h\
\{\{\{id=49|\
plot4 = plt.plot(bsim3_res_c['work'],bsim3_res_c['cost'],'ro', linewidth=0, alpha=0.2)\
plot4 = plt.plot(bsim2_res_c['work'],bsim2_res_c['cost'],'bo', linewidth=0, alpha=0.2)\
plot4 = plt.plot(bsim1_res_c['work'],bsim1_res_c['cost'],'go', linewidth=0, alpha=0.2)\
plt.xlabel('Work')\
plt.ylabel('Cost')\
plt.title('Cost vs Work')\
plt.grid(True)\
#plt.yscale('log')\
plt.savefig('plot4')\
plt.close()\
\
plot1 = plt.plot(bsim1_res_c['work'],bsim1_res_c['cost'],'gx', linewidth=0, alpha=0.5)\
plt.xlabel('Work')\
plt.ylabel('Cost')\
plt.title('Group A - Cost vs. Work')\
plt.grid(True)\
plt.savefig('plot1')\
plt.close()\
\
plot2 = plt.plot(bsim2_res_c['work'],bsim2_res_c['cost'],'bx', linewidth=0, alpha=0.5)\
plt.xlabel('Work')\
plt.ylabel('Cost')\
#plt.yscale('log')\
plt.title('Group B - Cost vs. Work')\
plt.grid(True)\
plt.savefig('plot2')\
plt.close()\
\
plot3 = plt.plot(bsim3_res_c['work'],bsim3_res_c['cost'],'rx', linewidth=0, alpha=0.5)\
plt.xlabel('Work')\
plt.ylabel('Cost')\
#plt.yscale('symlog')\
plt.title('Group C - Cost vs. Work')\
plt.grid(True)\
plt.savefig('plot3')\
plt.close()\
///\
\}\}\}\
\
\{\{\{id=54|\
bsim1_cpu = [(a+1)/(b+1) for a,b in zip(bsim1_res_c['work'],bsim1_res_c['cost'])]\
bsim2_cpu = [(a+1)/(b+1) for a,b in zip(bsim2_res_c['work'],bsim2_res_c['cost'])]\
bsim3_cpu = [(a+1)/(b+1) for a,b in zip(bsim3_res_c['work'],bsim3_res_c['cost'])]\
\
plot4 = plt.plot(bsim1_res_c['work'],bsim1_cpu,'ro', linewidth=0, alpha=0.2)\
plot4 = plt.plot(bsim2_res_c['work'],bsim2_cpu,'bo', linewidth=0, alpha=0.2)\
plot4 = plt.plot(bsim3_res_c['work'],bsim3_cpu,'go', linewidth=0, alpha=0.2)\
plt.xlabel('Workload')\
plt.ylabel('Work per Dollar')\
plt.title(r'Cost of Work')\
#plt.yscale('log')\
plt.grid(True)\
plt.savefig('plot4')\
plt.close()\
\
plot1 = plt.plot(bsim1_res_c['work'],bsim1_cpu,'ro', linewidth=0, alpha=0.5)\
plt.xlabel('Workload')\
plt.ylabel('Work per Dollar')\
plt.title(r'Group A - Cost of Work')\
plt.grid(True)\
plt.savefig('plot1')\
plt.close()\
\
plot2 = plt.plot(bsim2_res_c['work'],bsim2_cpu,'bo', linewidth=0, alpha=0.5)\
plt.xlabel('Workload')\
plt.ylabel('Work per Dollar')\
plt.title(r'Group B - Cost of Work')\
plt.grid(True)\
plt.savefig('plot2')\
plt.close()\
\
plot3 = plt.plot(bsim3_res_c['work'],bsim3_cpu,'go', linewidth=0, alpha=0.5)\
plt.xlabel('Workload')\
plt.ylabel('Work per Dollar')\
#plt.yscale('log')\
plt.title(r'Group C - Cost of Work')\
plt.grid(True)\
plt.savefig('plot3')\
plt.close()\
///\
\}\}\}\
\
\{\{\{id=29|\
bsim1_eff = [a/b/c for a,b,c in zip(bsim1_res_c['work'],bsim1_res_c['cost'],bsim1_res_c['time'])]\
bsim2_eff = [a/b/c for a,b,c in zip(bsim2_res_c['work'],bsim2_res_c['cost'],bsim2_res_c['time'])]\
bsim3_eff = [a/b/c for a,b,c in zip(bsim3_res_c['work'],bsim3_res_c['cost'],bsim3_res_c['time'])]\
\
bsim1_cpu = [a/b for a,b in zip(bsim1_res_c['work'],bsim1_res_c['cost'])]\
bsim2_cpu = [a/b for a,b in zip(bsim2_res_c['work'],bsim2_res_c['cost'])]\
bsim3_cpu = [a/b for a,b in zip(bsim3_res_c['work'],bsim3_res_c['cost'])]\
\
\
plot1 = plt.plot(bsim1_cpu,bsim1_eff,'rx', linewidth=0, alpha=0.5)\
plt.xlabel('Work-per-dollar')\
plt.ylabel('Work-per-dollar over Time')\
plt.title(r'Group A - Efficiency')\
plt.grid(True)\
plt.savefig('plot1')\
plt.close()\
\
plot2 = plt.plot(bsim2_cpu,bsim2_eff,'bx', linewidth=0, alpha=0.5)\
plt.xlabel('Work-per-dollar')\
plt.ylabel('Work-per-dollar over Time')\
plt.title(r'Group B -Efficiency')\
plt.grid(True)\
plt.savefig('plot2')\
plt.close()\
\
plot3 = plt.plot(bsim3_cpu,bsim3_eff,'gx', linewidth=0, alpha=0.5)\
plt.xlabel('Work-per-dollar')\
plt.ylabel('Work-per-dollar over Time')\
plt.title(r'Group C -Efficiency')\
plt.grid(True)\
plt.savefig('plot3')\
plt.close()\
\
\
plot5 = plt.plot(bsim1_cpu,bsim1_eff,'rx', linewidth=0, alpha=0.3)\
plot5 = plt.plot(bsim2_cpu,bsim2_eff,'bx', linewidth=0, alpha=0.3)\
plot5 = plt.plot(bsim3_cpu,bsim3_eff,'gx', linewidth=0, alpha=0.3)\
plt.xlabel('Work-per-dollar')\
plt.ylabel('Work-per-dollar over Time')\
plt.title(r'Efficiency')\
plt.grid(True)\
plt.savefig('plot5')\
plt.close()\
///\
\}\}\}\
\
\
\{\{\{id=70|\
remain = filter(lambda a: a != 0, bsim1_res_c['rtime'])\
\
print len(bsim1_res_c['rtime'])\
print len(remain)\
///\
\
\}\}\}\
\
\{\{\{id=56|\
# the histogram of the worker group\
n, bins, patches = plt.hist(filter(lambda a: a != 0, (bsim1_res_c['rtime']+bsim2_res_c['rtime']+bsim3_res_c['rtime'])), 50, facecolor='m', alpha=0.8)\
\
plt.xlabel('Remaining Hours')\
plt.ylabel('Customers')\
plt.title("Remaining Time")\
plt.grid(True)\
plt.savefig('hist4')\
plt.close()\
///\
\
\}\}\}\
\
\{\{\{id=13|\
print "GROUP A"\
print "Work"\
print "-Mean", mean(bsim1_res_c['work'])\
print "-Median", median(bsim1_res_c['work'])\
print "-Rate", (mean(bsim1_res_c['work']) / mean(bsim1_res_c['time']))\
print "Cost"\
print "-Mean", mean(bsim1_res_c['cost'])\
print "-Median", median(bsim1_res_c['cost'])\
print "Time"\
print "-Mean", mean(bsim1_res_c['time'])\
print "-Median", median(bsim1_res_c['time'])\
\
\
print "\\nGROUP B"\
print "Work"\
print "-Mean", mean(bsim2_res_c['work'])\
print "-Median", median(bsim2_res_c['work'])\
print "-Rate", (mean(bsim2_res_c['work']) / mean(bsim2_res_c['time']))\
print "Cost"\
print "-Mean", mean(bsim2_res_c['cost'])\
print "-Median", median(bsim2_res_c['cost'])\
print "Time"\
print "-Mean", mean(bsim2_res_c['time'])\
print "-Median", median(bsim2_res_c['time'])\
\
print "\\nGROUP C"\
print "Work"\
print "-Mean", mean(bsim3_res_c['work'])\
print "-Median", median(bsim3_res_c['work'])\
print "-Rate", (mean(bsim3_res_c['work']) / mean(bsim3_res_c['time']))\
print "Cost"\
print "-Mean", mean(bsim3_res_c['cost'])\
print "-Median", median(bsim3_res_c['cost'])\
print "Time"\
print "-Mean", mean(bsim3_res_c['time'])\
print "-Median", median(bsim3_res_c['time'])\
///\
\}\}\}\
\
\{\{\{id=74|\
\
///\
\}\}\}}