$ORIGIN .
$TTL 86400    ; 1 day
fractalio.lan        IN SOA    primary.fractalio.lan. root.fractalio.lan. (
	  		        2011071026 ; serial
       		        	3600       ; refresh (1 hour)
               			1800       ; retry (30 minutes)
              			604800     ; expire (1 week)
              			86400      ; minimum (1 day)
                )
            NS    primary.fractalio.lan.
            NS    secondary.fractalio.lan.
            PTR    fractalio.lan.
$ORIGIN fractalio.lan.
primary          A    10.1.1.4
secondary        A    10.1.1.5
