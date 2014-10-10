#!/usr/bin/python

def is_valid_ip(ip):
  parts = ip.split('.')
  return (
    len(parts) == 4
    and all(part.isdigit() for part in parts )
    and all(0 <= int(part) <= 255 for part in parts )
    )
