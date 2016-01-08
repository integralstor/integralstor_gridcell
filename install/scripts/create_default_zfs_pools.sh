#!/bin/sh

MAXBOOTSIZE=300 			#Assign maximum size for OS disk u wanted to skip for Default Pool creation

#############################################################################
#### This shell script creates a ZFS pool on each hard disk excluding the boot drive. The assumption is that the OS drive will be smaller than MAXBOOTSIZE
#### and that the data drives will be larger than that.
#### Warning! removes all the data in the existing hard disk forcefully. #### 
#############################################################################

if [ -f /opt/integralstor/integralstor_gridcell/pools_created ] ; then
  exit 0
fi


#### To get the array of all block devices ####
declare -a block_devices
for disk in `lsblk | grep disk | cut -d' ' -f 1` ; do    # Gives list of block devices interms of sda, sdb, sdc 
    block_devices=(${block_devices[@]} $disk)
done
#echo "block device : "${block_devices[@]}

#### To get an array without the base OS ####
declare -a without_os
for DEV in "${block_devices[@]}" ; do
  if [ -b "/dev/$DEV" ] ; then
    #Command to get size of the hard disk
    SIZE=`cat /sys/block/$DEV/size`
    GB=$(($SIZE/2**21))			
    #echo $GB $MAXBOOTSIZE
    if [ $GB -gt $MAXBOOTSIZE ] ; then			# skips the disk which is greater than the MAXBOOTSIZE 
      without_os=(${without_os[@]} $DEV)
    fi
   fi
done

#echo "array without OS : " ${without_os[@]}   	#prints list of disks without os disk 



#### To get an array of Serial Nos ####
declare -a serialnos
for item in "${without_os[@]}" ; do
    disk_string="/dev/$item"
    slno=`hdparm -i $disk_string | grep SerialNo | cut -d' ' -f 4 | cut -d'=' -f 2`    # Gives the Serial No. of the Disk. 
    serialnos=(${serialnos[@]} $slno)
done
#echo "serial no : " ${serialnos[@]}



#### To get an array of disk_by_id skipping OS ####
declare -a disk_byid
for sno in "${serialnos[@]}" ; do
    byid=$(ls -l /dev/disk/by-id | grep scsi |awk "/$sno/ { print \$9;}" | egrep '[a-zA-Z0-9]' | head -n1)    # Gives only the disk names as in /dev/disk/by-id excluing OS drive.
 
    disk_byid=(${disk_byid[@]} $byid)
done 

#echo "Total disks without OS are ${#disk_byid[@]}"

# The array "${disk_byid[@]}" will contain all the disks excluding OS.
# This script is using the contents of array to create a raidz on zfs.

#echo ${disk_byid[@]}

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
