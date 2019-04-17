<?php

function sensor_data_as_json($station, $sensor, $date_query, $time_as_int){
  global $date_query, $db_handle;
  $values = "time, reading";
  $db_query = "SELECT " . $values . " FROM " . $sensor .
              " WHERE station = " . $station .
              " AND " . $date_query;

  $db_result = mysqli_query($db_handle, $db_query);
  if (!$db_result)
  {
      print "Error: Unable to find data for query:" . $db_query . "\n";
      exit;
  }
  // Define the table columns, i.e. what the x and y data actually are.
  $gdata = array();
  $gdata['labels'] = array();
  $gdata['series'] = array();
  $gdata['series'][] = array();
  while($r = mysqli_fetch_assoc($db_result))
  {
      if ($time_as_int) {
        $gdata['labels'][] = $i;
      } else {
        $gdata['labels'][] = strtotime($r['time']);
      }
      $gdata['series'][0][] = (float)$r['reading'];
  }
  $json_data = json_encode($gdata);
  // echo $json_data; // Uncomment to dump the entire table
  mysqli_free_result($db_result);
  return $json_data;
}

  error_reporting(E_ALL);
  ini_set('display_errors', 'On');
  date_default_timezone_set('Europe/London');

  // DB variables
  $DB_HOST = "localhost";
  $DB_USER = "foo";
  $DB_PASS = "password";
  $DB_NAME = "farmurban";

  // Get variables from request
  $station = (isset($_REQUEST["station"]) ? $_REQUEST["station"]: "1");
  $sensor = (isset($_REQUEST["sensor"]) ? $_REQUEST["sensor"]: "ambient_light_0");
  $days = (isset($_REQUEST["days"]) ? $_REQUEST["days"]: "5");
  $time_as_int = false;
  if (isset($_REQUEST["time_as_int"])) {
    $time_as_int = true;
  }
  $end_date = "NOW()";
  $start_date = "SUBDATE(NOW(), " . $days . ")";
  $date_query = " time BETWEEN " . $start_date . " AND " . $end_date;

    $db_handle = mysqli_connect($DB_HOST,$DB_USER,$DB_PASS);
    if (!$db_handle)
    {
        print "Error: Unable to connect to server." . "<br>";
        print "Debugging errno: " . mysqli_connect_errno() . "<br>";
        print "Debugging error: " . mysqli_connect_error() . "<br>";
        print "" . "<br>";
        exit;
    //  ,-----------------------------------------------------------,
    //  | is the die function better for capturing errors?          |
    //  | die("Could not connect: " . mysqli_error($db_handle));    |
    //  '-----------------------------------------------------------'
    }
    $db_connect = mysqli_select_db($db_handle, $DB_NAME);
    if (!$db_connect)
    {
        print "Error: Unable to connect to database." . "<br>";
        print "Debugging errno: " . mysqli_connect_db_errno() . "<br>";
        print "Debugging error: " . mysqli_connect_db_error() . "<br>";
        exit;
    }

    header('Content-type: application/json');
    echo sensor_data_as_json($station, $sensor, $date_query, $time_as_int);
?>
