<?php 
  echo "aaaaa";
  $db = open("db/tracker.db");
  echo "000000"; 
  if (!$db) exit("Basedate file not found!"); 
  echo "11111";
  $res = query($db, "SELECT * FROM peers;"); 
  while ($array = sqlite_fetch_array($res))  
  { 
    echo "11111";
    echo($array); 
  } 
?>