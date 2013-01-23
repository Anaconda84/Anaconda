<?php

//$fp = fopen("c:/Tmp/out.txt", "w");
//$mytext = "1111111111111111111";
//$test = fwrite($fp, $mytext);
//fclose($fp); 

class MyDB extends SQLite3
{
    function __construct()
    {
        $this->open('db/tracker.db');
    }
}


// Verify Request //////////////////////////////////////////////////////////////////////////////////

// strip auto-escaped data
if (get_magic_quotes_gpc())
{
	$_GET['info_hash'] = stripslashes($_GET['info_hash']);
}


// 20-bytes - info_hash
// sha-1 hash of torrent metainfo
if (!isset($_GET['info_hash']) || strlen($_GET['info_hash']) != 20) exit;

//echo "Content-Type: text/plain\n\n";
$hash = $_GET['info_hash'];
//echo $hash;
// Handle Request //////////////////////////////////////////////////////////////////////////////////

$db = new MyDB();

$stmt = $db->prepare('SELECT * FROM peers WHERE info_hash=:info_hash');
$stmt->bindValue(':info_hash', $hash, SQLITE3_BLOB);
$result = $stmt->execute();

//$result = $db->query('SELECT ip FROM peers WHERE info_hash=:info_hash');
while($res = $result->fetchArray())
{ 
  echo $res["ip"]."<BR>";
}


?>