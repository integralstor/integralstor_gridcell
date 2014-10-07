
num_nodes = 5
disk_num = 1
first_node = 1
second_node = first_node + 1
init_node = 1
num_disks = 4

nl = []
count = 0
if num_nodes %2 == 0:
  while True:
    disk_num = 1
    while disk_num <= num_disks:
      d = {}
      d["node"] = first_node
      d["pool"] = disk_num
      print "node %d disk %d"%(first_node, disk_num)
      count += 1
      nl.append(d)

      d = {}
      d["node"] = second_node
      d["pool"] = disk_num
      print "node %d disk %d"%(second_node, disk_num)
      a = "node %d disk %d"%(second_node, disk_num)
      count += 1
      nl.append(a)
      disk_num += 1

    first_node = 1 if first_node == num_nodes else first_node + 2
    second_node = 1 if second_node == num_nodes else second_node + 2
    if second_node == 1:
      break
else:
  tl = []
  while True:
    a = "node %d disk %d"%(first_node, disk_num)
    if a in nl:
      break
    d = {}
    d["node"] = first_node
    d["pool"] = disk_num
    print "node %d disk %d"%(first_node, disk_num)
    count += 1
    nl.append(d)
    tl.append(a)

    disk_num = 1 if disk_num == num_disks else disk_num + 1
    d = {}
    d["node"] = second_node
    d["pool"] = disk_num
    nl.append(a)
    count += 1
    print "node %d disk %d"%(second_node, disk_num)
    a = "node %d disk %d"%(second_node, disk_num)
    tl.append(a)
    disk_num = 1 if disk_num == num_disks else disk_num + 1

    if second_node + 1 > num_nodes:
      first_node = second_node
      second_node = init_node
    else:
      first_node = second_node
      second_node = second_node + 1

print count
