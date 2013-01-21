<?php

	function check_ip_port()
	{
//          echo '1111111';
	  $server = '93.181.221.21';
	  $port = intval('6881');
	  $status = 'unavailable';
	  $timeout = 10;
	  $fp = @fsockopen ($server, $port, $errno, $errstr, $timeout);
	  if ($fp) { return True; } else { return False; }
	}

//echo check_ip_port();
if(check_ip_port()) { echo 'OK'; } else { echo 'ERROR !!!'; }

?>
