#!/usr/bin/env python
import os
import sys
import pysphere
import math
import Queue
import threading
import ipcalc

vc_ip = "127.0.0.1"
vc_user = "cool_user"
vc_pass = "cool_password"
mgmt_networks = ['192.168.68.0/23', '172.16.100.0/24']

num_vc_conns = 8 # max number of connections this script will make to vCenter
vm_jobs = 10 # Number of vms a thread will pull at a time from the work queue

server = pysphere.VIServer()
server.connect(vc_ip, vc_user, vc_pass)
vmxlist = server.get_registered_vms()
server.disconnect()
queue = Queue.Queue()
queue_collector = Queue.Queue()

class HostfileBuilder(threading.Thread):
    def __init__(self, queue, oqueue):
        threading.Thread.__init__(self)
        self.queue = queue
        self.server = pysphere.VIServer()
        self.server.connect(vc_ip, vc_user, vc_pass)
        self.oqueue = oqueue

    def run(self):
        ip_to_int = lambda ip: reduce(lambda x,y: x+y,
            [x << (y * 8)
            for (x,y) in zip(
            [long(x) for x in ip.split('.')[::-1]], range(4))])
        netcalc = lambda network: (ipcalc.Network(network).host_first().ip,
            ipcalc.Network(network).host_last().ip)
        while self.queue.unfinished_tasks > 0:
            vm_todo_list = self.queue.get()
            for vm in vm_todo_list:
                vmo = self.server.get_vm_by_path(vm)
                nets = vmo.get_property('net')
                if nets != None:
                    ips = [ip 
                        for net in nets 
                        for ip in net['ip_addresses'] 
                        for mgmt_net in mgmt_networks
                        if ":" not in ip 
                        and netcalc(mgmt_net)[0] < 
                        ip_to_int(ip) < 
                        netcalc(mgmt_net)[-1]]
                    for ip in ips:
                        self.oqueue.put({ip: vmo.get_property('name')})
            self.queue.task_done()
        self.server.disconnect()

runq = lambda start, end: {"start": start + vm_jobs, "end": end + vm_jobs}
start, end = 0, vm_jobs
for i in range(int(math.ceil(len(vmxlist)/float(vm_jobs)))):
    queue.put(vmxlist[start:end])
    start,end = runq(start,end)['start'], runq(start,end)['end']

for i in range(num_vc_conns):
    hsb = HostfileBuilder(queue, queue_collector)
    hsb.setDaemon(True)
    hsb.start()

queue.join()

hostlist = {}
while queue_collector.unfinished_tasks > 0:
    entry = queue_collector.get()
    for k,v in entry.items():
        hostlist[k] = v
    queue_collector.task_done()


tpl = open(os.path.join(os.path.dirname(__file__), "hosts.tpl"), 'r')
template = tpl.readlines()
tpl.close()

if sys.platform == "win32":
    system_host_file = os.path.join(os.sep, os.getenv("SystemRoot"), "system32", "drivers", "etc", "hosts")
else:
    """ Swap these if you're testing! """
    system_host_file = os.path.join(os.sep, "etc", "hosts")
    #system_host_file = os.path.join(os.path.dirname(__file__), "hosts")

outfile = open(system_host_file, 'w')

for t in template:
    outfile.write(t)
for k,v in hostlist.items():
    outfile.write("%-20s\t%s\n" % (k,v))
outfile.close()
