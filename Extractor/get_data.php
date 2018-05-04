<?php

function sensor_data_as_json($station, $sensor, $date_query){
  global $date_query, $db_handle;
  $values = "time, reading";
  $db_query = "SELECT " . $values . " FROM " . $sensor .
              " WHERE station = " . $station .
              " AND " . $date_query;

  $db_result = mysqli_query($db_handle, $db_query);
  if (!$db_result)
  {
      print "Error: Unable to query table." . $sensor . "<br>";
      exit;
  }
  // Define the table columns, i.e. what the x and y data actually are.
  $table = array();
  $table['cols'] = array(
      array('label' => 'Time',  'type' => 'datetime'),
      array('label' => 'Reading', 'type' => 'number')
  );
  $rows = array();
  // This populates the rows, i.e. the actual x and y data.
  while($r = mysqli_fetch_assoc($db_result))
  {
      $temp = array();
      /* The MySQL datetime format needs to be broken down and reformatted
         for Google Charts.  The Javascript API months start at 0, whereas
          MySQL starts at 1! */
      $date1 = strtotime($r['time'] . " -1 Month");
      $date2 = "Date(" . date("Y,m,d,H,i,s", $date1) . ")";
      $temp[] = array('v' => $date2);
      $temp[] = array('v' => $r['reading']);
      $rows[] = array('c' => $temp);
  }
  $table['rows'] = $rows;
  $json_data = json_encode($table);
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
  $sensor = (isset($_REQUEST["sensor"]) ? $_REQUEST["sensor"]: "water_temperature");
  $days = (isset($_REQUEST["days"]) ? $_REQUEST["days"]: "5");
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
    echo sensor_data_as_json($station, $sensor, $date_query);
?>
