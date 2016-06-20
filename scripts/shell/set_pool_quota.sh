#!/bin/bash
zfs upgrade -a
zpool upgrade -a
DATASET="frzpool/normal frzpool/deduplicated frzpool/compressed"
TOTAL=$(zfs get -H -o value -p available frzpool)
echo
echo "Total Space available:			$TOTAL" 
quota_calc=$(awk "BEGIN {print ($TOTAL*85)/100}")
echo
echo "Applicable quota for all Datasets:	$quota_calc" 
echo
for dataset in $DATASET; do 
    QUOTA=$(zfs get -H -o value -p quota $dataset)
    if [ ${QUOTA} -eq 0 ]; then
    	echo "There is no quota on zfs dataset $dataset"
    	echo "Applying Quota on dataset $dataset..."
	echo
	zfs set quota=$quota_calc $dataset
	echo "Quota of $quota_calc is appplied on dataset $dataset"
	echo
    fi
done

echo "Complete quota info...:"
zfs get quota
