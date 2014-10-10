#!/usr/bin/python

import sys

import host_info

def get_your_host_ip():
  """ To get and display the list of IP's in the local machine """
  
  ips_list = host_info.get_ip_info()

  local_ips = [] # List of local machine's IP-Addresses
  try:
    for i in ips_list:
      local_ips.append(i['ip'])
  except KeyError as e:
      print e

  for j in local_ips:
    print local_ips.index(j),"\b)", j

  choice_ip = raw_input("\nFollowing IP-Adressess are found, Press the serial number for your IP-Address : ")

  # List Comphrension to validate invalid choice entered by the user
  list_of_indexes = [ local_ips.index(ix) for ix in local_ips ]  

  ucase_lst = map(chr, range(97, 123))
  lcase_lst = map(chr, range(65, 91 ))

  if choice_ip in ucase_lst:
    print "Please enter a valid serial number from the above list !!" 
    sys.exit(-1)
  
  if choice_ip in lcase_lst:
    print "Please enter a valid serial number from the above list !!" 
    sys.exit(-1)

  if int(choice_ip) not in list_of_indexes:
    print "Please enter a valid serial number from the above list !!" 
    sys.exit(-1)

  ip_addr_selected = []
  for ip_addr in local_ips:
    if int(choice_ip) == local_ips.index(ip_addr):
      print "Your selected choice is : ", local_ips.index(ip_addr)
      print "Related IP of your selected choice is : ", ip_addr, "\n"
      ip_addr_selected.append(ip_addr)

  return ip_addr_selected[0]

def get_your_host_mask():
  """ To get and display the list of Subnet Mask IP's in the local machine """

  ips_list = host_info.get_ip_info()

  local_masks = []
  try:
    for i in ips_list:
      local_masks.append(i['mask'])
  except KeyError as e:
      print e

  for j in local_masks:
    print local_masks.index(j),"\b)", j

  choice_mask = raw_input("\nFollowing Masks are found, Press the serial number for your Mask : ")

  # List Comphrension to validate invalid choice entered by the user
  list_of_indexes = [ local_masks.index(ix) for ix in local_masks ]  

  ucase_lst = map(chr, range(97, 123))
  lcase_lst = map(chr, range(65, 91 ))

  if choice_mask in ucase_lst:
    print "Please enter a valid serial number from the above list !!" 
    sys.exit(-2)
  
  if choice_mask in lcase_lst:
    print "Please enter a valid serial number from the above list !!" 
    sys.exit(-2)

  if int(choice_mask) not in list_of_indexes:
    print "Please enter a valid serial number from the above list !!" 
    sys.exit(-2)

  ip_mask_selected = []
  for l in local_masks:
    if int(choice_mask) == local_masks.index(l):
      print "Your selected choice is : ", local_masks.index(l)
      print "Related IP of your selected choice is : ", l, "\n"
      ip_mask_selected.append(l)

  return ip_mask_selected[0]

if __name__ == '__main__':
  get_your_host_mask()  
