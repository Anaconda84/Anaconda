<?php
/**
 * Simple example of extending the SQLite3 class and changing the __construct
 * parameters, then using the open method to initialize the DB.
 */
class MyDB extends SQLite3
{
    function __construct()
    {
        $this->open('db/tracker.db');
    }
}

$db = new MyDB();

$hash='ŸâWhÉÅ˜|fÔîæÕ0hOwûÀ';

$stmt = $db->prepare('SELECT ip FROM peers WHERE info_hash=:info_hash');
$stmt->bindValue(':info_hash', $hash, SQLITE3_BLOB);
$result = $stmt->execute();

while($res = $result->fetchArray())
{ 
  echo $res["ip"]."\n";
}
?>