//= require jquery
//= require bootstrap


var authKey;
var form;
var photoKey;
var photoAccessKeys = [];
var records = [];

$(document).ready(
	function() {
		$(".alert").alert();
		getAuthenticationKey();
	}	
);

function getAuthenticationKey() {
	$(".alert").append("Getting user authentication key...");

	$.ajax({
		contentType: "application/json",
		dataType: "json",
		headers: { "Authorization": "Basic " + btoa(email + ":" + password) },
		success: function(data) { 
			$(".alert").append(" Done!<br>");
			authKey = data.user.contexts[0].api_token; 
			getFormDetails();
		},
		url: "https://api.fulcrumapp.com/api/v2/users.json",
	});
}

function getFormDetails() {
	$(".alert").append("Getting form details...");

	$.ajax({
		contentType: "application/json",
		dataType: "json",
		headers: { "X-ApiToken": authKey },
		success: function (data) {
   			$.each(
				data.forms,
				function(i, x) {
					if (x.name == "Starbucks") {
						$(".alert").append(" Done!<br>");
						form = x;
						$.each(
							form.elements,
							function(j, y) {
								if (y.label == "Photos") { i
									photoKey = y.key; 
								
									
									return false;
								}
							}
						);

						getRecords(1);		
				
						return false;
					}
				}
			);
		},
		url: "https://api.fulcrumapp.com/api/v2/forms.json",
	});
}

function getRecords(pageNumber) { 
	$(".alert").append("Getting records... page " + pageNumber + " ... ");

	$.ajax({
		data: {form_id: form.id, page: pageNumber},
		contentType: "application/json",
		dataType: "json",
		headers: { "X-ApiToken": authKey },
		success: function (data) {
			$(".alert").append(" Done!<br>");
			$.each(data.records, function(i, x) { records.push(x); });
			if (pageNumber < data.total_pages) { getRecords(pageNumber + 1); }
		},
		url: "https://api.fulcrumapp.com/api/v2/records.json",
	});
}

function guid() {
	function _p8(s) {
		var p = (Math.random().toString(16)+"000000000").substr(2,8);
		

		return s ? "-" + p.substr(0,4) + "-" + p.substr(4,4) : p ;
	}
	

	return _p8() + _p8(true) + _p8(true) + _p8();
}

function updateRecords() {
	$.each(
		records,
		function(i, x) {
			x.form_values[photoKey] = [];
			x.form_values[photoKey].push({
				caption: "",
				photo_id: photoAccessKeys[Math.floor(Math.random() * 100)] 
			});
			x.form_values[photoKey].push({
                		caption: "",
                		photo_id: photoAccessKeys[Math.floor(Math.random() * 100)]
        		});

			$.ajax({
				async: false,
				contentType: "application/json",
				data: JSON.stringify({ "record": x }),
				dataType: "json",
				headers: { "X-ApiToken": authKey },
				success: function(data) {},
				type: "PUT",
				url: "https://api.fulcrumapp.com/api/v2/records/" + x.id + ".json",
			});

			var startTime = new Date().getTime(); // get the current time
			while (new Date().getTime() < startTime + 1500);
		}
	);
}

function uploadPhotos() {
	for (var i = 1; i <= 100; i++) {
		var formData = new FormData();
		formData.append("photo[access_key]", guid());
		formData.append("photo[file]", $("#photo" + i)[0].files[0]);
	
		$.ajax({
			async: false,
			cache: false,
			contentType: false,
			data: formData,
			dataType: "json",
			headers: { "X-ApiToken": authKey },
			processData: false,
			success: function (data) { photoAccessKeys.push(data.photo.access_key); },
			type: "POST",
			url: "https://api.fulcrumapp.com/api/v2/photos.json"
		});
	}

	updateRecords();
}

