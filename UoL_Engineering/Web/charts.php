<?php

//settings  
$server="remotemysql.com:3306";
$username="o0sRSRjnwl";
$password="n4J1tq4yYW";
$database="o0sRSRjnwl";


//Create and check connection
$conn = new mysqli($server, $username, $password, $database);

if (!$conn){
    die("Could not connect: " . mysqli_connect_error);
}


/* Getting demo_viewer table data */
$sql = "SELECT * FROM hydroponic_vertical_farm WHERE date >= (SELECT MAX(date) FROM hydroponic_vertical_farm) - INTERVAL 1 DAY";
$result = mysqli_query($conn, $sql);
$num = mysqli_num_rows($result);

while ($row = mysqli_fetch_assoc($result)) {
       $date[] = $row["date"];
       $D = $row["date"];
       $water_temp[] = $row["water_temp"];
       $W_T = $row["water_temp"];
       $humidity[] = $row["humidity"];
       $H = $row["humidity"];
       $pressure[] = $row["pressure"];
       $P = $row["pressure"];
       $air_temp = $row["air_temp"];
       $A_T = $row["air_temp"];
       $image = $row["image"];
 }

mysqli_close($conn);

?>


<!DOCTYPE html>
<html>
<head>
        <link rel="shortcut icon" href="logo.ico" />
	<title>  Vertical Farm </title>
	<link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap.min.css">
	<script type="text/javascript" src="https://cdnjs.cloudflare.com/ajax/libs/jquery/3.1.1/jquery.js"></script>
	<script src="https://code.highcharts.com/highcharts.js"></script>
        <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
        <style>
	body {
	    text-align: center;
	}
	#water_temp, #humidity, #air_temp  {
	    width: 200px;
	    height: 160px;
	    display: inline-block;
	    margin: 1em;
	}
        </style>
</head>
<body>
    <h1>  Sensor Data  </h1>
    <h2>
    <div id="water_temp"></div>
    <div id="humidity"></div>
    <div id="air_temp"></div>
    </h2>
    <hr>
	<h3> Last Reading: <?php echo $D; ?> ==> <button value="Refresh Page" onClick="window.location.reload();"> Refresh Button </button> </h3>
	<hr>
	<p> <img src="livuni.png" width="300" height="300"> &nbsp;&nbsp; <img src="Lab Logo 2.png" width="250" height="100"> &nbsp;&nbsp;&nbsp;&nbsp; <img src="uf.png" width="100" height="100"> &nbsp;&nbsp; </p>
<script type="text/javascript" src="./src/raphael-2.1.4.min.js"></script>
    <script type="text/javascript" src="./src/justgage.js"></script>
    <script>
	var water_temp;
	document.addEventListener("DOMContentLoaded", function(event) {
	    water_temp = new JustGage({
		id: "water_temp",
		value: <?php echo $W_T; ?>,
		valueFontColor: "blue",
		min: 13,
		max: 30,
		title: "Water Temperature",
		label: "Celsius"
	   });
        });

        var humidity;
        document.addEventListener("DOMContentLoaded", function(event) {
            humidity = new JustGage({
                id: "humidity",
                value: <?php echo $H; ?>,
                valueFontColor: "blue",
                min: 0,
                max: 100,
                title: "Humidity",
                label: "%"
            });
        });

 var air_temp;
        document.addEventListener("DOMContentLoaded", function(event) {
            air_temp = new JustGage({
                id: "air_temp",
                value: <?php echo $A_T; ?>,
                valueFontColor: "blue",
                min: 10,
                max: 40,
                title: "Air Temperature",
                label: "Celsius"
            });
        });


    </script>

<script type="text/javascript">


$(function () { 


    var water_temp = <?php echo json_encode($water_temp, JSON_NUMERIC_CHECK); ?>;
    var date = <?php echo json_encode($date); ?>;

    $('#container').highcharts({
        chart: {
            type: 'line'
        },
        title: {
            text: 'Water Temperature'
        },
        xAxis: {
            title: {
                 text: 'Time'
            },
            categories: date,
            labels: {
                 formatter: function() {
                        return Highcharts.dateFormat('%l%p', Date.parse(this.value +' UTC'));
                 }
            }
        },
        yAxis: {
            title: {
                text: 'Values'
            }
        },
        plotOptions : {
                line : {
                    dataLabels : {
                        enabled : true,
                        lineColor : '#666666',
                        lineWidth : 1
                    },
                enableMouseTracking: true
                }
         },
        series: [{
            type: 'line',
            name: 'Temp',
            data: water_temp
        }]
    });
});


</script>


<div class="container">
	<br/>
	<h2 class="text-center"> water temperature chart (last 24h)</h2>
    <div class="row">
        <div class="col-md-10 col-md-offset-1">
            <div class="panel panel-default">
                <div class="panel-heading">Dashboard</div>
                <div class="panel-body">
                    <div id="container"></div>
                </div>
            </div>
        </div>
    </div>
</div>

<p> <?php echo '<img src="data:image/jpg;base64,'.base64_encode($image) .'" width="300" height="400"/>' ?> </p>

</body>
</html>
