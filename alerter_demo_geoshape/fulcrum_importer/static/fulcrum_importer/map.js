"use strict";
		
	$(document).ready(function () {
	
		if (!Date.now) {
				Date.now = function() { return new Date().getTime() } //Time in milliseconds
			}

		var OpenStreetMap = L.tileLayer('http://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{
			maxZoom : 16,
			attribution : 'Map data © <a href="http://openstreetmap.org">OpenStreetMap</a> contributors',
			id : 'mapbox.light'
		});
		
		var Esri_WorldImagery = L.tileLayer('http://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
			maxZoom : 16,
			attribution: 'Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community'
		});
		
		var mini1 = new L.TileLayer('http://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
			minZoom: 0, 
			maxZoom: 14, 
			attribution: 'Map data © <a href="http://openstreetmap.org">OpenStreetMap</a> contributors'
		});
		
		var mini2 = new L.TileLayer('http://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
			minZoom: 0,
			maxZoom: 14,
			attribution: 'Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN , IGP, UPR-EGP, and teh GIS User Community'
		});
		
		var map = L.map('map', {
			zoomControl: false,
			fullscreenControl: true,
			center:[0, 0], 
			zoom: 2,
			layers: OpenStreetMap
		});
		
		var baseMaps = {
			"Esri_WorldImagery": Esri_WorldImagery,
			"OpenStreetMap": OpenStreetMap
		};
		
		var myGeo = {
			"type": "Feature",
			"properties": {
				"name": "A place"
			},
			"geometry": {
				"type": "Point",
				"coordinates": [91.99404, 62.75621]
			}, 
		};
		
		// Track which layers are in the map //
		var activeLayers = {};
		
		// Track layer colors for legend //
		var layerStyles = {};
		
		// Track refresh intervals sources for each layer //
		var layerUpdates = {};
		
		// Track layer sources //
		var layerUrls = {};
		
		// Track which layers are subscription //
		var subLayers = {};
		
		// Track triggers posted by user //
		var pzTriggers= {};
		
		var mycolor = "#3d3d3d";
		layerStyles["E55"] = {
			radius : 4,
			fillColor : mycolor,
			color : "#000000",
			weight : 1, 
			opacity : 1,
			fillOpacity : 1
		}
		
		var myLayer = L.geoJson(myGeo, {
			pointToLayer: function(feature, latlng) {
					return L.circleMarker(latlng, Markers(feature, "E55"));
				}
		});
		
		// Empty layer list for any user uploaded layers //
		var layers = {};
		
		// Empty layer list for any pz Events //
		var events = {}; 
		events["E55"] = myLayer;
		
		// Create divisions in the layer control //
		var overlays = {
			"Fulcrum Layers": layers,
			"Events": events
		};
		
		//Set starting bounds for zoom-to-extent button //
		var defaultBounds = map.getBounds();
		var north = -90.0;
		var east = -180.0;
		var south = 90.0;
		var west = 180.0;
		var bounds = defaultBounds;
		
		// Get the bounds of a layer and compare to any other active layers //
		function fetchBounds(layer) {
			var temp = L.latLngBounds(layer.getBounds()); 
			north = (north > temp.getNorth() ? north : temp.getNorth());
			east = (east > temp.getEast() ? east : temp.getEast());
			south = (south < temp.getSouth() ? south : temp.getSouth());
			west = (west < temp.getWest() ? west : temp.getWest());
			var SW = L.latLng(south,west)
			var NE = L.latLng(north,east);
			return L.latLngBounds(SW, NE);
		};
		
		var layerControl;
		
		// Gets list of available layers //
		$.ajax({
			url : '/fulcrum_importer/fulcrum_layers',
			dataType: "json",
			success : function(result) {
				updateLayers(result);
			}
		});
		// Update the layer control with any new layers //
		function updateLayers(result) {
			for (var key in result) {
				if(!layers[key]){
					if(!(key in layerStyles)) {
						var color = getRandomColor();
						layerStyles[key] = {
							radius : 4,
							fillColor : color,
							color : "#000000",
							weight : 1, 
							opacity : 1,
							fillOpacity : 1
						}
					};
					layers[key] = L.geoJson(false);
					layerUrls[key] = '/fulcrum_importer/fulcrum_geojson?layer=' + key;
					console.log(layerUrls[key]);
				}
			}
			layerControl = L.control.groupedLayers(baseMaps, overlays).addTo(map);
		};
		
		// Listens for user selecting a layer from Layer Control //
		map.on('overlayadd', onOverlayAdd);

		// Find which layer was selected, get its data from URL, add it to the empty layer, and add the layer to the map //
		function onOverlayAdd(e) {
			var name = e["name"];
			// If its a subscribed layer, handle the process differently //
			if (name in subLayers) {
				onSubOverlayAdd(name);
			}
			else if (name in events) {
				onEventAdd(name);
			}
			else {
				console.log("Going to get: " + layerUrls[name]);
				$.ajax({
						url : layerUrls[name],
						dataType: "json",
						success : function(result) {
							addSuccess(result, name);
						}, 
				});
			}
		};
		
		function addSuccess(result, name) {
			var layer = result[name];
			addLayer(layer, name);
			activeLayers[name] = null;
			bounds = fetchBounds(layers[name]);
			// If no layers/legend currently: add legend, else: delete old version and add new version //
			if(Object.keys(activeLayers).length == 1) {
				legend.addTo(map);
			}
			else {
				legend.removeFrom(map);
				legend.addTo(map);
			}
			layerRefresher(name);
		};
		
		function addLayer(layer, name) {
			console.log("Adding layer");
			console.log(layer);
			layers[name] = L.geoJson(layer, {
				onEachFeature: onEachFeature,
				filter : function(feature) {
					if (timeout != 0) {
						return feature.properties.time + (timeout * 60) > Math.floor(Date.now()/1000);
					}
					else {
						return true;
					}
				},
				pointToLayer: function(feature, latlng) {
					return L.circleMarker(latlng, Markers(feature, name));
				}
			}).addTo(map);
		};
		
		function layerRefresher(key) {
			layerUpdates[key] = setInterval(function() {
				console.log("Updating");
				$.ajax({
						url : layerUrls[key],
						dataType: "json",
						success : function(result) {
							var layer = result[key];
							layers[key].clearLayers();
							layers[key] = null;
							addLayer(layer, key);
							north = -90.0;
							east = -180.0;
							south = 90.0;
							west = 180.0;
							bounds = defaultBounds;
							bounds = fetchBounds(layers[key]);
						}, 
					});
			}, refresh * 1000);
		};
		
		// Listens for user deselecting layer from Layer Control //
		map.on('overlayremove', onOverlayRemove);
		
		// Removes layer data from the geojson layer //
		function onOverlayRemove(e) {
			var name = e["name"];
			// If its a subscribed layer, handle the process differently //
			if(name in subLayers) {
				onSubOverlayRemove(name);
			}
			else if(name in events) {
				onEventRemove(name);
			}
			else {
				console.log("Updates stopped");
				clearInterval(layerUpdates[name]);
				layerUpdates[name] = null;
				layers[name].clearLayers();
				layers[name] = null;
				delete activeLayers[name];
				// Reset bounds then iterate through any active layers to compute new bounds //
				north = -90.0;
				east = -180.0;
				south = 90.0;
				west = 180.0;
				bounds = defaultBounds;
				for (var key in activeLayers) {
					if (key in layers) {
						bounds = fetchBounds(layers[key]);
					}
					if (key in events) {
						bounds = fetchBounds(events[key]);
					}
				}
				// If removing only layer: remove legend, else: remove and add new version //
				legend.removeFrom(map);
				if(Object.keys(activeLayers).length != 0) {
					legend.addTo(map);
				};
			}
		};
		
		// Create legend for active layers //
		var legend = L.control({position: 'bottomright'});

		legend.onAdd = function (map) {
			var div = L.DomUtil.create('div', 'legend');
			for(var key in activeLayers) {
				div.innerHTML +=
					'<div class="subdiv">' +
					'<i class="circle" style="background: '+ layerStyles[key].fillColor + '"></i> ' +
					'<span class="legend-lable">' + key + '</span><br>'
					+ '</div>';
			}
			return div;
		};
		
		// Adds a locator map to bottom corner of the main map //
		var miniMap = new L.Control.MiniMap(mini1).addTo(map);
		
		map.on('baselayerchange', function(e) {
			console.log(e);
			var base = e["name"];
			if (base == 'Esri_WorldImagery') {
				miniMap.removeFrom(map);
				miniMap = new L.Control.MiniMap(mini2).addTo(map);
			}
			else {
				miniMap.removeFrom(map);
				miniMap = new L.Control.MiniMap(mini1).addTo(map);
			}
		});
		
		// Adds a popup with information for each point //
		function onEachFeature(feature, layer) {
			layer.on('click', function (e) {
				var content = "";
				
				// Add alert name //
				if (e.target.feature.properties.name != null && e.target.feature.properties.name != "") {
					content += '<p><strong>Name: </strong> ' + e.target.feature.properties.name + '</p>';
				}
				else  {
					content += '<p><strong>Name: </strong>Unavailable</p>';
				}
				
				// Add alert time //
				if (e.target.feature.properties.time != null && e.target.feature.properties != "") {
					var time = new Date(e.target.feature.properties.time * 1000);
					content += '<p><strong>Date: </strong>'+ time + '</p>';
				}
				else {
					content += '<p><strong>Date: </strong>Unavailable</p>';
				}
				
				// Add alert address //
				if (e.target.feature.properties.address_1 != null && e.target.feature.properties.address_1 != "") {
					content += '<p><strong>Address: </strong>' + e.target.feature.properties.address_1;
				}
				else {
					content += '<p><strong>Address: </strong>Unavailable';
				}
				
				// Add alert city //
				if (e.target.feature.properties.city != null && e.target.feature.properties.city != "") {
					content += '</br><strong>City: </strong>' + e.target.feature.properties.city;
				}
				else {
					content += '</br><strong>City: </strong>Unavailable';
				}
				
				// Add alert country //
				if (e.target.feature.properties.country != null && e.target.feature.properties.country != "") {
					content += '</br><strong>Country: </strong>' + e.target.feature.properties.country;
				}
				else {
					content += '</br><strong>Country: </strong>Unavailable';
				}
				
				// close the address, city, country paragraph //
				content += '</p>';
				
				// Add alert photos //
				if (e.target.feature.properties.photos_url != null && e.target.feature.properties.photos_url != "") {
					var urlStr = "";
					for (var url in e.target.feature.properties.photos_url){
						urlStr += '<p><a href="' + e.target.feature.properties.photos_url[url] + '" target="_blank"><img src="' + e.target.feature.properties.photos_url[url] + '" style="width: 250px; height: 250px;"/></a></p>';
					};
					
					content += urlStr;
				}
				
				// Add alert videos
				if (e.target.feature.properties.videos_url != null && e.target.feature.properties.videos_url != "") {
					var urlStr = "";
					for (var url in e.target.feature.properties.videos_url){
						urlStr += '<p><video width="250" height="250" controls><source src="' + e.target.feature.properties.videos_url[url] + '" type="video/mp4" target="_blank"></video></p>';
					};
					
					content += urlStr;
				}
				
				// Add alert audio
				if (e.target.feature.properties.audio_url != null && e.target.feature.properties.audio_url != "") {
					var urlStr = "";
					for (var url in e.target.feature.properties.audio_url){
						urlStr += '<p><audio controls><source src="' + e.target.feature.properties.audio_url[url] + '" type="audio/mp4"></audio></p>';
					};
					
					content += urlStr;
				}
				
				// Get position for popup //
				var coords = [e.target.feature.geometry.coordinates[1],e.target.feature.geometry.coordinates[0]];
				
				// Create popup and add to map //
				var popup = L.popup({
					maxHeight: 400,
					closeOnClick: false,
					keepInView: true
				}).setLatLng(coords).setContent(content).openOn(map);
			});
		}
		
		// Symbolizes new points in red, old points in grey //
		function Markers (feature, key) {
			
			
			if (feature.properties.time + (colortime * 60) > Math.round(Date.now()/1000.0) && colortime > 0){
				return {
					radius : 5,
					fillColor : "#e60000",
					color : "#000000",
					weight : 1,
					opacity : 1,
					fillOpacity : 1
				}
			}
			
			else {
			    return layerStyles[key];
			}
		}
		
		
		// Show coordinates of mouse position //
		L.control.mousePosition().addTo(map);
		
		// Option to get your own location on the map //
		L.control.locate({
			position: 'topleft',
			drawCircle: false,
			remainActive: false,
			icon: 'fa fa-map-marker'
		}).addTo(map);
		
		// Adds a return to home extend button //
		var zoomHome = L.Control.zoomHome();
		zoomHome.addTo(map);
		
		// Adds numeric scale to map //
		L.control.scale().addTo(map);
		
		// Button to fit map extent to bounds of point layer //
		var extentButton = L.easyButton({
			states: [{
				stateName: 'Zoom to extent of current features',
				icon: 'fa-map',	
				title: 'Zoom to extent of current features',
				onClick: function(btn, map) {
					map.fitBounds(bounds);
				}
			}]
		}).addTo(map);
		
		// Adds draggable zoom box //
		var zoomBox = L.control.zoomBox({
			className: 'fa fa-search-plus',
			modal: true,
		}).addTo(map);
		
		
		// Button to set alert timeout //
		if(typeof(Storage) != "undefined") {
			if (sessionStorage.timeout) {
				var timeout = parseInt(sessionStorage.timeout);
			}
			else {
				sessionStorage.timeout = "0";
				timeout = 0;
			}
		}
		else {
			var timeout = 0;
		}
		document.getElementById("timeout").value = timeout;
		var getTimeout = $(function() {
		
			var TimeDialogBox = $("#timeoutForm").dialog({
				autoOpen: false,
				closeOnEscape: false,
				open: function(event, ui) {
					$(".ui-dialog-titlebar-close", ui.dialog | ui).hide();
					$("#colortimeForm").dialog('close');
					$("#refreshForm").dialog('close');
					$("#subscribeForm").dialog('close');
					$("#formContainer").dialog('close');
					$("#pzContainer").dialog('close');
					$("#triggerContainer").dialog('close');
					$("#eventContainer").dialog('close');
					$("#alertContainer").dialog('close');
				},
				height: 250,
				width: 350,
				appendTo: "#map",
				position: {
					my: "left top",
					at: "right bottom",
					of: placeholder
				},
				modal: false,
				buttons: {
					"Submit": function() {
						var inNum = parseInt($("#timeout").val());
						if(isNaN(inNum) || inNum < 0 || inNum == "") {
							timeout = 0;
							document.getElementById("timeout").value = timeout;
							sessionStorage.timeout = timeout;
						}
						else {
							timeout = inNum;
							sessionStorage.timeout = inNum;
							
						}
						map.dragging.enable();
						map.doubleClickZoom.enable();
						$(this).dialog("close");
					},
					"Cancel": function() {
						map.dragging.enable();
						map.doubleClickZoom.enable();
						$(this).dialog("close");
					}
				},
			
			});
			
			$('#timeoutForm').keypress( function(e) {
				if (e.charCode == 13 || e.keyCode == 13) {
					var inNum = parseInt($("#timeout").val());
						if(isNaN(inNum) || inNum < 0 || inNum == "") {
							timeout = 0;
							document.getElementById("timeout").value = timeout;
							sessionStorage.timeout = timeout;
						}
						else {
							timeout = inNum;
							sessionStorage.timeout = inNum;
						}
						map.dragging.enable();
						map.doubleClickZoom.enable();
						$(this).dialog("close");
					e.preventDefault();
				}
			});
			
			var timeoutButton = L.easyButton({
				states: [{
					stateName: 'Set timeout for features',
					icon: 'fa-clock-o',	
					title: 'Set timeout for features',
					onClick: function(btn, map) {
						map.dragging.disable();
						map.doubleClickZoom.disable();
						TimeDialogBox.dialog("open");
					}
				}]
			}).addTo(map);
		});		
	
		
		// Button to set new alert color time //
		if(typeof(Storage) != "undefined") {
			if (sessionStorage.colortime) {
				var colortime = parseInt(sessionStorage.colortime);
			}
			else {
				sessionStorage.colortime = "0";
				colortime = 0;
			}
		}
		else {
			var colortime = 0;
		}
		document.getElementById("colortime").value = colortime;
		var getColortime = $(function() {
		
			var colorDialogBox = $("#colortimeForm").dialog({
				autoOpen: false,
				closeOnEscape: false,
				open: function(event, ui) {
					$(".ui-dialog-titlebar-close", ui.dialog | ui).hide(); 
					$("#timeoutForm").dialog('close');
					$("#refreshForm").dialog('close');
					$("#subscribeForm").dialog('close');
					$("#formContainer").dialog('close');
					$("#pzContainer").dialog('close');
					$("#triggerContainer").dialog('close');
					$("#eventContainer").dialog('close');
					$("#alertContainer").dialog('close');
				},
				height: 250,
				width: 350,
				appendTo: "#map",
				position: {
					my: "left top",
					at: "right bottom",
					of: placeholder
				},
				modal: false,
				buttons: {
					"Submit": function() {
						var inNum = parseInt($("#colortime").val());
						if(isNaN(inNum) || inNum < 0 || inNum == '') {
							colortime = 0;
							document.getElementById("colortime").value = colortime;
							sessionStorage.colortime = colortime;
						}
						else {
							colortime = inNum;
							sessionStorage.colortime = inNum;
						}
						map.dragging.enable();
						map.doubleClickZoom.enable();
						$(this).dialog("close");
					},
					"Cancel": function() {
						map.dragging.enable();
						map.doubleClickZoom.enable();
						$(this).dialog("close");
					}
				},
			
			});
			
			$('#colortimeForm').keypress( function(e) {
				if (e.charCode == 13 || e.keyCode == 13) {
					var inNum = parseInt($("#colortime").val());
						if(isNaN(inNum) || inNum < 0 || inNum == "") {
							colortime = 0;
							document.getElementById("colortime").value = colortime;
							sessionStorage.colortime = colortime;
						}
						else {
							colortime = inNum;
							sessionStorage.colortime = inNum;
						}
						map.dragging.enable();
						map.doubleClickZoom.enable();
						$(this).dialog("close");
					e.preventDefault();
				}
			});
			
			var colorTimeButton = L.easyButton({
				states: [{
					stateName: 'Set time for new feature color',
					icon: 'fa-eye',	
					title: 'Set time for new feature color',
					onClick: function(btn, map) {
						map.dragging.disable();
						map.doubleClickZoom.disable();
						colorDialogBox.dialog("open");
					}
				}]
			}).addTo(map);
		});
		
		// Button to set new Refresh rate //
		var refresh;
		if(typeof(Storage) != "undefined") {
			if (sessionStorage.refresh) {
				refresh = parseInt(sessionStorage.refresh);
			}
			else {
				sessionStorage.refresh = "60";
				refresh = 60;
			}
		}
		else {
			refresh = 60;
		}
		document.getElementById("refresh").value = refresh;
		var getRefresh = $(function() {
		
			var refreshDialogBox = $("#refreshForm").dialog({
				autoOpen: false,
				closeOnEscape: false,
				open: function(event, ui) {
					$(".ui-dialog-titlebar-close", ui.dialog | ui).hide();
					$("#timeoutForm").dialog('close');
					$("#colortimeForm").dialog('close');
					$("#subscribeForm").dialog('close');
					$("#formContainer").dialog('close');
					$("#pzContainer").dialog('close');
					$("#triggerContainer").dialog('close');
					$("#eventContainer").dialog('close');
					$("#alertContainer").dialog('close');
				},
				height: 250,
				width: 350,
				appendTo: "#map",
				position: {
					my: "left top",
					at: "right bottom",
					of: placeholder
				},
				modal: false,
				buttons: {
					"Submit": function() {
						var inNum = parseInt($("#refresh").val());
						if(isNaN(inNum) || inNum <= 0 || inNum == "") {
							refresh = 60;
							document.getElementById("refresh").value = refresh;
							sessionStorage.refresh = refresh;
						}
						else {
							refresh = inNum;
							sessionStorage.refresh = inNum;
							
						}
						for(var key in activeLayers) {
							clearInterval(layerUpdates[key]);
							layerUpdates[key] = null;
							layerRefresher(key);
						}
						map.dragging.enable();
						map.doubleClickZoom.enable();
						$(this).dialog("close");
					},
					"Cancel": function() {
						map.dragging.enable();
						map.doubleClickZoom.enable();
						$(this).dialog("close");
					}
				},
			
			});
			
			$('#refreshForm').keypress( function(e) {
				if (e.charCode == 13 || e.keyCode == 13) {
					var inNum = parseInt($("#refresh").val());
						if(isNaN(inNum) || inNum < 0 || inNum == "") {
							refresh = 60;
							document.getElementById("refresh").value = refresh;
							sessionStorage.refresh = refresh;
						}
						else {
							refresh = inNum;
							sessionStorage.refresh = inNum;
						}
						for(var key in activeLayers) {
							clearInterval(layerUpdates[key]);
							layerUpdates[key] = null;
							layerRefresher(key);
						}
						map.dragging.enable();
						map.doubleClickZoom.enable();
						$(this).dialog("close");
					e.preventDefault();
				}
			});
			
			var refreshButton = L.easyButton({
				states: [{
					stateName: 'Set time for layer refresh',
					icon: 'fa-refresh',	
					title: 'Set time for layer refresh',
					onClick: function(btn, map) {
						map.dragging.disable();
						map.doubleClickZoom.disable();
						refreshDialogBox.dialog("open");
					}
				}]
			}).addTo(map);
		});
		
		// Uploads user data //
		var uploadForm = (function(){
			map.dragging.enable();
			map.doubleClickZoom.enable();
            var formData = new FormData($('#fileUpload')[0]);
            $.ajax({
                url: '/fulcrum_importer/fulcrum_upload',  //Server script to process data
                type: 'POST',
                xhr: function() {  // Custom XMLHttpRequest
                    var myXhr = $.ajaxSettings.xhr();
                    if(myXhr.upload){ // Check if upload property exists
                        myXhr.upload.addEventListener('progress',progressHandlingFunction, false); // For handling the progress of the upload
						myXhr.upload.addEventListener('progress',progressFinishedFunction, false); // If progress is finished, close file upload dialog
                    }
                    return myXhr;
                },
                // Ajax events //
                beforeSend: console.log("Sending"),
				// Adds layer to the map //
                success: function (result) {
					document.getElementById('waiting').style.visibility = 'hidden';
					for(var key in result) {
						// If layer already exists, remove first, then add new version //
						if(key in layers) {
							map.removeLayer(layers[key]);
							layerControl.removeLayer(key);
							delete layers[key];
							if(key in activeLayers) {
								delete activeLayers[key];
							};
						}
						layerControl.removeFrom(map);
						updateLayers(result);
						
					};
					
				},
                error: console.log("Fail"),
                // Form data //
                data: formData,
                // Options to tell jQuery not to process data or worry about content-type. //
                cache: false,
                contentType: false,
                processData: false
            });
        });
        
		// For progress bar ..
        function progressHandlingFunction(e){
            if(e.lengthComputable){
                $('progress').attr({value:e.loaded,max:e.total});
            }
        }
		function progressFinishedFunction(e) {
			if(e.lengthComputable){
				if(e.loaded == e.total) {
					$("#formContainer").dialog("close");
					$('progress').attr({value: 0.0, max: 1.0});
					document.getElementById('waiting').style.visibility = 'visible';
				}
			}
		}
		
		// Upload dialog box //
		var uploadFileDialogBox = $("#formContainer").dialog({
			autoOpen: false,
			closeOnEscape: false,
			open: function(event, ui) {
				$(".ui-dialog-titlebar-close", ui.dialog | ui).hide(); 
				$("#timeoutForm").dialog('close');
				$("#colortimeForm").dialog('close');
				$("#refreshForm").dialog('close');
				$("#subscribeForm").dialog('close');
				$("#pzContainer").dialog('close');
				$("#triggerContainer").dialog('close');
				$("#eventContainer").dialog('close');
				$("#alertContainer").dialog('close');
			},
			height: 250,
			width: 500,
			appendTo: "#map",
			position: {
				my: "left top",
				at: "right bottom",
				of: placeholder
			},
			modal: true,
			buttons: {
				"Upload": uploadForm,
				"Cancel": function() {
					map.dragging.enable();
					map.doubleClickZoom.enable();
					$(this).dialog("close");
				}
			},
		});
         
		// Button to call upload dialog box //
        var uploadFileButton = L.easyButton({
			states: [{
				stateName: 'Upload File',
				icon: 'fa fa-upload',	
				title: 'Upload File',
				onClick: function(btn, map) {
					map.dragging.disable();
					map.doubleClickZoom.disable();
					uploadFileDialogBox.dialog("open");
				}
			}]
		}).addTo(map);
		
		// Handles use of enter key //
        $('#fileUpload').keypress( function(e) {
			if (e.charCode == 13 || e.keyCode == 13) {
				uploadForm();
				map.dragging.enable();
				map.doubleClickZoom.enable();
				e.preventDefault();
				
			}
		});
		
		var pzType;
		var pzAction;
		var triggerId;
		var triggerTitle;
		var triggerType;
		var triggerQuery;
		var triggerTask;
		var eventId;
		var eventType;
		var eventDate;
		var eventData;
		var alertId;
		var alertTriggerId;
		var alertEventId;
		
		var getPzAction = $(function() {
			var pzDialogBox = $("#pzContainer").dialog({
				autoOpen: false,
				closeOnEscape: false,
				open: function(event, ui) {
					$(".ui-dialog-titlebar-close", ui.dialog | ui).hide();
					$("#timeoutForm").dialog('close');
					$("#colortimeForm").dialog('close');
					$("#refreshForm").dialog('close');
					$("#formContainer").dialog('close');
					$("#subscribeForm").dialog('close');
					$("#triggerContainer").dialog('close');
					$("#eventContainer").dialog('close');
					$("#alertContainer").dialog('close');
				},
				height: 250,
				width: 350,
				appendTo: "#map",
				position: {
					my: "left top",
					at: "right bottom",
					of: placeholder
				},
				modal: false,
				buttons: {
					"Submit": function() {
						pzType = $("#pzType").val().toLowerCase();
						pzAction = $("#pzAction").val().toLowerCase();
						$(this).dialog("close");
						pzHandler(pzType, pzAction);
					},
					
					"Cancel": function() {
						$(this).dialog("close");
						map.dragging.enable();
						map.doubleClickZoom.enable();
					},
					"Manage Events" : function () {
						$(this).dialog("close");
						$('#eventManager').dialog("open");
					}
				},
			});
			
			$('#pzContainer').keypress( function(e) {
				if (e.charCode == 13 || e.keyCode == 13) {
					pzType = $("#pzType").val().toLowerCase();
					pzAction = $("#pzAction").val().toLowerCase();
					$(this).dialog("close");
					pzHandler(pzType, pzAction);
					e.preventDefault();	
				}
			});
			
			var eventManager = $('#eventManager').dialog({
				autoOpen: false,
				maxWidth: 300,
				maxHeight: 600,
				height: 'auto',
				appendTo: '#map',
				modal: false,
				position: {
					my: "left top",
					at: "right bottom",
					of: placeholder
				},
				open: function () {
					var contentStr = "";
					var i = 0;
					for(var key in events) {
						contentStr += '<input type="radio" id="' + i + '" name="eventChoice" value="' + key + '"/><label for="' + i + '">'+ key + '</label><br/>';
						i++;
					}
					$(this).html(contentStr);
				},
				buttons: {
					"Delete": function() {
						deleteEvent();
						$(this).dialog("close");
					},
					"Cancel": function () {
						$(this).dialog("close");
						map.dragging.enable();
						map.doubleClickZoom.enable();
					}
				}
			}); //end confirm dialog
			
			function deleteEvent() {
				//Delete something //
				var choice = $('input[name="eventChoice"]:checked').val();
				console.log(choice);
				console.log(events);
				if (choice in activeLayers) {
					console.log("Event is active, removing from the map");
					map.removeLayer(events[choice]);
					//delete activeLayers[choice];
				}
				console.log("Deleting layer. . .");
				events[choice] = null;
				delete events[choice];
				console.log("Layer deleted")
				layerControl.removeFrom(map);
				layerControl = L.control.groupedLayers(baseMaps, overlays).addTo(map);
				console.log(events);
				map.dragging.enable();
				map.doubleClickZoom.enable();
			};
			
			function pzHandler(type, action) {
				if(action == 'get_all') {
					map.dragging.enable();
					map.doubleClickZoom.enable();
					var request = {"type": type, "data": {}, "action": action};
					pzSender(request);
				}
				else if(type == 'trigger') {
					$("#triggerContainer").dialog("open");
				}
				else if(type == 'event') {
					$("#eventContainer").dialog("open");
				}
				else if(type == 'alert') {
					$("#alertContainer").dialog("open");
				}
				else {
					alert("Wait how did you get here?");
				}
			};
			
			function pzSender(pzrequest) {
				var requestStr = JSON.stringify(pzrequest);
				$.ajax({
					url: '/fulcrum_importer/fulcrum_pzworkflow',
					type: "POST",
					data: requestStr,
					contentType: "application/json",
					processData: false,
					dataType: "json",
					success: function(result) {
						console.log("Success");
						pzResponse(result);
					},
					error: function(result) {
						console.log("Error");
						pzError(result);
					}
				});
			};
			
			function pzResponse(result) {
				if (pzAction == 'delete') {
					if(result == null) {
						console.log("Delete was successful");
					}
					else {
						console.log(result);
					}
				}
				else if (pzAction == 'get') {
					console.log(result);
					if (pzType == 'event') {
						for (var pzevent in events) {
							if (pzevent['data'] != null) {
								L.geoJson(pzevent['data']).addTo(map);
							}
						} 
					}
				}
				else if (pzAction == 'get_all') {
					console.log(result);
					$('<div></div>').dialog({
						autoOpen: true,
						maxWidth: 300,
						maxHeight: 600,
						modal: false,
						appendTo: '#map',
						position: {
							my: "left top",
							at: "right bottom",
							of: placeholder
						},
						title: "List of all {0}s".format(pzType),
						open: function () {
							map.dragging.disable();
							map.doubleClickZoom.disable();
							var contentStr = "";
							$.each(result, function (index, value) {
								contentStr += '<p>' + JSON.stringify(value, undefined, '\t') + '</p>';
							});
							$(this).html(contentStr);
						},
						buttons: {
							Ok: function () {
								$(this).dialog("close");
								map.dragging.enable();
								map.doubleClickZoom.enable();
							}
						}
					}); //end confirm dialog
				}
				else if (pzAction == 'post') {
					if(result == null) {
						console.log("Not created");
					}
					else {
						if(pzType == 'trigger') {
							pzTriggers['id'] = result['id'];
							console.log(pzTriggers);
						}
					}
				}
			}
			function pzError(result) {
				if (pzAction == 'delete') {
					console.log("Oh crap it failed");
				}
			}
			
			var triggerDialogBox = $("#triggerContainer").dialog({
				autoOpen: false,
				closeOnEscape: false,
				open: function(event, ui) {
					$(".ui-dialog-titlebar-close", ui.dialog | ui).hide();
				},
				height: 450,
				width: 300,
				appendTo: "#map",
				position: {
					my: "left top",
					at: "right bottom",
					of: placeholder
				},
				modal: false,
				buttons: {
					"Submit": function() {
						triggerId = $("#triggerId").val();
						triggerTitle = $("#triggerTitle").val()
						triggerType = $("#triggerType").val();
						triggerQuery = $("#triggerQuery").val();
						triggerTask = $("#triggerTask").val();
						var triggerData = {"id": triggerId, "title": triggerTitle, "condition": {"type": triggerType, "query": triggerQuery}, "job": {"Task": triggerTask}}
						var pzTrigger = {"type": pzType, "data": {}, "action": pzAction};
						pzTrigger["data"] = triggerData;
						console.log(pzTrigger);
						console.log(triggerData);
						pzSender(pzTrigger);
						$(this).dialog("close");
						map.dragging.enable();
						map.doubleClickZoom.enable();
					},
					"Cancel": function() {
						$(this).dialog("close");
						map.dragging.enable();
						map.doubleClickZoom.enable();
					}
				},
			});
			$('triggerContainer').keypress( function(e) {
				if (e.charCode == 13 || e.keyCode == 13) {
					triggerId = $("#triggerId").val();
					triggerTitle = $("#triggerTitle").val()
					triggerType = $("#triggerType").val();
					triggerQuery = $("#triggerQuery").val();
					triggerTask = $("#triggerTask").val();
					var triggerData = {"id": triggerId, "title": triggerTitle, "condition": {"type": triggerType, "query": triggerQuery}, "job": {"Task": triggerTask}}
					var pzTrigger = {"type": pzType, "data": {}, "action": pzAction};
					pzTrigger["data"] = triggerData;
					console.log(pzTrigger);
					console.log(triggerData);
					pzSender(pzTrigger);
					$(this).dialog("close");
					map.dragging.enable();
					map.doubleClickZoom.enable();
					e.preventDefault();	
				}
			});
			
			var eventDialogBox = $("#eventContainer").dialog({
				autoOpen: false,
				closeOnEscape: false,
				open: function(event, ui) {
					$(".ui-dialog-titlebar-close", ui.dialog | ui).hide();
				},
				height: 400,
				width: 300,
				appendTo: "#map",
				position: {
					my: "left top",
					at: "right bottom",
					of: placeholder
				},
				modal: false,
				buttons: {
					"Submit": function() {
						eventId = $("#eventId").val();
						eventType = $("#eventType").val();
						eventDate = $("#eventDate").val();
						if ($("#eventData").val() != "") {
							eventData = JSON.parse($("#eventData").val());
						}
						else {
							eventData = {};
						}
						var pzData = {"id": eventId, "type": eventType, "date": eventDate, "data": eventData}
						var pzEvent = {"type": pzType, "data": pzData, "action": pzAction};
						console.log(pzEvent);
						console.log(pzData);
						pzSender(pzEvent);
						$(this).dialog("close");
						map.dragging.enable();
						map.doubleClickZoom.enable();
					},
					"Cancel": function() {
						$(this).dialog("close");
						map.dragging.enable();
						map.doubleClickZoom.enable();
					}
				},
			});
			$('eventContainer').keypress( function(e) {
				if (e.charCode == 13 || e.keyCode == 13) {
					eventId = $("#eventId").val();
					eventType = $("#eventType").val();
					eventDate = $("#eventDate").val();
					if ($("#eventData").val() != "") {
						eventData = JSON.parse($("#eventData").val());
					}
					else {
						eventData = {};
					}
					var pzData = {"id": eventId, "type": eventType, "date": eventDate, "data": eventData}
					var pzEvent = {"type": pzType, "data": pzData, "action": pzAction};
					console.log(pzEvent);
					console.log(pzData);
					pzSender(pzEvent);
					$(this).dialog("close");
					map.dragging.enable();
					map.doubleClickZoom.enable();
					e.preventDefault();	
				}
			});
			
			var alertDialogBox = $("#alertContainer").dialog({
				autoOpen: false,
				closeOnEscape: false,
				open: function(event, ui) {
					$(".ui-dialog-titlebar-close", ui.dialog | ui).hide();
				},
				height: 400,
				width: 300,
				appendTo: "#map",
				position: {
					my: "left top",
					at: "right bottom",
					of: placeholder
				},
				modal: false,
				buttons: {
					"Submit": function() {
						alertId = $("#alertId").val();
						alertTriggerId = $("#alertTriggerId").val();
						alertEventId = $("#alertEventId").val();
						var alertData = {"id": alertId, "trigger_id": alertTriggerId, "event_id": alertEventId}
						var pzAlert = {"type": pzType, "data": {}, "action": pzAction};
						pzAlert["data"] = alertData;
						console.log(pzAlert);
						console.log(alertData);
						pzSender(pzAlert);
						$(this).dialog("close");
						map.dragging.enable();
						map.doubleClickZoom.enable();
					},
					"Cancel": function() {
						$(this).dialog("close");
						map.dragging.enable();
						map.doubleClickZoom.enable();
					}
				},
			});
			$('alertContainer').keypress( function(e) {
				if (e.charCode == 13 || e.keyCode == 13) {
					alertId = $("#alertId").val();
					alertTriggerId = $("#alertTriggerId").val();
					alertEventId = $("#alertEventId").val();
					var alertData = {"id": alertId, "trigger_id": alertTriggerId, "event_id": alertEventId}
					var pzAlert = {"type": pzType, "data": {}, "action": pzAction};
					pzAlert["data"] = alertData;
					console.log(pzAlert);
					console.log(alertData);
					pzSender(pzAlert);
					$(this).dialog("close");
					map.dragging.enable();
					map.doubleClickZoom.enable();
					e.preventDefault();	
				}
			});
			
			var pzButton = L.easyButton({
				states: [{
					stateName: 'Pz-Workflow controller',
					icon: 'fa-cogs',	
					title: 'Pz-Workflow controller',
					onClick: function(btn, map) {
						map.dragging.disable();
						map.doubleClickZoom.disable();
						pzDialogBox.dialog("open");
					}
				}]
			}).addTo(map);
		});
		function onEventAdd(name) {
			console.log("Adding");
			activeLayers[name] = null;
			bounds = fetchBounds(events[name]);
			if(Object.keys(activeLayers).length == 1) {
				legend.addTo(map);
			}
			else {
				legend.removeFrom(map);
				legend.addTo(map);
			}
		};
		function onEventRemove(name) {
			console.log("Removing");
			delete activeLayers[name];
			// Reset bounds then iterate through any active layers to compute new bounds //
			north = -90.0;
			east = -180.0;
			south = 90.0;
			west = 180.0;
			bounds = defaultBounds;
			for (var key in activeLayers) {
				if (key in layers) {
					bounds = fetchBounds(layers[key]);
				}
				if (key in events) {
					bounds = fetchBounds(events[key]);
				}
			}
			// If removing only layer: remove legend, else: remove and add new version //
			legend.removeFrom(map);
			if(Object.keys(activeLayers).length != 0) {
				legend.addTo(map);
			};
		};
		
		// Button to set alert subscription //
		if(typeof(Storage) != "undefined") {
			if (sessionStorage.sub) {
				var sub = sessionStorage.sub;
			}
			else {
				sessionStorage.sub = "";
				var sub = "";
			}
		}
		else {
			var sub = "";
		}
		document.getElementById("sub").value = sub;
		var getSubscription = $(function() {
			var subDialogBox = $("#subscribeForm").dialog({
				autoOpen: false,
				closeOnEscape: false,
				open: function(event, ui) {
					$(".ui-dialog-titlebar-close", ui.dialog | ui).hide();
					$("#timeoutForm").dialog('close');
					$("#colortimeForm").dialog('close');
					$("#refreshForm").dialog('close');
					$("#formContainer").dialog('close');
					$("#pzContainer").dialog('close');
					$("#triggerContainer").dialog('close');
					$("#eventContainer").dialog('close');
					$("#alertContainer").dialog('close');
				},
				height: 200,
				width: 500,
				appendTo: "#map",
				position: {
					my: "left top",
					at: "right bottom",
					of: placeholder
				},
				modal: false,
				buttons: {
					"Submit": function() {
						var inStr = $("#sub").val();
						//if(!ValidURL(inStr)) {
						//	sub = "";
						//	document.getElementById("sub").value = sub;
						//	sessionStorage.sub = sub;
						//}
						//else {
							sub = inStr;
							sessionStorage.sub = inStr;
							getSub(sub);
							
						//}
						$(this).dialog("close");
						map.dragging.enable();
						map.doubleClickZoom.enable();
					},
					"Clear": function() {
						sessionStorage.sub = "";
						sub = "";
						document.getElementById("sub").value = sub;
					},
					"Cancel": function() {
						$(this).dialog("close");
						map.dragging.enable();
						map.doubleClickZoom.enable();
					}
				},
			
			});
			
			$('#subcribeForm').keypress( function(e) {
				if (e.charCode == 13 || e.keyCode == 13) {
					var inStr = $("#sub").val();
					//if(!ValidURL(inStr)) {
					//	sub = "";
					//	document.getElementById("sub").value = sub;
					//	sessionStorage.sub = sub;
					//}
					//else {
						sub = inStr;
						sessionStorage.sub = inStr;
						getSub(sub);
							
					//}
					
					$(this).dialog("close");
					e.preventDefault();
					map.dragging.enable();
					map.doubleClickZoom.enable();
				}
			});
			
			var subscribeButton = L.easyButton({
				states: [{
					stateName: 'Subscribe to an Alert',
					icon: 'fa-bell',	
					title: 'Subscribe to an Alert',
					onClick: function(btn, map) {
						map.dragging.disable();
						map.doubleClickZoom.disable();
						subDialogBox.dialog("open");
					}
				}]
			}).addTo(map);
		});	
		
		
		function getSub(url) {
			$.ajax({
				url : url,
				dataType: "json",
				success : function(result) {
						subUpdate(result, url);
					},
				error : function() {
						alert("Unable to get alert service, re-check URL or give up all hope");
					}
			});
		}	
			
		function subUpdate(result, url) {
			//var layerName = result['test'];
			var layerName = 'test';
			subLayers[layerName] = null;
			if(!(layerName in layers)){
				if(!(layerName in layerStyles)) {
					var color = getRandomColor();
					layerStyles[layerName] = {
						radius : 4,
						fillColor : color,
						color : "#000000",
						weight : 1, 
						opacity : 1,
						fillOpacity : 1
					}
				};
				layers[layerName] = L.geoJson(false);
				layerUrls[layerName] = url;
			}
			layerControl.removeFrom(map);
			layerControl = L.control.groupedLayers(baseMaps, overlays).addTo(map);
		}
		
		function onSubOverlayAdd(name) {
			console.log("Going to get: " + layerUrls[name] + " from subbed layers!");
			$.ajax({
					url : layerUrls[name],
					dataType: "json",
					success : function(result) {
						addSubSuccess(result, name);
					}, 
			});
		};
		
		function addSubSuccess(result, name) {
			//var layer = result['data'];
			var layer = result[name];
			addSubLayer(layer, name);
			activeLayers[name] = null;
			bounds = fetchBounds(layers[name]);
			// If no layers/legend currently: add legend, else: delete old version and add new version //
			if(Object.keys(activeLayers).length == 1) {
				legend.addTo(map);
			}
			else {
				legend.removeFrom(map);
				legend.addTo(map);
			}
			layerRefresher(name);
		};
		
		function addSubLayer(layer, name) {
			console.log("Adding layer");
			console.log(name);
			console.log(layer);
			layers[name] = L.geoJson(layer, {
				onEachFeature: onEachFeature,
				//filter : function(feature) {
				//	if (timeout != 0) {
				//		return feature.properties.time + (timeout * 60) > Math.floor(Date.now()/1000);
				//	}
				//	else {
				//		return true;
				//	}
				//},
				pointToLayer: function(feature, latlng) {
					return L.circleMarker(latlng, Markers(feature, name));
				}
			}).addTo(map);
		};
		
		function subLayerRefresher(key) {
			layerUpdates[key] = setInterval(function() {
				console.log("Updating");
				$.ajax({
						url : layerUrls[key],
						dataType: "json",
						success : function(result) {
							//var layer = result['data'];
							var layer = result;
							layers[key].clearLayers();
							layers[key] = null;
							addLayer(layer, key);
							north = -90.0;
							east = -180.0;
							south = 90.0;
							west = 180.0;
							bounds = defaultBounds;
							bounds = fetchBounds(layers[key]);
						}, 
					});
			}, refresh * 1000);
		};
		
		// Removes layer data from the geojson layer //
		function onSubOverlayRemove(name) {
			console.log("Updates stopped");
			clearInterval(layerUpdates[name]);
			layerUpdates[name] = null;
			layers[name].clearLayers();
			layers[name] = null;
			delete activeLayers[name];
			// Reset bounds then iterate through any active layers to compute new bounds //
			north = -90.0;
			east = -180.0;
			south = 90.0;
			west = 180.0;
			bounds = defaultBounds;
			for (var key in activeLayers) {
				bounds = fetchBounds(layers[key]);
			}
			// If removing only layer: remove legend, else: remove and add new version //
			legend.removeFrom(map);
			if(Object.keys(activeLayers).length != 0) {
				legend.addTo(map);
			};
		};
	
		// Gets randomized color for new layer //
		var approvedColors =[
			"#003366", //darkblue
			"#006600", //darkgreen
			"#ff8000", //orange
			"#99cc00", //limegreen
			"#990099", //purple
			"#009999", //cyan
			"#a6a6a6", //grey
			"#0099cc", //light neon blue
			"#00ff00", //bright green
			"#330032", //dark purple
			"#663300", //poopy brown
			"#ffff00", //bright yellow
			"#999966", //dark tan
			"#ffff99", //light yellow
			"#9999ff", //very light blue
			"#ffbf80", //creamsicle
			"#4d4d4d", //dark grey
			"#ff66cc", //light pink
			"#666699", //pale-ish purple
			"#333300" //vomit			
		];
		var colorix = 0;
		function getRandomColor() {
			if(colorix < approvedColors.length) {
				return approvedColors[colorix++];
			}
			else {
				colorix = 1;
				return approvedColors[0];
			}
		};
		
		String.prototype.format = function() {
			var formatted = this;
			for (var i = 0; i < arguments.length; i++) {
				var regexp = new RegExp('\\{'+i+'\\}', 'gi');
				formatted = formatted.replace(regexp, arguments[i]);
			}
			return formatted;
		};
		
		
	});