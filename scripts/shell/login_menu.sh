#!/bin/bash

pause(){
  read -p "Press [Enter] key to continue..." key
}
 
configure_networking(){
	#echo "configure networking called"
	python /opt/fractalio/scripts/python/configure_networking.py
}

set_as_primary(){
	#echo "set as primary called"
  ping -c 1 fractalio-pri.fractalio.lan > /dev/null 2> /dev/null
  ret=$?
  if [ $ret != 0 ]
  then
	  python /opt/fractalio/scripts/python/set_node_type.py primary
    pause
  else
    echo 'A primary GRIDCell (with hostname fractalio-pri) seems to already exist in the LAN! A grid cannot have more than one primary.'
    pause
  fi
}

set_as_secondary(){
	#echo "set as secondary called"
  ping -c 1 fractalio-sec.fractalio.lan > /dev/null 2> /dev/null
  ret=$?
  if [ $ret != 0 ]
  then
	  python /opt/fractalio/scripts/python/set_node_type.py secondary
    pause
  else
    echo 'A secondary GRIDCell (with hostname fractalio-sec) seems to already exist in the LAN! A grid cannot have more than one secondary.'
    pause
  fi
}

view_minion_status(){
	echo "view minion status called"
	if [ $HOSTNAME == "fractalio-pri" ]
	then
		/opt/fractalio/scripts/shell/view_minions.sh
   	pause
	fi
}
reset_minion(){
	echo "reset minion called"
	/opt/fractalio/scripts/shell/reset_salt_minion.sh
  pause
}
remove_minions(){
	#echo "remove minions called"
	if [ $HOSTNAME == "fractalio-pri" ]
	then
		python /opt/fractalio/scripts/shell/clear_minions.py
    pause
	fi
}
 

goto_shell() {
	#echo "go to shell called"
	su -l fractalio
        pause
}

do_reboot() {
	#echo "reboot called"
	reboot now
        pause
}


do_shutdown() {
	#echo "do shutdown called"
	shutdown -h now
        pause
}

show_menu() {
  primary=$1
  secondary=$2
	#echo $primary
	#echo $secondary
	clear
	echo "-------------------------------"	
	echo " Fractalio IntegralStore - Menu"
	echo "-------------------------------"
	echo "1. Configure Network Configuration"
	echo "2. View minion status"
	echo "3. Reset minion on this node"
	echo "4. Remove minions"
  echo "5. Reboot"
	echo "6. Shutdown"
  if [ $primary == 1 -o $secondary == 1 ]
  then
    if [ ! -f '/opt/fractalio/first_time_setup_completed' ]
    then
	    echo "7. Initiate the first time grid setup"
    fi
  else
	  echo "7. Convert this GRIDCell to a primary"
	  echo "8. Convert this GRIDCell to a secondary"
  fi
}

read_input(){
  primary=$1
  secondary=$2
	#echo $primary
	#echo $secondary
	local input 
  if [ $primary == 1 -o $secondary == 1 ]
  then
    if [ -f '/opt/fractalio/first_time_setup_completed' ]
    then
	    read -p "Enter choice [1 - 6] " input 
	    case $input in
    		1) configure_networking ;;
    		2) view_minion_status ;;
    		3) reset_minion ;;
    		4) remove_minions ;;
    		5) do_reboot;;
    		6) do_shutdown;;
    		*)  echo "Not a Valid INPUT" && sleep 2
    	esac
    else
	    read -p "Enter choice [1 - 7] " input 
	    case $input in
    		1) configure_networking ;;
    		2) view_minion_status ;;
    		3) reset_minion ;;
    		4) remove_minions ;;
    		5) do_reboot;;
    		6) do_shutdown;;
    		7) first_time_setup;;
    		*)  echo "Not a Valid INPUT" && sleep 2
    	esac
    fi
  else
   read -p "Enter choice [1 - 8] " input 
   case $input in
  		1) configure_networking ;;
  		2) view_minion_status ;;
  		3) reset_minion ;;
   		4) remove_minions ;;
   		5) do_reboot;;
   		6) do_shutdown;;
   		7) set_as_primary;;
   		8) set_as_secondary;;
   		*)  echo "Not a Valid INPUT" && sleep 2
    	esac
  fi
}
 
trap '' SIGINT SIGQUIT SIGTSTP
 
while true
do
	echo "fractal menu is started" > /tmp/out
  primary=0
  secondary=0
	if [ $HOSTNAME == "fractalio-pri" ]
	then
		primary=1
	fi
	if [ $HOSTNAME == "fractalio-sec" ]
	then
		secondary=1
	fi
	#echo $primary
	#echo $secondary
	show_menu $primary $secondary
	read_input $primary $secondary
	echo "fractal menu is stoped" >> /tmp/out
done
