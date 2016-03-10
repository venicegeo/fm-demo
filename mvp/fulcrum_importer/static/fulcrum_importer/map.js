"use strict";
		
	$(document).ready(function () {
	
		if (!Date.now) {
				Date.now = function() { return new Date().getTime() } //Time in milliseconds
			}

		var OpenStreetMap = L.tileLayer('http://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{
			maxZoom : 18,
			attribution : 'Map data © <a href="http://openstreetmap.org">OpenStreetMap</a> contributors',
			id : 'mapbox.light'
		});
		
		var Esri_WorldImagery = L.tileLayer('http://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
			maxZoom : 18,
			attribution: 'Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community'
		});
		
		var mini1 = new L.TileLayer('http://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
			minZoom: 0, 
			maxZoom: 16, 
			attribution: 'Map data © <a href="http://openstreetmap.org">OpenStreetMap</a> contributors'
		});
		
		var mini2 = new L.TileLayer('http://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
			minZoom: 0,
			maxZoom: 16,
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
		
		// Track eventtypes //
		var pzEventtypes = {};
		
		// Track which notification have already occured //
		var pzAlerts = {}
		
		// Empty layer list for any user uploaded layers //
		var layers = {};
		
		// Empty layer list for any pz Events //
		var pzEvents = {}; 
		
		// Create divisions in the layer control //
		var overlays = {
			"Fulcrum Layers": layers,
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
			url : '/fulcrum_layers',
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
					layerUrls[key] = '/fulcrum_geojson?layer=' + key;
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
				var genericStr = "";
				var titleStr = "";
				var idStr = "";
				var photosStr = "";
				var audioStr = "";
				var videosStr = "";
				for (var property in e.target.feature.properties) {
					
					if (String(property).toLowerCase().indexOf('name') > -1 || String(property).toLowerCase().indexOf('title') > -1) {
						titleStr += '<p><strong>' + property + ':</strong> ' + e.target.feature.properties[property] + '</p>'
					}
					else if (String(property).toLowerCase().indexOf('id') == 0){
						idStr += '<p><strong>' + property + ':</strong> ' + e.target.feature.properties[property] + '</p>'
					}
					else if(String(property).indexOf('_url') > -1) {
						if (e.target.feature.properties[property] != null && e.target.feature.properties[property] != "") {
							var urls = String(e.target.feature.properties[property]).split(",");
							console.log(urls);
							for (var url in urls){
								if(String(urls[url]).indexOf('.jpg') > -1) {
									photosStr += '<p><a href="' + urls[url] + '" target="_blank"><img src="' + urls[url] + '" style="width: 250px; height: 250px;"/></a></p>';
								}
								if(String(urls[url]).indexOf('.mp4') > -1) {
									videosStr += '<p><video width="250" height="250" controls><source src="' + urls[url] + '" type="video/mp4" target="_blank"></video></p>';
								}
								if(String(urls[url]).indexOf('.m4a') > -1) {
									audioStr += '<p><audio controls><source src="' + urls[url] + '" type="audio/mp4"></audio></p>';
								}
							}
						}
					}
					else {
						if (e.target.feature.properties[property] != null && e.target.feature.properties[property] != "") {
							genericStr += '<p><strong>' + property + ':</strong> ' + e.target.feature.properties[property] + '</p>';
						}
					}
				}
				
				// Get position for popup //
				var coords = [e.target.feature.geometry.coordinates[1],e.target.feature.geometry.coordinates[0]];
				
				// Create popup and add to map //
				var popup = L.popup({
					maxHeight: 400,
					closeOnClick: false,
					keepInView: true
				}).setLatLng(coords).setContent(titleStr + idStr + genericStr + photosStr + videosStr + audioStr).openOn(map);
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
                url: '/fulcrum_upload',  //Server script to process data
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
		
		var getID;
		
		var eventtypesId;
		var eventtypesName;
		var eventtypesFilename;
		var eventtypesSeverity;
		var eventtypesCode;
		
		var triggerId;
		var triggerTitle;
		var triggerType;
		var triggerSeverity;
		var triggerCode;
		var triggerTask;
		
		var eventId;
		var eventType;
		var eventDate;
		var eventFilename;
		var eventSeverity;
		var eventCode;
		
		var alertId;
		var alertTriggerId;
		var alertEventId;
		
		//var getPzAction = $(function() {
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
				"Manager" : function () {
					$(this).dialog("close");
					$('#Manager').dialog("open");
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
		
		var eventManager = $('#Manager').dialog({
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
				for (var key in pzEventtypes) {
					contentStr += '<input type="radio" id="' + i + '" name="choice" value="' + key + '" style="float: left; margin-left: 30%;"/><label for="' + i + '" style="float: left;">Eventtype: '+ key + '</label><br/>';
					i++;
				}
				for(var key in pzEvents) {
					contentStr += '<input type="radio" id="' + i + '" name="choice" value="' + key + '" style="float: left; margin-left: 30%;"/><label for="' + i + '" style="float: left;">Event: '+ key + '</label><br/>';
					i++;
				}
				for (var key in pzTriggers) {
					contentStr += '<input type="radio" id="' + i + '" name="choice" value="' + key + '" style="float: left; margin-left: 30%;"/><label for="' + i + '" style="float: left;">Trigger: '+ key + '</label><br/>';
					i++;
				}
				$(this).html(contentStr);
			},
			buttons: {
				"Delete": function() {
					deleteManager();
					$(this).dialog("close");
				},
				"Cancel": function () {
					$(this).dialog("close");
					map.dragging.enable();
					map.doubleClickZoom.enable();
				}
			}
		}); //end confirm dialog
		
		function deleteManager() {
			var choice = $('input[name="choice"]:checked').val();
			if (choice in pzEvents) {
				deleteEvent(choice);
			}
			if (choice in pzTriggers) {
				deleteTrigger(choice);
			}
			if (choice in pzEventtypes) {
				deleteEventtype(choice);
			}
		}
		
		function deleteEvent(choice) {
			pzEvents[choice] = null;
			delete pzEvents[choice];
			map.dragging.enable();
			map.doubleClickZoom.enable();
		}
		
		function deleteEventtype(choice) {
			pzEventtypes[choice] = null;
			delete pzEventtypes[choice];
			map.dragging.enable();
			map.doubleClickZoom.enable();
		}
		
		function deleteTrigger(choice) {
			pzTriggers[choice] = null;
			delete pzTriggers[choice];
			map.dragging.enable();
			map.doubleClickZoom.enable();
		}
		
		function pzHandler(type, action) {
			if(action == 'get_all') {
				map.dragging.enable();
				map.doubleClickZoom.enable();
				var request = {"type": type, "data": {}, "action": action};
				pzSender(request);
			}
			else if(action == 'get') {
				$("#getContainer").dialog("open");
			}
			else if(action == 'delete') {
				if(type == 'event') {
					$("#deleteEventContainer").dialog("open");
				}
				else {
					$("deleteContainer").dialog("open");
				}
			}
			else {
				if(type == 'eventtypes') {
					$("#eventtypesContainer").dialog("open");
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
			}
		}
		
		function pzSender(pzrequest) {
			var requestStr = JSON.stringify(pzrequest);
			/*function getCookie(name) {
				var cookieValue = null;
				if (document.cookie && document.cookie != '') {
					var cookies = document.cookie.split(';');
						for (var i = 0; i < cookies.length; i++) {
							var cookie = jQuery.trim(cookies[i]);
							// Does this cookie string begin with the name we want?
							if (cookie.substring(0, name.length + 1) == (name + '=')) {
								cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
								break;
							}
						}
				}
				return cookieValue;
			}
			function csrfSafeMethod(method) {
				// these HTTP methods do not require CSRF protection
				return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
			}*/
			var csrftoken = getCookie('csrftoken');
			console.log(requestStr);
			$.ajax({
				url: '/fulcrum_pzworkflow',
				type: "POST",
				data: requestStr,
				contentType: false,
				processData: false,
				dataType: "json",
				success: function(result) {
					console.log("Success");
					pzResponse(result);
				},
				error: function(result) {
					console.log("Error");
					pzError(result);
				},
				beforeSend: function(xhr, settings) {
					if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
						xhr.setRequestHeader("X-CSRFToken", csrftoken);
					}
				}
			});
		};
		
		function pzResponse(result) {
			if (pzAction == 'delete') {
				if(result == null) {
					console.log("Delete was successful");
					if(pzType == 'eventtypes') {
						if(eventtypesId in pzEventtypes) {
							delete pzEventtypes[eventtypesId]
						}
					}
				}
				else {
					console.log(result);
				}
			}
			else if (pzAction == 'get') {
				console.log(result);
				if (pzType == 'event') {
					pzEvents[result['id']] = result[id];
				}
				if(pzType == 'trigger') {
					pzTriggers[result['id']] = result['id'];
				}
				if(pzType == 'eventtypes') {
					pzEventtypes[result['id']] = result['name'];
					console.log("added to eventtypes");
					console.log(pzEventtypes);
				}
				
				
			}
			else if (pzAction == 'get_all') {
				getDialog(result)
			}
			else if (pzAction == 'post') {
				if(result == null) {
					console.log("Not created");
				}
				else {
					if(pzType == 'trigger') {
						pzTriggers[result['id']] = result['id'];
						console.log(pzTriggers);
					}
					if(pzType == 'eventtypes') {
						pzEventtypes[result['id']] = eventtypesName;
						console.log(pzEventtypes);
					}
				}
			}
		}
		
		function getDialog(result) {
			$('<div></div>').dialog({
				autoOpen: true,
				//maxWidth: 450,
				maxHeight: 600,
				width: 400,
				modal: false,
				appendTo: '#map',
				position: {
					my: "left top",
					at: "right bottom",
					of: placeholder
				},
				title: "{0}".format(pzType),
				open: function () {
					map.dragging.disable();
					map.doubleClickZoom.disable();
					map.scrollWheelZoom.disable();
					var contentStr = "";
					$.each(result, function (index, value) {
						contentStr += '<pre style="text-align: left;">' + JSON.stringify(value, undefined, 2) + '</pre><br/>';
					});
					$(this).html(contentStr);
				},
				buttons: {
					Close: function () {
						$(this).dialog("close");
						map.dragging.enable();
						map.doubleClickZoom.enable();
						map.scrollWheelZoom.enable();
					}
				}
			}); //end confirm dialog
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
			height: 425,
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
					triggerTitle = $("#triggerTitle").val()
					triggerType = $("#triggerType").val();
					triggerCode = $("#triggerCode").val();
					triggerSeverity = $("#triggerSeverity").val();
					triggerTask = $("#triggerTask").val();
					var triggerData = {"title": triggerTitle, 
										"condition": {
											"type": triggerType, 
											"query": {
												"query": {
													"bool": {
														"must": [
															{
															"match": {
																"severity": triggerSeverity
																}
															},
															{
															"match": {
																"code": triggerCode
																}
															}
														]
													}
												}
											},
											"job": {
												"Task": triggerTask
											}
										}
									}
									
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
				triggerTitle = $("#triggerTitle").val()
				triggerType = $("#triggerType").val();
				triggerCode = $("#triggerCode").val();
				triggerSeverity = $("#triggerSeverity").val();
				triggerTask = $("#triggerTask").val();
				var triggerData = {"title": triggerTitle, "condition": {"type": triggerType, "query": {"query": {"bool": {"must": [{"match": {"severity": triggerSeverity}},{"match": {"code": triggerCode}}]}}}, "job": {"Task": triggerTask}}}
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
		
		var getDialogBox = $("#getContainer").dialog({
			autoOpen: false,
			closeOnEscape: false,
			open: function(event, ui) {
				$(".ui-dialog-titlebar-close", ui.dialog | ui).hide();
			},
			height: 250,
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
					getID = $("#getID").val();			
					var pzGet = {"type": pzType, "action": pzAction};
					pzGet["data"] = {"id" : getID};
					pzSender(pzGet);
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
		$('getContainer').keypress( function(e) {
			if (e.charCode == 13 || e.keyCode == 13) {
				getID = $("#getID").val();			
				var pzGet = {"type": pzType, "action": pzAction};
				pzGet["data"] = {"id" : getID};
				pzSender(pzGet);
				$(this).dialog("close");
				map.dragging.enable();
				map.doubleClickZoom.enable();
				e.preventDefault();	
			}
		});
		
		var deleteDialogBox = $("#deleteContainer").dialog({
			autoOpen: false,
			closeOnEscape: false,
			open: function(event, ui) {
				$(".ui-dialog-titlebar-close", ui.dialog | ui).hide();
			},
			height: 250,
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
					deleteID = $("#deleteID").val();			
					var pzDelete = {"type": pzType, "action": pzAction};
					pzGet["data"] = {"id" : deleteID};
					pzSender(pzDelete);
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
		$('deleteContainer').keypress( function(e) {
			if (e.charCode == 13 || e.keyCode == 13) {
				deleteID = $("#deleteID").val();			
				var pzDelete = {"type": pzType, "action": pzAction};
				pzGet["data"] = {"id" : deleteID};
				pzSender(pzDelete);
				$(this).dialog("close");
				map.dragging.enable();
				map.doubleClickZoom.enable();
				e.preventDefault();	
			}
		});
		/*
		var triggerIdDialogBox = $("#triggerContainerID").dialog({
			autoOpen: false,
			closeOnEscape: false,
			open: function(event, ui) {
				$(".ui-dialog-titlebar-close", ui.dialog | ui).hide();
			},
			height: 500,
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
					triggerTitle = $("#triggerTitleID").val();
					triggerType = $("#triggerTypeID").val();
					triggerCode = $("#triggerCodeID").val();
					triggerSeverity = $("#triggerSeverityID").val();
					triggerTask = $("#triggerTaskID").val();
					var triggerData = {"title": triggerTitle, "condition": {"type": triggerType, "query": {"query": {"bool": {"must": [{"match": {"severity": triggerSeverity}},{"match": {"code": triggerCode}}]}}}, "job": {"Task": triggerTask}}};
					if($("#triggerIdID").val() != "") {
						triggerId = $("#triggerIdID").val();
						triggerData["id"] = $("#triggerIdID").val();
					}
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
		$('triggerContainerID').keypress( function(e) {
			if (e.charCode == 13 || e.keyCode == 13) {
				triggerTitle = $("#triggerTitleID").val()
				triggerType = $("#triggerTypeID").val();
				triggerCode = $("#triggerCodeID").val();
				triggerSeverity = $("#triggerSeverityID").val();
				triggerTask = $("#triggerTaskID").val();
				var triggerData = {"title": triggerTitle, "condition": {"type": triggerType, "query": {"query": {"bool": {"must": [{"match": {"severity": triggerSeverity}},{"match": {"code": triggerCode}}]}}}, "job": {"Task": triggerTask}}};
				if($("#triggerIdID").val() != "") {
					triggerId = $("#triggerIdID").val();
					triggerData["id"] = $("#triggerIdID").val();
				}
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
		*/
		var eventDialogBox = $("#eventContainer").dialog({
			autoOpen: false,
			closeOnEscape: false,
			open: function(event, ui) {
				$(".ui-dialog-titlebar-close", ui.dialog | ui).hide();
			},
			height: 425,
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
					eventType = $("#eventType").val();
					eventDate = $("#eventDate").val();
					eventFilename = $("#eventFilename").val();
					eventCode = $("#eventCode").val();
					eventSeverity = $("#eventSeverity").val();
					var pzData = {"type": eventType, "date": eventDate, "data": {"filename": eventFilename, "code": eventCode, "severity": parseInt(eventSeverity)}}
					var pzEvent = {"type": pzType, "data": pzData, "action": pzAction};
					if(pzAction == 'post') {
						pzEvent["eventname"] = pzEventtypes[eventType];
						console.log(pzEventtypes[eventType]);
					}
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
				eventType = $("#eventType").val();
				eventDate = $("#eventDate").val();
				eventFilename = $("#eventFilename").val();
				eventCode = $("#eventCode").val();
				eventSeverity = $("#eventSeverity").val();
				var pzData = {"type": eventType, "date": eventDate, "data": {"filename": eventFilename, "code": eventCode, "severity": eventSeverity}}
				var pzEvent = {"type": pzType, "data": pzData, "action": pzAction};
				if(pzAction == 'post') {
					pzEvent["eventname"] = pzEventtypes[eventType];
					console.log(pzEventtypes[eventType]);
				}
				console.log(pzEvent);
				console.log(pzData);
				pzSender(pzEvent);
				$(this).dialog("close");
				map.dragging.enable();
				map.doubleClickZoom.enable();
				e.preventDefault();	
			}
		});
		/*
		var eventIdDialogBox = $("#eventContainerID").dialog({
			autoOpen: false,
			closeOnEscape: false,
			open: function(event, ui) {
				$(".ui-dialog-titlebar-close", ui.dialog | ui).hide();
			},
			height: 500,
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
					eventType = $("#eventTypeID").val();
					eventDate = $("#eventDateID").val();
					eventFilename = $("#eventFilenameID").val();
					eventCode = $("#eventCodeID").val();
					eventSeverity = $("#eventSeverityID").val();
					var pzData = {"type": eventType, "date": eventDate, "data": {"filename": eventFilename, "code": eventCode, "severity": eventSeverity}}
					
					if ($("#eventIdID").val() != "") {
						eventId = $("#eventIdID").val();
						pzData["id"] = eventId;
					}
					var pzEvent = {"type": pzType, "data": pzData, "action": pzAction};
					if(pzAction == 'delete') {
						pzEvent['eventname'] = pzEventtypes[eventType];
					}
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
		$('eventContainerID').keypress( function(e) {
			if (e.charCode == 13 || e.keyCode == 13) {
				eventType = $("#eventTypeID").val();
				eventDate = $("#eventDateID").val();
				eventFilename = $("#eventFilenameID").val();
				eventCode = $("#eventCodeID").val();
				eventSeverity = $("#eventSeverityID").val();
				var pzData = {"type": eventType, "date": eventDate, "data": {"filename": eventFilename, "code": eventCode, "severity": eventSeverity}}
				if ($("#eventIdID").val() != "") {
					eventId = $("#eventIdID").val();
					pzData["id"] = eventId;
				}
				var pzEvent = {"type": pzType, "data": pzData, "action": pzAction};
				if(pzAction == 'delete') {
					pzEvent['eventname'] = pzEventtypes[eventType];
				}
				console.log(pzEvent);
				console.log(pzData);
				pzSender(pzEvent);
				$(this).dialog("close");
				map.dragging.enable();
				map.doubleClickZoom.enable();
				e.preventDefault();	
			}
		});
		*/
		var eventtypesDialogBox = $("#eventtypesContainer").dialog({
			autoOpen: false,
			closeOnEscape: false,
			open: function(event, ui) {
				$(".ui-dialog-titlebar-close", ui.dialog | ui).hide();
			},
			height: 375,
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
					eventtypesName = $("#eventtypesName").val();
					eventtypesFilename = $("#eventtypesFilename").val();
					eventtypesSeverity = $("#eventtypesSeverity").val();
					eventtypesCode = $("#eventtypesCode").val();
					var pzData = {"name": eventtypesName, "mapping": {"filename": eventtypesFilename, "severity": eventtypesSeverity, "code": eventtypesCode}};
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
		$('eventtypesContainer').keypress( function(e) {
			if (e.charCode == 13 || e.keyCode == 13) {
				eventtypesName = $("#eventtypesName").val();
				eventtypesFilename = $("#eventtypesFilename").val();
				eventtypesSeverity = $("#eventtypesSeverity").val();
				eventtypesCode = $("#eventtypesCode").val();
				var pzData = {"name": eventtypesName, "mapping": {"filename": eventtypesFilename, "severity": eventtypesSeverity, "code": eventtypesCode}};
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
		/*
		var eventtypesIdDialogBox = $("#eventtypesContainerID").dialog({
			autoOpen: false,
			closeOnEscape: false,
			open: function(event, ui) {
				$(".ui-dialog-titlebar-close", ui.dialog | ui).hide();
			},
			height: 425,
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
					eventtypesName = $("#eventtypesName").val();
					eventtypesFilename = $("#eventtypesFilename").val();
					eventtypesSeverity = $("#eventtypesSeverity").val();
					eventtypesCode = $("#eventtypesCode").val();
					var pzData = {"name": eventtypesName, "mapping": {"filename": eventtypesFilename, "severity": eventtypesSeverity, "code": eventtypesCode}};
					if ($("#eventtypesId").val() != "") {
						console.log("Should be working");
						eventtypesId = $("#eventtypesId").val();
						pzData["id"] = eventtypesId;
					}
					console.log("Should be below me");
					console.log($("#eventtypesId").val());
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
		$('eventtypesContainerID').keypress( function(e) {
			if (e.charCode == 13 || e.keyCode == 13) {
				eventtypesName = $("#eventtypesName").val();
				eventtypesFilename = $("#eventtypesFilename").val();
				eventtypesSeverity = $("#eventtypesSeverity").val();
				eventtypesCode = $("#eventtypesCode").val();
				var pzData = {"name": eventtypesName, "mapping": {"filename": eventtypesFilename, "severity": eventtypesSeverity, "code": eventtypesCode}};
				if ($("#eventtypesId").val() != "") {
					console.log("Should be working");
					eventtypesId = $("#eventtypesId").val();
					pzData["id"] = eventtypesId;
				}
				console.log("Should be below me");
				console.log($("#eventtypesId").val());
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
		*/
		var alertDialogBox = $("#alertContainer").dialog({
			autoOpen: false,
			closeOnEscape: false,
			open: function(event, ui) {
				$(".ui-dialog-titlebar-close", ui.dialog | ui).hide();
			},
			height: 300,
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
				//alertId = $("#alertId").val();
				alertTriggerId = $("#alertTriggerId").val();
				alertEventId = $("#alertEventId").val();
				var alertData = {"trigger_id": alertTriggerId, "event_id": alertEventId}
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
		/*
		var alertIdDialogBox = $("#alertContainerID").dialog({
			autoOpen: false,
			closeOnEscape: false,
			open: function(event, ui) {
				$(".ui-dialog-titlebar-close", ui.dialog | ui).hide();
			},
			height: 325,
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
					alertTriggerId = $("#alertTriggerIdID").val();
					alertEventId = $("#alertEventIdID").val();
					var alertData = {"trigger_id": alertTriggerId, "event_id": alertEventId}
					if ($("#alertIdID").val() != "") {
						alertId = $("#alertIdID").val();
						alertData["id"] = alertId;
					}
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
		$('alertContainerID').keypress( function(e) {
			if (e.charCode == 13 || e.keyCode == 13) {
				alertTriggerId = $("#alertTriggerIdID").val();
				alertEventId = $("#alertEventIdID").val();
				var alertData = {"trigger_id": alertTriggerId, "event_id": alertEventId}
				if ($("#alertIdID").val() != "") {
					alertId = $("#alertIdID").val();
					alertData["id"] = alertId;
				}
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
		*/
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

		//});
		/*
		function onEventAdd(name) {
			console.log("Adding");
			activeLayers[name] = null;
			bounds = fetchBounds(pzEvents[name]);
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
				if (key in pzEvents) {
					bounds = fetchBounds(pzEvents[key]);
				}
			}
			// If removing only layer: remove legend, else: remove and add new version //
			legend.removeFrom(map);
			if(Object.keys(activeLayers).length != 0) {
				legend.addTo(map);
			};
		}; */
		setInterval(function(pzrequest) {
			if(Object.keys(pzTriggers).length != 0) {
				console.log("Getting alerts");
				pzrequest = {"action": "get_all", "data": {}, "type": "alert"};
				pzChecker(pzrequest);
			}
			else {
				console.log("No triggers in list");
			}
		}, 30000);
		
		function pzChecker(pzrequest) {
			var csrftoken = getCookie('csrftoken');
			var requestStr = JSON.stringify(pzrequest);
			$.ajax({
				url: '/fulcrum_pzworkflow',
				type: "POST",
				data: requestStr,
				contentType: "application/json",
				processData: false,
				dataType: "json",
				success: function(result) {
					console.log("Alert request successful");
					findEvents(result);
				},
				error: function(result) {
					console.log("Error with alert request");
					return result;
				},
				beforeSend: function(xhr, settings) {
					if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
						xhr.setRequestHeader("X-CSRFToken", csrftoken);
					}
				}
			});
		};
		function findEvents(result) {
			if (Object.keys(result).length != 0) {
				console.log("Finding triggers in alerts");
				$.each(result, function (index, value) {
					console.log(value["trigger_id"]);
					if(value["trigger_id"] in pzTriggers) {
						console.log(value["trigger_id"] + " is a listed Trigger, checking against events");
						if (value["event_id"] in pzEvents) {
							console.log("Event already listed, moving on");
						}
						else {
							console.log("Event not listed, going to get event");
							addEvent(value["event_id"]);
						}
					}
				});
			}
			else {
				console.log("No alerts to iterate through");
			}
		}
		
		function addEvent(id) {
			var csrftoken = getCookie('csrftoken');
			var requestStr = JSON.stringify({"type": "event", "data": {"id": id}, "action": "get"});
			$.ajax({
				url: '/fulcrum_pzworkflow',
				type: "POST",
				data: requestStr,
				contentType: "application/json",
				processData: false,
				dataType: "json",
				success: function(result) {
					console.log("Event request successful");
					$('<div></div>').dialog({
						autoOpen: true,
						//maxWidth: 450,
						maxHeight: 600,
						width: 400,
						modal: false,
						appendTo: '#map',
						position: {
							my: "left top",
							at: "right bottom",
							of: placeholder
						},
						title: "Event matching one of your triggers!",
						open: function () {
							map.dragging.disable();
							map.doubleClickZoom.disable();
							map.scrollWheelZoom.disable();
							var contentStr = '<pre style="text-align: left;">' + JSON.stringify(result, undefined, 2) + '</pre><br/>';
							$(this).html(contentStr);
						},
						buttons: {
							Close: function () {
								$(this).dialog("close");
								map.dragging.enable();
								map.doubleClickZoom.enable();
								map.scrollWheelZoom.enable();
							}
						}
					}); 
						pzEvents[id] = id;
				},
				error: function(result) {
					console.log("Error getting event");
					console.log(result);
				},
				beforeSend: function(xhr, settings) {
					if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
						xhr.setRequestHeader("X-CSRFToken", csrftoken);
					}
				}
			});
		};
		//// IF PULLING GEOJSON FROM WORKFLOW, WOULD HAVE USED THIS //
		/*function createEventLayer(result) {
			if (Object.keys(result['data']).length != 0) {
				if(!(result['id'] in pzEvents)) {
					console.log("Adding event to layer control");
					console.log(result['data']);
					var color = getRandomColor();
					layerStyles[result['id']] = {
						radius : 4,
						fillColor : color,
						color : "#000000",
						weight : 1, 
						opacity : 1,
						fillOpacity : 1
					}
					pzEvents[result['id']] = null;
					try {
						pzEvents[result['id']] = L.geoJson(result['data'], {
							pointToLayer: function(feature, latlng) {
								return L.circleMarker(latlng, layerStyles[result['id']]);
							}
						});
						layerControl.removeFrom(map);
						layerControl = L.control.groupedLayers(baseMaps, overlays).addTo(map);
					}
					catch(err) {
						console.log("Invalid geoJson object");
					}
				}
				else {
					console.log("This event already has a layer");
				}
			}
			else {
				console.log("Event has no data");
			}
		};
		*/
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
						alert("Unable to get alert service, re-check URL");
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
		
		function getCookie(name) {
				var cookieValue = null;
				if (document.cookie && document.cookie != '') {
					var cookies = document.cookie.split(';');
						for (var i = 0; i < cookies.length; i++) {
							var cookie = jQuery.trim(cookies[i]);
							// Does this cookie string begin with the name we want?
							if (cookie.substring(0, name.length + 1) == (name + '=')) {
								cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
								break;
							}
						}
				}
				return cookieValue;
			}
			
		function csrfSafeMethod(method) {
			// these HTTP methods do not require CSRF protection
			return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
		}
	
		// Gets randomized color for new layer //
		var approvedColors0 =[
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
		
		var approvedColors = [
			"#0000ff",
			"#a52a2a",
			"#00ffff",
			"#00008b",
			"#008b8b",
			"#a9a9a9",
			"#006400",
			"#bdb76b",
			"#8b008b",
			"#556b2f",
			"#ff8c00",
			"#9932cc",
			"#e9967a",
			"#9400d3",
			"#ff00ff",
			"#ffd700",
			"#008000",
			"#4b0082",
			"#f0e68c",
			"#add8e6",
			"#e0ffff",
			"#90ee90",
			"#d3d3d3",
			"#ffb6c1",
			"#ffffe0",
			"#00ff00",
			"#ff00ff",
			"#800000",
			"#000080",
			"#808000",
			"#ffa500",
			"#ffc0cb",
			"#800080",
			"#800080",
			"#c0c0c0",
			"#ffff00"
		]
		var colorix = 0;
		function getRandomColor() {
			if(colorix < approvedColors.length) {
				console.log(approvedColors[colorix]);
				return approvedColors[colorix++];
			}
			else {
				colorix = 1;
				console.log(approvedColors[colorix]);
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