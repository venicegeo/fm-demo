<!DOCTYPE html>
<html>
	<title>Fulcrum Demo</title>
	<head>
		<asset:stylesheet src = "demo.css"/>
	</head>
	<body>
		<h1>Third Party UI</h1>
		<div class = "container-fluid">
			<div class = "map" id = "map"></div>

			<div id = "popup" class = "ol-popup">
				<a href = "#" id = "popup-closer" class = "ol-popup-closer"></a>
				<div id = "popup-content"></div>
			</div>

			<div class = "alert alert-info" role = "alert"></div>
		</div>	

		<script>
			var email = "${raw(grailsApplication.config.email)}";
			var password = "${raw(grailsApplication.config.password)}";
		</script>
		<asset:javascript src = "demo.js"/> 
	</body>
</html>
