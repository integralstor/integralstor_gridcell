#!/bin/sh

#######################################################################
#The exit status codes used: 

    # -1: Need to be a super user i.e root.
    # -2: Operation, git clone from www.github.com failed.
    # -3: Failed to create "/opt/integralstor/integral_view/integral_view"
    # -4: Failed to do a git branch

#######################################################################
'''
*NOTE:
"Your Machine must be configured with git basic settings with https or ssh in order to do a clone of integral view. "
"The clone will be taken from https://$github_username@github.com/fractalio/integral-view.git "
"Make sure that the Branch you mention should also be available publically with public repo"
"For sending files from one server(local system) to the remote server(the installation server) you need to configure passwordless SSH" 
#naveen.mh08@gmail.com
''' 

# To force the user to be a super-user: root
if [[ $EUID != 0 ]]; then
  echo "You must be root to run this script !! Login as \"root\" and try again." 2>&1
  exit -1
fi

# Changing dir to /tmp dir
cd /tmp
rm -rf /tmp/integralstor_gridcell*
rm -rf /tmp/integralstor_common*

# To clone the integral-view.git
git clone https://github.com/integralstor/integralstor_common.git
git clone https://github.com/integralstor/integralstor_gridcell.git
echo

echo "Want to pull specific BRANCH and/or TAG? Press <YES> else Press <ENTER> to pull automatically the latest tag for Both Gridcell and common:"
read input1
    if [[ $input1 == "y" || $input1 == "Y" || $input1 == "yes" || $input1 == "Yes" || $input1 == "YES" ]] ; then

	echo "You are in 'integralstor_common' now. To pull from any branch, enter 'branch' else enter 'tag'"
	read input2
	if [[ $input2 == "branch" ]] ; then
	    	cd /tmp/integralstor_common
	    echo "Available Git 'branches' are:"
	    echo
	    	git branch -a
	    echo
	    read -p "Enter the required branch from above: " branchcmmn	# change the branch name as per the requirement
	    echo
	    	git checkout $branchcmmn 
	    	touch /tmp/integralstor_common/version
	    echo "$branchcmmn" > /tmp/integralstor_common/version	
	    echo "Downloaded from Branch :"
	    	git branch
	    	cd /tmp
		rm -rf /tmp/integralstor_common/.git*
	    	tar czf integralstor_common.tar.gz integralstor_common/ 		# creating zip file of integralstor_common
		yes | cp -r integralstor_common /root/gridcell_rpm/
	    	mkdir -p /home/fractalio/integralstor/gridcell_soft_updaters/gridcell_code_back/$branchcmmn
	    	yes | cp -rf /tmp/integralstor_common.tar.gz /home/fractalio/integralstor/gridcell_soft_updaters/gridcell_code_back/$branchcmmn
	elif [[ $input2 == "tag" ]] ; then
	    	cd /tmp/integralstor_common
	    echo "Available Git 'tags' are:"
	    echo
	    	git tag -l
	    echo
	    read -p "Enter the required tag from above: " tagcmmn	# change the branch name as per the requirement
	    	cd /tmp/integralstor_common/
	    	git checkout tags/$tagcmmn 
	    	touch /tmp/integralstor_common/version
	    echo "$tagcmmn" > /tmp/integralstor_common/version	
	    echo "Downloaded from Tag : $tagcmmn"
	   	#git tag
	    	cd /tmp
		rm -rf /tmp/integralstor_common/.git*
	    	tar czf integralstor_common.tar.gz integralstor_common/ 		# creating zip file of integralstor_common
		yes | cp -r integralstor_common /root/gridcell_rpm/
	    	mkdir -p /home/fractalio/integralstor/gridcell_soft_updaters/gridcell_code_back/$tagcmmn
	    	yes | cp -rf /tmp/integralstor_common.tar.gz /home/fractalio/integralstor/gridcell_soft_updaters/gridcell_code_back/$tagcmmn
	else
		"Go back and enter appropriate input."
	fi
	echo "You are in 'integralstor_gridcell' now. To pull from any branch, enter 'branch' else enter 'tag'"
	read input3
	if [[ $input3 == "branch" ]] ; then
	    	cd /tmp/integralstor_gridcell
	    echo "Available Git 'branches' are:"
	    echo
	    	git branch -a
	    echo
	    read -p "Enter the required 'branch' from above : " branchgrid # change the branch name as per the requirement
	    echo
	    	git checkout $branchgrid
	    	touch /tmp/integralstor_gridcell/version
		#yes | cp /var/www/html/netboot/distros/centos/6.6/x86_64/integralstor_gridcell/v1.0/create_default_zfs_pools.sh /tmp/integralstor_gridcell/install/scripts
	    echo "$branchgrid" > /tmp/integralstor_gridcell/version
	    sed -i "s/version=1.0/version=$branchgrid/g"  /tmp/integralstor_gridcell/install/ks/ksgridcell.cfg
	    echo "Downloaded from Branch:"
	    	git branch
	    	cd /tmp
		rm -rf /tmp/integralstor_gridcell/.git*
	    	tar czf integralstor_gridcell.tar.gz integralstor_gridcell/ 		# creating zip file of integralstor_common
		yes | cp -r integralstor_gridcell /root/gridcell_rpm/
	    	mkdir -p /home/fractalio/integralstor/gridcell_soft_updaters/gridcell_code_back/$branchgrid
	    	yes | cp -rf /tmp/integralstor_gridcell.tar.gz /home/fractalio/integralstor/gridcell_soft_updaters/gridcell_code_back/$branchgrid
	elif [[ $input3 == "tag" ]] ; then
	    	cd /tmp/integralstor_gridcell
	    echo "Available Git 'tags' are :"
	    	git tag -l
	    echo
	    read -p "Enter the required 'tag' from above : " taggrid	# change the branch name as per the requirement
	    	cd /tmp/integralstor_gridcell/
	    	git checkout tags/$taggrid
	    	touch /tmp/integralstor_gridcell/version
	    sed -i "s/version=1.0/version=$taggrid/g"  /tmp/integralstor_gridcell/install/ks/ksgridcell.cfg
		#yes | cp /var/www/html/netboot/distros/centos/6.6/x86_64/integralstor_gridcell/v1.0/create_default_zfs_pools.sh /tmp/integralstor_gridcell/install/scripts
	    echo "$taggrid" > /tmp/integralstor_gridcell/version	
	    echo "Downloaded from Tag: $taggrid"
	    	#git tag
	    	cd /tmp
		rm -rf /tmp/integralstor_gridcell/.git*
	    	tar czf integralstor_gridcell.tar.gz integralstor_gridcell/ 		# creating zip file of integralstor_common
		yes | cp -r integralstor_gridcell /root/gridcell_rpm/
	    	mkdir -p /home/fractalio/integralstor/gridcell_soft_updaters/gridcell_code_back/$taggrid
	    	yes | cp -rf /tmp/integralstor_gridcell.tar.gz /home/fractalio/integralstor/gridcell_soft_updaters/gridcell_code_back/$taggrid
	else
		"Go back and enter appropriate input."
	fi

    elif [[ $input1 == "n" || $input1 == "N" || $input1 == "no" || $input1 == "No" || $input1 == "NO" || $input1 == "" || $input1 == " " ]] ; then

	cd /tmp/integralstor_common
        TAGCMMN=$(git describe $(git rev-list --tags --max-count=1))
	git checkout tags/$TAGCMMN
	touch /tmp/integralstor_common/version
	echo "$TAGCMMN" > /tmp/integralstor_common/version	
	echo "Downloaded from Tag: $TAGCMMN"
	#git tag
    	cd /tmp
	rm -rf /tmp/integralstor_common/.git*
    	tar czf integralstor_common.tar.gz integralstor_common/ 		# creating zip file of integralstor_common
	yes | cp -r integralstor_common /root/gridcell_rpm/
    	mkdir -p /home/fractalio/integralstor/gridcell_soft_updaters/gridcell_code_back/$TAGCMMN
    	yes | cp -rf /tmp/integralstor_common.tar.gz /home/fractalio/integralstor/gridcell_soft_updaters/gridcell_code_back/$TAGCMMN
	
	cd /tmp/integralstor_gridcell
        TAGGRID=$(git describe $(git rev-list --tags --max-count=1))
	git checkout tags/$TAGGRID
	touch /tmp/integralstor_gridcell/version
	echo "$TAGGRID" > /tmp/integralstor_gridcell/version	
	sed -i "s/version=1.0/version=$TAGGRID/g"  /tmp/integralstor_gridcell/install/ks/ksgridcell.cfg
	echo "Downloaded from Tag: $TAGGRID"
	#git tag
    	cd /tmp
	rm -rf /tmp/integralstor_gridcell/.git*
    	tar czf integralstor_gridcell.tar.gz integralstor_gridcell/ 		# creating zip file of integralstor_common
	yes | cp -r integralstor_gridcell /root/gridcell_rpm/
    	mkdir -p /home/fractalio/integralstor/gridcell_soft_updaters/gridcell_code_back/$TAGGRID
    	yes | cp -rf /tmp/integralstor_gridcell.tar.gz /home/fractalio/integralstor/gridcell_soft_updaters/gridcell_code_back/$TAGGRID
    else
	"Go back and enter appropriate input."
    fi
cp -r /tmp/integralstor_common.tar.gz /tmp/integralstor_gridcell.tar.gz /var/www/html/netboot/distros/centos/6.6/x86_64/integralstor_gridcell/v1.0/tar_installs/
