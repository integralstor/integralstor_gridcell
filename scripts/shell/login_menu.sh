#!/bin/bash

pause(){
  read -p "Press [Enter] key to continue..." key
}
 
gluster_restart(){
  read -p "Press [Enter] key to restart . . . Note this could cause a intermediate data disruption to all clients. " key
  service glusterd restart
}

set_cpu_cores(){
  echo
  TOTAL_CPU=$(nproc --all)
  echo "Total CPU(s):" $TOTAL_CPU
  onlin=$(getconf _NPROCESSORS_ONLN)
  echo "Online cores are:" $onlin
  echo
  read -p "Enter the number of cores to be disabled from [minimum 2][press 1 to reset]. " ip
  sh /opt/integralstor/integralstor_common/scripts/shell/cpu_core_dis.sh $ip
  sleep 1
}

configure_networking(){
  #echo "configure networking called"
  python /opt/integralstor/integralstor_gridcell/scripts/python/configure_networking.py
}

set_as_primary(){
  #echo "set as primary called"
  ping -c 1 gridcell-pri.integralstor.lan > /dev/null 2> /dev/null
  ret=$?
  if [ $ret != 0 ]
  then
    python /opt/integralstor/integralstor_gridcell/scripts/python/set_node_type.py primary
    pause
  else
    echo 'A primary GRIDCell (with hostname gridcell-pri) seems to already exist in the LAN! A grid cannot have more than one primary.'
    pause
  fi
}

first_time_setup(){
  hn=`hostname`
  if [ $hn == "gridcell-pri" ]
  then
    /opt/integralstor/integralstor_gridcell/scripts/python/first_time_setup.py
    pause
  else
    echo 'This functionality can only initiated from the primary GRIDCell.'
  fi
}

view_node_status(){
  python /opt/integralstor/integralstor_gridcell/scripts/python/display_node_status.py
  pause
}
view_node_config(){
  python /opt/integralstor/integralstor_gridcell/scripts/python/display_node_config.py
  pause
}

set_as_secondary(){
  #echo "set as secondary called"
  ping -c 1 gridcell-sec.integralstor.lan > /dev/null 2> /dev/null
  ret=$?
  if [ $ret != 0 ]
  then
    python /opt/integralstor/integralstor_gridcell/scripts/python/set_node_type.py secondary
    pause
  else
    echo 'A secondary GRIDCell (with hostname gridcell-sec) seems to already exist in the LAN! A grid cannot have more than one secondary.'
    pause
  fi
}

salt_ping(){
  if [ $primary == 0 -a $secondary == 0 ]
  then
    echo 'This functionality can only done on a primary or secondary GRIDCell'
    pause
  else
    salt '*' test.ping
    pause
  fi
}
view_minion_status(){
  hn=`hostname`
  echo $hn
  if [ $hn == "gridcell-pri" ]
  then
    /opt/integralstor/integralstor_gridcell/scripts/shell/view_minions.sh
    pause
  else
    echo 'This functionality can only done on a primary GRIDCell'
    pause
  fi
}

reset_minion(){
  /opt/integralstor/integralstor_gridcell/scripts/shell/reset_salt_minion.sh
  pause
}

remove_minions(){
  hn=`hostname`
  if [ $hn == "gridcell-pri" ]
  then
    python /opt/integralstor/integralstor_gridcell/scripts/python/clear_minions.py
    pause
  else
    echo 'This functionality can only done on a primary GRIDCell'
    pause
  fi
}

 

goto_shell() {
  su -l integralstor
  pause
}

do_reboot() {
  reboot now
  pause
}


do_shutdown() {
  shutdown -h now
  pause
}

show_menu() {
  primary=$1
  secondary=$2
  clear
  echo "-------------------------------"	
  echo " IntegralStor GRIDCell - Menu"
  echo "-------------------------------"
  echo "1. Configure Network Configuration"
  echo "2. Reboot"
  echo "3. Shutdown"
  echo "4. View GRIDCell configuration"
  echo "5. View GRIDCell process status"
  if [ $primary == 0 -a $secondary == 0 ]
  then
    #Normal node
    echo "6. Convert this GRIDCell to a primary"
    echo "7. Convert this GRIDCell to a secondary"
  fi
  if [ $primary == 1 ]
  then
    if [ ! -f '/opt/integralstor/integralstor_gridcell/first_time_setup_completed' ]
    then
      echo "6. View minion status"
      echo "7. Initiate the first time grid setup"
      echo "8. View GRIDCell salt responses"
    else
      echo "6. View minion status"
      echo "8. View GRIDCell salt responses"
    fi
  fi
  if [ $secondary == 1 ]
  then
    echo "6. View minion status"
    echo "8. View GRIDCell salt responses"
  fi
  echo "9. Restart GLUSTER Service"
  echo "10.Modify CPU cores"
}

read_input(){
  primary=$1
  secondary=$2
  local input 
  if [ $primary == 0 -a $secondary == 0 ]
  then
    # Normal node
    read -p "Enter choice " input 
    case $input in
      1) configure_networking ;;
      2) do_reboot;;
      3) do_shutdown;;
      4) view_node_config;;
      5) view_node_status;;
      6) set_as_primary;;
      7) set_as_secondary;;
      9) gluster_restart;;
      10)set_cpu_cores;;
      *)  echo "Not a Valid INPUT" && sleep 2
    esac
  fi
  if [ $primary == 1  ]
  then
    #Primary node
    if [ ! -f '/opt/integralstor/integralstor_gridcell/first_time_setup_completed' ]
    then
        #Primary node with first time setup complete
        read -p "Enter choice " input 
        case $input in
        1) configure_networking ;;
        2) do_reboot;;
        3) do_shutdown;;
        4) view_node_config;;
        5) view_node_status;;
        6) view_minion_status ;;
        7) first_time_setup;;
	8) salt_ping;;
        *)  echo "Not a Valid INPUT" && sleep 2
    	esac
    else
        read -p "Enter choice " input 
        case $input in
        1) configure_networking ;;
        2) do_reboot;;
        3) do_shutdown;;
        4) view_node_config;;
        5) view_node_status;;
        6) view_minion_status ;;
	8) salt_ping;;
        9) gluster_restart;;
        10)set_cpu_cores;;
        *)  echo "Not a Valid INPUT" && sleep 2
    	esac
    fi
  fi
  if [ $secondary == 1 ]
  then
    #Secondary node
      read -p "Enter choice " input 
      case $input in
      1) configure_networking ;;
      2) do_reboot;;
      3) do_shutdown;;
      4) view_node_config;;
      5) view_node_status;;
      6) view_minion_status ;;
      8) salt_ping;;
      9) gluster_restart;;
      10)set_cpu_cores;;
      *)  echo "Not a Valid INPUT" && sleep 2
    	esac
  fi
}
 
trap '' SIGINT SIGQUIT SIGTSTP
 
while true
do
  echo "The Integralstor menu has started" > /tmp/out
  primary=0
  secondary=0
  hn=`hostname`
  if [ $hn == "gridcell-pri" ]
  then
    primary=1
  fi
  if [ $hn == "gridcell-sec" ]
  then
    secondary=1
  fi
  show_menu $primary $secondary
  read_input $primary $secondary
  echo "The Integralstor menu has stopped" >> /tmp/out
done
