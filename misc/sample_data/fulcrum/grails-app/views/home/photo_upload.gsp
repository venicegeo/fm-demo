<!DOCTYPE html>
<html>
	<title>Fulcrum - Photo Upload</title>
	<head>
		<asset:stylesheet src = "photo_upload.css"/>
	</head>
	<body>
		<h1>Fulcrum - Photo Upload</h1>
		<div class = "container-fluid">
			<div class = "alert alert-info" role = "alert"></div>

			<form>
				<g:each in = "${1..100}">
					  <input type = "file" name = "photo" id = "photo${it}"><br/>
				</g:each>
				<input type = "button" id = "upload" onclick = uploadPhotos() value = "upload">
			</form>

		</div>	

		<script>
			var email = "${raw(grailsApplication.config.email)}";
			var password = "${raw(grailsApplication.config.password)}";
		</script>
		<asset:javascript src = "photo_upload.js"/> 
	</body>
</html>
