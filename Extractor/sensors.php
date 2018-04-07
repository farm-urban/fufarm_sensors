<?php
  error_reporting(E_ALL);
  ini_set('display_errors', 'On');
  date_default_timezone_set('Europe/London');

//  ,-----------------------------------------------------------------------,
//  | Web script to display aquaponic sensor information from a database.   |
//  |                                                                       |
//  | Licensing ?                                                           |
//  |                                                                       |
//  | Darren Faulke (VEC).                                                  |
//  '-----------------------------------------------------------------------'
    $DB_HOST = "localhost";
    $DB_USER = "foo";
    $DB_PASS = "password";
    $DB_NAME = "farmurban";

    //  ,-----------------------------------------------------------,
    //  | Variables.                                                |
    //  |                                                           |
    //  | These are really for future use in being able to modify   |
    //  | the charts interactively by modifying database queries.   |
    //  '-----------------------------------------------------------'

    //  ,-------------------------------,
    //  | Define the display period.    |
    //  '-------------------------------'
    $days = (isset($_REQUEST["days"]) ? $_REQUEST["days"]: "5");
    $end_date = "NOW()";
    $start_date = "SUBDATE(NOW(), " . $days . ")";
    $date_query = " time BETWEEN " . $start_date .
                  " AND " . $end_date;

    $station = (isset($_REQUEST["station"]) ? $_REQUEST["station"]: "1");
    //  ,-------------------------------,
    //  | Charts.                       |
    //  '-------------------------------'
    $chart_height = 300; // Google API doesn't like this!
    $chart_width = 400;  // ""

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

//  ,-----------------------------------------------------------------------,
//  | This section creates JSON formatted tables for the Google Charts API. |
//  |                                                                       |
//  | It would be better to only draw 1 or 2 charts on a page but have the  |
//  | sensors and stations selectable. This would save resources and tidy   |
//  | up the next section of code. For now, a number of pre-defined charts  |
//  | are displayed to demonstrate the capabilities.                        |
//  '-----------------------------------------------------------------------'

//  ,-----------------------------------------------------------,
//  | The following charts are deined here:                     |
//  |                                                           |
//  |   Station 1                                               |
//  |   Temperatures: Barometer (MPL3115A2),                    |
//  |                 Humidity sensor (Si7006-A20),             |
//  |                 Liquid temperature (DS18B20).             |
//  |   Light levels: Channel 0 (LTR-329ALS-01),                |
//  |                 Channel 1 (LTR-329ALS-01).                |
//  |   Humidity:     Air (MPL3115A2).                          |
//  |                                                           |
//  |   Station 2                                               |
//  |   Temperatures: Barometer (MPL3115A2),                    |
//  |                 Humidity sensor (Si7006-A20),             |
//  |   Light levels: Channel 0 (LTR-329ALS-01),                |
//  |                 Channel 1 (LTR-329ALS-01).                |
//  |   Humidity:     Air (MPL3115A2).                          |
//  |                                                           |
//  '-----------------------------------------------------------'

