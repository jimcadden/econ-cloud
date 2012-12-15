from sage.all import *

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
