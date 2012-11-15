"""
 Main test file 
"""
from CloudMarketplace import *

MAX_CONSUMERS = 10000
MAXWORK = 50
MAXTIME  = 10000000000

def main():
  ec2data = CSVImport('ec2rates-useast_11-09-12.csv')
  ec2data_nopar = CSVImport('ec2rates-useast_11-09-12_nopar.csv')

  sim1 = Marketplace( name = "basic", instances = ec2data_nopar.instances(), \
      consumer_count = MAX_CONSUMERS, maxwork = MAXWORK, maxtime= MAXTIME)
  sim1.start()
  sim1.results("filename")
  sim1.finish()

# standard boilerplate
if __name__ == '__main__':
	main()
# fin.
