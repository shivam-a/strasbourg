# -*- coding: utf-8 -*-
"""
Created on Thu Jun  7 14:36:42 2018

@author: slehmler
"""

#testing subprocess
from subprocess import Popen, PIPE, call, STDOUT
#process = Popen(['echo', 'Hello cmd'], stdout=PIPE, stderr=PIPE, shell=True)
#stdout, stderr = process.communicate()
#print(stdout)
#process = Popen(['cd', 'otp'], stdout=PIPE, stderr=PIPE, shell=True)
#process = Popen(['dir'], stdout=PIPE, stderr=PIPE, shell=True)
#stdout, stderr = process.communicate()
#print(stdout)
#print(os.path.isfile('otp/otp-1.1.0-shaded.jar'))

#call otp.jar to create the grpah object
#call(['java', '–Xmx10G','-jar', 'otp-1.1.0-shaded.jar', '--build strasbourg'])
#p = Popen(['java', '-jar', 'otp/otp-1.2.0-shaded.jar','--build', 'otp/graphs/strasbourg'], stdout=PIPE, stderr=STDOUT)
p = Popen(['java', '-Xmx2G', '-jar', './otp/otp-1.2.0-shaded.jar','--build', './otp/graphs/strasbourg', '--inMemory', '--port', '8801', '--securePort', '8802'], stdout=PIPE, stderr=STDOUT)
#for line in p.stdout:
#    print(line)

import requests
r = requests.get("http://localhost:8801/otp/routers/default/plan?fromPlace=47.21470,-1.55770&toPlace=47.21394,-1.55804&mode=BICYCLE,TRANSIT")
print(r.json())
r = requests.get("http://localhost:8801/otp/routers/default/plan?fromPlace=47.21470,-1.55770&toPlace=47.21394,-1.55804&mode=CAR")
print(r.json())
#"http://localhost:8801/otp/routers/default/plan?fromPlace=47.21470,-1.55770&toPlace=47.21394,-1.55804&time=1:02pm&date=06-20-2018&mode=BICYCLE,TRANSIT&maxWalkDistance=500&arriveBy=false"
#"http://localhost:8801/otp/routers/default/plan?fromPlace=47.21470,-1.55770&toPlace=47.21394,-1.55804&time=1:02pm&date=06-20-2018&mode=CAR&maxWalkDistance=500&arriveBy=false"
"http://localhost:8801/otp/routers/default/plan?fromPlace=47.21470,-1.55770&toPlace=47.21394,-1.55804&mode=CAR"
"http://localhost:8801/otp/routers/default/plan?fromPlace=47.21470,-1.55770&toPlace=47.21394,-1.55804&mode=BICYCLE,TRANSIT"
#p = Popen(['java', '-Xmx2G', '-jar', 'otp/otp-1.2.0-shaded.jar', '--router', 'strasbourg', '--server', '--port', '8809', '--securePort', '8810'], stdout=PIPE, stderr=STDOUT)
##for line in p.stdout:
##    print(line)
#
#import requests
#
#r = requests.get("localhost:8809/otp/routers/default/plan")

#TODO: 
# the code below doesn't work on my system as jython throws some error
    
#os.system("c:\jython2.7.0\bin\jython.exe -J-XX:-UseGCOverheadLimit -J-Xmx10G -Dpython.path=otp-1.1.0-shaded.jar sbg_car.py")
#p = Popen(['C:/jython2.7.0/bin/jython.exe', '-Dpython.path=otp-1.1.0-shaded.jar', 'otp/sbg_car.py'], stdout=PIPE, stderr=STDOUT)
#for line in p.stdout:
#    print(line)
#print(os.system('java –Xmx10G -jar otp-1.1.0-shaded.jar --build strasbourg'))