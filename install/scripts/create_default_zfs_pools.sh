#!/bin/sh

#############################################################################
#### This shell script creates ZFS pool on each hard disk excluding SSD. ####
#### Warning! removes all the data in the existing hard disk forcefully. #### 
#############################################################################

if [ -f /opt/integralstor/integralstor_gridcell/pools_created ] ; then
  exit 0
fi


#### To get the array of all block devices ####
declare -a block_devices
for disk in `lsblk | grep disk | cut -d' ' -f 1` ; do    # Gives list of block devices interms of sda, sdb, sdc ...
    block_devices=(${block_devices[@]} $disk)
done
#echo "block device : ", ${block_devices[@]}



#### To get an array without SSD ####
declare -a without_ssd
for i in "${block_devices[@]}" ; do
    #echo "entry: $i"
    output=`cat /sys/block/$i/queue/rotational`          # Value in the file /sys/block/$i/queue/rotational will be 0 if disk is an SSD.
    if [ $output -ne 0 ]; then
        #echo $i
        without_ssd=(${without_ssd[@]} $i)
    fi
done
#echo "array without ssd : " ${without_ssd[@]}    



#### To get an array of Serial Nos ####
declare -a serialnos
for item in "${without_ssd[@]}" ; do
    disk_string="/dev/$item"
    slno=`hdparm -i $disk_string | grep SerialNo | cut -d' ' -f 4 | cut -d'=' -f 2`    # Gives the Serial No. of the Disk. 
    serialnos=(${serialnos[@]} $slno)
done
#echo "serial no : " ${serialnos[@]}



#### To get an array of disk_by_id skipping ssd, as by convention SSD will have the OS ####
declare -a disk_byid
for sno in "${serialnos[@]}" ; do
    byid=$(ls -l /dev/disk/by-id | awk "/$sno/ { print \$9;}" | egrep '[a-zA-Z0-9]' | head -n1)    # Gives only the disk names as in /dev/disk/by-id excluing SSD.
 
    disk_byid=(${disk_byid[@]} $byid)
done 

echo "Total disks without SSD are ${#disk_byid[@]}"

# The array "${disk_byid[@]}" will contain all the disks excluding SSD.
# This script is using the contents of array to create a raidz on zfs.

# ZFS command to create raidz pool on the disks.
/sbin/zpool create frzpool raidz ${disk_byid[@]} -f
/sbin/zfs set acltype=posixacl frzpool
/sbin/zfs set xattr=sa frzpool
/sbin/zfs set atime=off frzpool

if [ $? != 0 ] ; then
    echo "zpool creation failed. Exiting !!"
    exit -1     
fi

if [ $? == 0 ] ; then

    # 3 datasets : 1. Normal 2. Compress 3. Deduplication
    /sbin/zfs create frzpool/normal

    /sbin/zfs create -o dedup=on frzpool/deduplicated

    /sbin/zfs create -o compression=on frzpool/compressed
    
    # Displays the ouput of zpool list
    echo "zpool list : "`zpool list frzpool`

fi
touch /opt/integralstor/integralstor_gridcell/pools_created