//  ,-----------------------------------------------------------,
//  | A query is made to return specific sensor data for the    |
//  | station within the specified time interval. A new query   |
//  | needs to be made for each data set. Multiple passes of a  |
//  | full table cannot be made because the query pointer can't |
//  | be reset for each pass after the first (afaik).           |
//  | Once the data is transferred to the chart arrays, the     |
//  | memory should be freed up.                                |
//  '-----------------------------------------------------------'
    function sensor_data_as_json($args){
      global $date_query, $db_handle;
      $station = $args['station'];
      $sensor = $args['sensor'];
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
          array('label' => $args['data_label'], 'type' => 'number')
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

/* jmht
//  ,-----------------------------------------------------------,
//  | This is an attempt to use database JOIN and UNION queries |
//  | to consolidate data from multiple tables so that readings |
//  | from different sensors can be viewed on the same chart.   |
//  |                                                           |
//  | MySQL does not have an OUTER JOIN, which is what is       |
//  | needed, but apparently a UNION can be used to simulate an |
//  | OUTER JOIN.                                               |
//  '-----------------------------------------------------------'

    //  ,-----------------------------------------------------------,
    //  |           *** Station 1 combined temperatures ***         |
    //  '-----------------------------------------------------------'
    $station = 1;
    $sensor1 = "barometer_temperature";
    $sensor2 = "humidity_temperature";
    $dates   = "time BETWEEN " . $start_date .
               " AND " . $end_date;

    //  ,-------------------------------------------------------,
    //  | It is a little easier to practice queries directly in |
    //  | MySQL so this definition is pasted in from MySQl for  |
    //  | anything that seems to work on the command line.      |
    //  '-------------------------------------------------------'
    //$db_query = "SELECT a.time, a.reading, b.reading FROM barometer_temperature AS a LEFT JOIN humidity_temperature AS b ON a.time = b.time UNION ALL SELECT b.time, a.reading, b.reading FROM barometer_temperature AS a RIGHT JOIN humidity_temperature AS b ON a.time = b.time WHERE a.reading is NULL AND ( a.station = 1 OR b.station = 1)";
    //$db_query = "SELECT a.time, a.reading, b.reading FROM barometer_temperature AS a LEFT JOIN humidity_temperature AS b ON a.time = b.time UNION ALL SELECT b.time, a.reading, b.reading FROM barometer_temperature AS a RIGHT JOIN humidity_temperature AS b ON a.time = b.time WHERE a.reading is NULL AND ( a.station = 1 OR b.station = 1) AND ( a.time BETWEEN SUBDATE(NOW(), 2) AND NOW() OR b.time BETWEEN SUBDATE(NOW(), 2) AND NOW())";
    //$db_query = "SELECT a.time, a.reading, b.reading FROM barometer_temperature AS a RIGHT JOIN humidity_temperature AS b ON a.time = b.time UNION ALL SELECT b.time, a.reading, b.reading FROM barometer_temperature AS a LEFT JOIN humidity_temperature AS b ON a.time = b.time WHERE a.reading is NULL AND ( a.station = 1 OR b.station = 1) AND ( a.time BETWEEN SUBDATE(NOW(), 1) AND NOW() OR b.time BETWEEN SUBDATE(NOW(), 1) AND NOW())";
    //$db_query = "SELECT a.time, a.reading, b.reading FROM barometer_temperature AS a LEFT JOIN humidity_temperature AS b ON a.time = b.time UNION ALL SELECT b.time, a.reading, b.reading FROM barometer_temperature AS a RIGHT JOIN humidity_temperature AS b ON a.time = b.time WHERE a.reading is NULL AND ( a.station = 1 OR b.station = 1) AND ( a.time BETWEEN SUBDATE(NOW(), 1) AND NOW() OR b.time BETWEEN SUBDATE(NOW(), 1) AND NOW()) ORDER BY time";
    //$db_query = "SELECT a.time, a.reading, b.reading FROM barometer_temperature AS a LEFT JOIN humidity_temperature AS b ON a.time = b.time UNION ALL SELECT b.time, a.reading, b.reading FROM barometer_temperature AS a RIGHT JOIN humidity_temperature AS b ON a.time = b.time WHERE a.reading is NULL AND ( a.station = 1 AND b.station = 1) AND ( a.time BETWEEN SUBDATE(NOW(), 1) AND NOW() OR b.time BETWEEN SUBDATE(NOW(), 1) AND NOW()) ORDER BY time";
    //$db_query = "SELECT a.time, a.reading, b.reading FROM barometer_temperature AS a LEFT JOIN humidity_temperature AS b ON a.time = b.time UNION ALL SELECT b.time, a.reading, b.reading FROM barometer_temperature AS a RIGHT JOIN humidity_temperature AS b ON a.time = b.time WHERE a.reading is NULL AND ( a.station = 1 AND b.station = 1) AND ( a.time BETWEEN SUBDATE(NOW(), 1) AND NOW() OR b.time BETWEEN SUBDATE(NOW(), 1) AND NOW())";
    //$db_query = "SELECT a.time, a.reading, b.reading FROM barometer_temperature AS a LEFT JOIN humidity_temperature AS b ON a.time = b.time WHERE a.station = 1 UNION ALL SELECT b.time, a.reading, b.reading FROM humidity_temperature AS b RIGHT JOIN barometer_temperature AS a ON a.time = b.time WHERE b.station = 1 ORDER BY time";
    //$db_query = "SELECT a.time, barometer_temperature.reading, humidity_temperature.reading FROM (reading FROM barometer_temperature WHERE station = 1 UNION SELECT reading FROM humidity_temperature WHERE station = 1) AS a LEFT JOIN barometer_temperature ON a.time = barometer_temperature.time LEFT JOIN humidity_temperature ON a.time = humidity_temperature.time ORDER BY time";

    //  ,-------------------------------------------------------,
    //  | This just dumps the query to check the formatting.    |
    //  '-------------------------------------------------------'
    //    echo $db_query;

    $db_query = "SELECT a.time, " . $sensor1 . ".reading, " . $sensor2 . ".reading " .
                "FROM (" .
                "SELECT time FROM " . $sensor1 . " " .
                "WHERE " . $dates . " " .
                "UNION " .
                "SELECT time FROM ". $sensor2 . " " .
                "WHERE " . $dates . " " .
                ") a " .
                "LEFT JOIN " . $sensor1 . " " . "ON a.time = " . $sensor1 . ".time " .
                "AND " . $sensor1 . ".station = " . $station . " " .
                "LEFT JOIN " . $sensor2 . " " . "ON a.time = " . $sensor2 . ".time " .
                "AND " . $sensor2 . ".station =" . $station . " " .
                "ORDER BY time";

    //echo $db_query;

    $db_result = mysqli_query($db_handle, $db_query);

    if (!$db_result)
    {
        print "Error: Unable to query table." . $sensor . "<br>";
        exit;
    }

    $table = array();
    $table['cols'] = array(
        array('label' => 'Time',      'type' => 'datetime'),
        array('label' => 'Barometer', 'type' => 'number'),
        array('label' => 'Humidity',  'type' => 'number')
    );

    $rows = array();

    while($r = mysqli_fetch_row($db_result))
    {
        $temp = array();
        $date1 = strtotime($r[0] . " -1 Month");
        $date2 = "Date(" . date("Y,m,d,H,i,s", $date1) . ")";
        $temp[] = array('v' => $date2);
        $temp[] = array('v' => $r[1]);
        $temp[] = array('v' => $r[2]);
        $rows[] = array('c' => $temp);
    }
    $table['rows'] = $rows;

    $json_all_temp_1 = json_encode($table);
    mysqli_free_result($db_result);
    // echo $json_all_temp_1;


    //  ,-----------------------------------------------------------,
    //  |           *** Station 1 Light levels ***                  |
    //  '-----------------------------------------------------------'
    $station = 1;
    $sensor1 = "ambient_light_0";
    $sensor2 = "ambient_light_1";
    $dates   = "time BETWEEN " . $start_date .
               " AND " . $end_date;

    $db_query = "SELECT a.time, " . $sensor1 . ".reading, " . $sensor2 . ".reading " .
                "FROM (" .
                "SELECT time FROM " . $sensor1 . " " .
                "WHERE " . $dates . " " .
                "UNION " .
                "SELECT time FROM ". $sensor2 . " " .
                "WHERE " . $dates . " " .
                ") a " .
                "LEFT JOIN " . $sensor1 . " " . "ON a.time = " . $sensor1 . ".time " .
                "AND " . $sensor1 . ".station = " . $station . " " .
                "LEFT JOIN " . $sensor2 . " " . "ON a.time = " . $sensor2 . ".time " .
                "AND " . $sensor2 . ".station =" . $station . " " .
                "ORDER BY time";

    //echo $db_query;

    $db_result = mysqli_query($db_handle, $db_query);

    if (!$db_result)
    {
        print "Error: Unable to query table." . $sensor . "<br>";
        exit;
    }

    $table = array();
    $table['cols'] = array(
        array('label' => 'Time',      'type' => 'datetime'),
        array('label' => 'Channel 0', 'type' => 'number'),
        array('label' => 'Channel 1', 'type' => 'number')
    );

    $rows = array();

    while($r = mysqli_fetch_row($db_result))
    {
        $temp = array();
        $date1 = strtotime($r[0] . " -1 Month");
        $date2 = "Date(" . date("Y,m,d,H,i,s", $date1) . ")";
        $temp[] = array('v' => $date2);
        $temp[] = array('v' => $r[1]);
        $temp[] = array('v' => $r[2]);
        $rows[] = array('c' => $temp);
    }
    $table['rows'] = $rows;

    $json_all_light_1 = json_encode($table);
    mysqli_free_result($db_result);
    // echo $json_all_light_1;



    // ,--------------------------------------------------------,
    // | Free up the MySQL connector resources.                 |
    // '--------------------------------------------------------'
    mysqli_close($db_handle);

jmht  */
$args = array('sensor' => 'water_temperature',
              'station' => $station,
              'data_label' => 'Temp');
$json_wat_temp_1 = sensor_data_as_json($args);

$args = array('sensor' => 'barometer_temperature',
              'station' => $station,
              'data_label' => 'Barometer');
$json_bar_temp_1 = sensor_data_as_json($args);

$args = array('sensor' => 'humidity_temperature',
              'station' => $station,
              'data_label' => 'Humidity');
$json_hum_temp_1 = sensor_data_as_json($args);

$args = array('sensor' => 'ambient_light_0',
              'station' => $station,
              'data_label' => 'Channel 0');
$json_light_0_1 = sensor_data_as_json($args);

$args = array('sensor' => 'ambient_light_1',
              'station' => $station,
              'data_label' => 'Channel 1');
$json_light_1_1 = sensor_data_as_json($args);

$args = array('sensor' => 'humidity_humidity',
              'station' => $station,
              'data_label' => 'Humidity');
$json_humidity_1 = sensor_data_as_json($args);
?>


<!--//  ,-------------------------------------------------------------------,   -->
<!--//  | This section sets up the Google Charts using the JSON formatted   |   -->
<!--//  | tables. There may be better ways of creating multiple charts      |   -->
<!--//  | based on user interaction (There is provision in the API but it   |   -->
<!--//  | is beyond the scope of this project).                             |   -->
<!--//  '-------------------------------------------------------------------'   -->
<html>
    <head>
        <script type="text/javascript" src="https://www.gstatic.com/charts/loader.js"></script>
        <script type="text/javascript" src="//ajax.googleapis.com/ajax/libs/jquery/1.10.2/jquery.min.js"></script>
        <script type="text/javascript">


<!--//  ,-----------------------------------------------------------,   -->
<!--//  | Material style charts - newer but limited customisation.  |   -->
<!--//  '-----------------------------------------------------------'   -->
        google.charts.load('current', {'packages':['line']});

<!--//  ,-----------------------------------------------------------,   -->
<!--//  | Classic style charts - more customisations but longevity? |   -->
<!--//  '-----------------------------------------------------------'   -->
        google.charts.load('current', {'packages':['corechart']});

<!--//  ,-------------------------------------------------------,   -->
<!--//  | Callback functions for the sensor charts.             |   -->
<!--//  '-------------------------------------------------------'   -->
        google.charts.setOnLoadCallback(water_temp_station_1);
        google.charts.setOnLoadCallback(barometer_temp_station_1);
        google.charts.setOnLoadCallback(humidity_temp_station_1);
        google.charts.setOnLoadCallback(light_channel0_station_1);
        google.charts.setOnLoadCallback(light_channel1_station_1);
        google.charts.setOnLoadCallback(humidity_station_1);
<!--//  ,-------------------------------------------------------,   -->
<!--//  | Attempts to merge database tables to show multiple    |   -->
<!--//  | data curves on a single chart.                        |   -->
<!--//  '-------------------------------------------------------'   -->
        // google.charts.setOnLoadCallback(all_temp_station_1);
        // google.charts.setOnLoadCallback(all_light_station_1);

        function water_temp_station_1()
        {
            var data = new google.visualization.DataTable(<?=$json_wat_temp_1?>);
            var options =
            {
                title: "Water temperature for station 1 (°C)",
                legend: { position: "right" },
                vAxis:  { format: "##.#"  },
                hAxis:  { format: "EEEE HH:mm" }
            };
            var chart = new google.visualization.LineChart(document.getElementById('water_temp_1'));
            chart.draw(data, options);
        }

        function barometer_temp_station_1()
        {
            var data = new google.visualization.DataTable(<?=$json_bar_temp_1?>);
            var options =
            {
                theme: "material",
                title: "Barometer temperature for station 1 (°C)",
                legend: "none",
                vAxis:  { format: "##.#" },
                hAxis:  { format: "EEEE HH:mm",
                          gridlines: {count: 12}}
            };
            var chart = new google.visualization.LineChart(document.getElementById('bar_temp_1'));
            chart.draw(data, options);
        }

        function humidity_temp_station_1()
        {
            var data = new google.visualization.DataTable(<?=$json_hum_temp_1?>);
            var options =
            {
                chart:
                {
                    title: "Humidity temperature for station 1 (°C)"
                },
                vAxis:
                {
                    format: "##.#"
                },
                hAxis:
                {
                    <!--format: "HH:mm:ss"-->
                    format: "dd/MM/yyyy HH:mm:ss"
                    <!--format: "EEEE HH:mm"-->
                }
            };
            var chart = new google.charts.Line(document.getElementById('hum_temp_1'));
            chart.draw(data, google.charts.Line.convertOptions(options));
        }

        function light_channel0_station_1()
        {
            var data = new google.visualization.DataTable(<?=$json_light_0_1?>);
            var options =
            {
                theme: "material",
                title: "Ambient light (channel 0) for station 1 (lx)",
                legend: { position: "right" },
                vAxis:  { format: "##.#"  },
                hAxis:  { format: "dd/MM/yyyy HH:mm",
                          gridlines: {count: 8}}
            };
            var chart = new google.visualization.LineChart(document.getElementById('light_0_1'));
            chart.draw(data, options);
        }

        function light_channel1_station_1()
        {
            var data = new google.visualization.DataTable(<?=$json_light_1_1?>);
            var options =
            {
                theme: "material",
                title: "Ambient light (channel 1) for station 1 (lx)",
                legend: { position: "right" },
                vAxis:  { format: "##.#"  },
                hAxis:  { format: "EEEE HH:mm" }
            };
            var chart = new google.visualization.LineChart(document.getElementById('light_1_1'));
            chart.draw(data, options);
        }

        function humidity_station_1()
        {
            var data = new google.visualization.DataTable(<?=$json_humidity_1?>);
            var options =
            {
                theme: "material",
                title: "Humidity for station 1 (%)",
                legend: { position: "right" },
                vAxis:  { format: "##.#"  },
                hAxis:  { format: "EEEE HH:mm" }
            };
            var chart = new google.visualization.LineChart(document.getElementById('humidity_1'));
            chart.draw(data, options);
        }

/* jmht
        function all_temp_station_1()
        {
            var data = new google.visualization.DataTable(<?=$json_all_temp_1?>);
            var options =
            {
                theme: "material",
                title: "Temperatures for station 1 (°C)",
                legend: { position: "right" },
                vAxis:  { format: "##.#"  },
                hAxis:  { format: "EEEE HH:mm" },
                interpolateNulls: true
            };
            var chart = new google.visualization.LineChart(document.getElementById('all_temp_1'));
            chart.draw(data, options);
        }

        function all_light_station_1()
        {
            var data = new google.visualization.DataTable(<?=$json_all_light_1?>);
            var options =
            {
                theme: "material",
                title: "Ambient light levels for station 1 (lx)",
                legend: { position: "right" },
                vAxis:  { format: "##.#"  },
                hAxis:  { format: "EEEE HH:mm" },
                interpolateNulls: true
            };
            var chart = new google.visualization.LineChart(document.getElementById('all_light_1'));
            chart.draw(data, options);
        }

        */

    </script>
</head>
<!--//  ,---------------------------------------------------,   -->
<!--//  | This is the HTML section, which handles the page  |   -->
<!--//  | layout and formatting.                            |   -->
<!--//  | This would idealy be the page that is called by   |   -->
<!--//  | the browser and all other sections are called     |   -->
<!--//  | from here.                                        |   -->
<!--//  '---------------------------------------------------'   -->

<body>
    <p>Classic style API.</p>
    <div id="water_temp_1" style="width: 600px; height: 400px"></div>
    <p>Classic style API using a Material theme.</p>
    <div id="bar_temp_1"   style="width: 600px; height: 400px"></div>
    <p>Material API.</p>
    <div id="hum_temp_1"   style="width: 600px; height: 400px"></div>
    <p>Classic style API using a Material theme.</p>
    <div id="light_0_1"    style="width: 600px; height: 400px"></div>
    <div id="light_1_1"    style="width: 600px; height: 400px"></div>
    <div id="humidity_1"   style="width: 600px; height: 400px"></div>
<!--
    <div id="all_temp_1"   style="width: 600px; height: 400px"></div>
    <div id="all_light_1"  style="width: 600px; height: 400px"></div>
-->
</body>
</html>
