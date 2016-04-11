	/*
				Copyright 2016, RadiantBlue Technologies, Inc.

				Licensed under the Apache License, Version 2.0 (the "License");
				you may not use this file except in compliance with the License.
				You may obtain a copy of the License at

				http://www.apache.org/licenses/LICENSE-2.0

				Unless required by applicable law or agreed to in writing, software
				distributed under the License is distributed on an "AS IS" BASIS,
				WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
				See the License for the specific language governing permissions and
				limitations under the License.
				*/

	"use strict";

	$(document).ready(function() {

		if (!Date.now) {
			Date.now = function() {
					return new Date().getTime()
				} //Time in milliseconds
		}

		var OpenStreetMap = L.tileLayer('http://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
			maxZoom: 18,
			attribution: 'Map data © <a href="http://openstreetmap.org">OpenStreetMap</a> contributors',
			id: 'mapbox.light'
		});

		var Esri_WorldImagery = L.tileLayer('http://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
			maxZoom: 18,
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
			center: [0, 0],
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

		// Empty layer list for any layers //
		var layers = {};

		// Pz alert markers //
		var markers = {};

		// // Track triggers posted by user //
		// if (typeof(Storage) != "undefined") {
		// 	if (sessionStorage.pzTriggers) {
		// 		var pzTriggers = JSON.parse(sessionStorage.pzTriggers);
		// 	} else {
		// 		var pzTriggers = {};
		// 	}
		// } else {
		// 	var pzTriggers = {};
		// }

		// // Empty list for any pz Events //
		// if (typeof(Storage) != "undefined") {
		// 	if (sessionStorage.pzEvents) {
		// 		var pzEvents = JSON.parse(sessionStorage.pzEvents);
		// 	} else {
		// 		var pzEvents = {};
		// 	}
		// } else {
		// 	var pzEvents = {};
		// }
		var pzTriggers = {};
		var pzEvents = {};

		var eventLayer;
		var eventLayerGeojson = {'type': 'FeatureCollection', 'features': [] };
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
			var SW = L.latLng(south, west)
			var NE = L.latLng(north, east);
			return L.latLngBounds(SW, NE);
		};

		var layerControl;

		// Gets list of available layers //
		$.ajax({
			url: '/pz_fulcrum_layers',
			dataType: "json",
			success: function(result) {
				updateLayers(result, true);
			}
		});

		setInterval(function() {
			$.ajax({
				url: '/pz_fulcrum_layers',
				dataType: "json",
				success: function(result) {
					//layerControl.removeFrom(map);
					//layerControl = null;
					updateLayers(result, false);
				}
			});
		}, 30000);

		// Update the layer control with any new layers //
		function updateLayers(result, firstcall) {
			for (var key in layers) {
				console.log(key);
			}
			for (var key in result) {
				console.log("looking at " + key);
				if (!(key in layers)) {
					console.log("not in layers");
					if (!(key in layerStyles)) {
						var color = getRandomColor();
						layerStyles[key] = {
							radius: 4,
							fillColor: color,
							color: "#000000",
							weight: 1,
							opacity: 1,
							fillOpacity: 1
						}
					};
					layers[key] = L.geoJson(false);
					layerUrls[key] = '/pz_fulcrum_geojson?layer=' + key;
					console.log(layerUrls[key]);
					if (firstcall == false) {
						layerControl.addOverlay(layers[key], key, "Fulcrum Layers");
					}
				}
			}
			if (firstcall == true) {
				layerControl = L.control.groupedLayers(baseMaps, overlays).addTo(map);
			}
		};

		$.ajax({
			url: '/pz_fulcrum_pzmodels',
			dataType: 'json',
			success: function(result) {
				console.log(result);
				console.log(typeof(result))
				var events = result['events'];
				var triggers = result['triggers'];
				var features = result['features'];
				console.log(features);
				for (var event_id in events) {
					pzEvents[event_id] = events[event_id];
				}
				for (var trigger_id in triggers) {
					pzTriggers[trigger_id] = triggers[trigger_id];
				}
				if (features.length > 0) {
					console.log("Features found");
					for (var feature in features) {
						//var json_feature = features[feature];//JSON.parse(features[feature]);
						eventLayerGeojson['features'].push(features[feature]);
					}
					console.log(eventLayerGeojson);
					eventLayer = L.geoJson(eventLayerGeojson, {
						onEachFeature: onEachEventFeature,
						pointToLayer: function(feature, latlng) {
							return L.circleMarker(latlng, {
								radius: 4,
								fillColor: "#e60000",
								color: "#000000",
								weight: 1,
								opacity: 1,
								fillOpacity: 1
							});
						}
					});
					layerControl.addOverlay(eventLayer, "PzEvents", "Fulcrum Layers");
				}
			}
		});

		// Listens for user selecting a layer from Layer Control //
		map.on('overlayadd', onOverlayAdd);

		// Find which layer was selected, get its data from URL, add it to the empty layer, and add the layer to the map //
		function onOverlayAdd(e) {
			var name = e["name"];
			// If its a subscribed layer, handle the process differently //
			if (name in subLayers) {
				onSubOverlayAdd(name);
			} 
			else if(name in layers) {
				console.log("Going to get: " + layerUrls[name]);
				$.ajax({
					url: layerUrls[name],
					dataType: "json",
					success: function(result) {
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
			if (Object.keys(activeLayers).length == 1) {
				legend.addTo(map);
			} else {
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
				filter: function(feature) {
					if (timeout != 0) {
						return feature.properties.time + (timeout * 60) > Math.floor(Date.now() / 1000);
					} else {
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
					url: layerUrls[key],
					dataType: "json",
					success: function(result) {
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
			if (name in subLayers) {
				onSubOverlayRemove(name);
			} 
			else if(name in layers) {
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
				if (Object.keys(activeLayers).length != 0) {
					legend.addTo(map);
				};
			}
		};

		// Create legend for active layers //
		var legend = L.control({
			position: 'bottomright'
		});

		legend.onAdd = function(map) {
			var div = L.DomUtil.create('div', 'legend');
			for (var key in activeLayers) {
				div.innerHTML +=
					'<div class="subdiv">' +
					'<i class="circle" style="background: ' + layerStyles[key].fillColor + '"></i> ' +
					'<span class="legend-lable">' + key + '</span><br>' + '</div>';
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
			} else {
				miniMap.removeFrom(map);
				miniMap = new L.Control.MiniMap(mini1).addTo(map);
			}
		});

		// Adds a popup with information for each point //
		//

		var popupProperties;

		function onEachFeature(feature, layer) {
			layer.on('click', function(e) {
				var genericStr = "";
				var titleStr = "";
				var idStr = "";
				var photosStr = "";
				var audioStr = "";
				var videosStr = "";
				for (var property in e.target.feature.properties) {

					if (String(property).toLowerCase().indexOf('name') > -1 || String(property).toLowerCase().indexOf('title') > -1) {
						titleStr += '<p><strong>' + property + ':</strong> ' + e.target.feature.properties[property] + '</p>'
					} else if (String(property).toLowerCase().indexOf('id') == 0) {
						idStr += '<p><strong>' + property + ':</strong> ' + e.target.feature.properties[property] + '</p>'
					} else if (String(property).indexOf('_url') > -1) {
						if (e.target.feature.properties[property] != null && e.target.feature.properties[property] != "") {
							var urls = String(e.target.feature.properties[property]).split(",");
							console.log(urls);
							for (var url in urls) {
								if (String(urls[url]).indexOf('.jpg') > -1) {
									photosStr += '<p><a href="' + urls[url] + '" target="_blank"><img src="' + urls[url] + '" style="width: 250px; height: 250px;"/></a></p>';
								}
								if (String(urls[url]).indexOf('.mp4') > -1) {
									videosStr += '<p><video width="250" height="250" controls><source src="' + urls[url] + '" type="video/mp4" target="_blank"></video></p>';
								}
								if (String(urls[url]).indexOf('.m4a') > -1) {
									audioStr += '<p><audio controls><source src="' + urls[url] + '" type="audio/mp4"></audio></p>';
								}
							}
						}
					} else {
						if (e.target.feature.properties[property] != null && e.target.feature.properties[property] != "") {
							genericStr += '<p><strong>' + property + ':</strong> ' + e.target.feature.properties[property] + '</p>';
						}
					}
				}

				// Get position for popup //
				var coords = [e.target.feature.geometry.coordinates[1], e.target.feature.geometry.coordinates[0]];

				//var triggerBuffer = '<p><button id="triggerBuffer">Create Buffer Trigger</button></p>';

				var triggerAttribute = '<p><button id="triggerAttribute">Create Trigger</button></p>';

				popupProperties = e.target.feature.properties;

				// Create popup and add to map //
				var popup = L.popup({
					maxHeight: 400,
					closeOnClick: false,
					keepInView: true
				}).setLatLng(coords).setContent(titleStr + idStr + genericStr + photosStr + videosStr + audioStr + triggerAttribute).openOn(map);
			});



		}

		map.on('popupopen', function(e) {
			var source = e;
			
			$("#removeFeature").on('click', function() {
				map.closePopup();
				removeFeature(popupProperties);
			});
			$("#triggerAttribute").on('click', function() {
				map.closePopup();
				openOnClickAttrTrigger(source, popupProperties)
			});
		});

		var attrFields = 0;

		function openOnClickAttrTrigger(source, popupProperties) {
			var buffer = false;
			var coords = [source.popup._latlng.lng, source.popup._latlng.lat];
			var selectOptions = '';
			for (var prop in popupProperties) {
				if (typeof(popupProperties[prop]) != 'object') {
					var json = {};
					json[prop] = popupProperties[prop];
					selectOptions += '<option>' + JSON.stringify(json) + '</option>';
				}
			}
			var onClickTriggerDialog = $('#onClickAttrTrigger').dialog({
				autoOpen: true,
				width: 600,
				maxHeight: 550,
				appendTo: '#map',
				modal: false,
				position: {
					my: "top",
					at: "bottom",
					of: $("#placeholder2")
				},
				open: function() {
					map.dragging.disable();
					map.doubleClickZoom.disable();
					map.scrollWheelZoom.disable();
					var contentStr = '<p><strong>Select attributes and get any <br/>Piazza Workflow events that match</strong></p>';
					contentStr += '<fieldset id="attrParentFieldset"><fieldset id="triggerAttrFieldset' + attrFields + '"><label for="attrField' + attrFields + '">Must Match:</label><br/><select id="attrField' + attrFields + '">' + selectOptions + '</select></fieldset></fieldset>';
					attrFields++;
					$(this).html(contentStr);
				},
				buttons: {
					"Submit": function() {
						submitOnClickAttrEvent(coords, buffer);
						$(this).dialog("close");
						map.dragging.enable();
						map.doubleClickZoom.enable();
						map.scrollWheelZoom.enable();
					},
					"Add Field": function() {
						$("#attrParentFieldset").append('<fieldset id="triggerAttrFieldset' + attrFields + '"><label for="attrField' + attrFields + '">Must Match:</label><br/><select id="attrField' + attrFields + '">' + selectOptions + '</select></fieldset>');
						attrFields++;
					},
					"Remove Field": function() {
						if (attrFields > 0) {
							$('#triggerAttrFieldset{0}'.format(attrFields - 1)).remove();
							attrFields--;
						}
					},
					"Add/Remove Buffer": function() {
						if (buffer == false) {
							var contentStr = '<fieldset id="triggerBufferFieldset">';
							contentStr += '<p><strong>Define a bounding box and get Piazza Workflow events<br/>within defined bounds</strong></p>';
							contentStr += '<label for="xTolerance">Longitude +/- Tolerance</label><br/><input type="number" id="xTolerance"/><br/><br/>';
							contentStr += '<label for="yTolerance">Latitude +/- Tolerance</label><br/><input type="number" id="yTolerance"/><br/><br/>'
							contentStr += '</fieldset>';
							$("#attrParentFieldset").prepend(contentStr);
							buffer = true;
						} else {
							$("#triggerBufferFieldset").remove();
							buffer = false;
						}
					},
					"Cancel": function() {
						$(this).dialog("close");
						map.dragging.enable();
						map.doubleClickZoom.enable();
						map.scrollWheelZoom.enable();
					}
				}
			});

			$('#onClickAttrTrigger').keypress(function(e) {
				if (e.charCode == 13 || e.keyCode == 13) {
					submitOnClickAttrEvent(coords, buffer);
					$(this).dialog("close");
					map.dragging.enable();
					map.doubleClickZoom.enable();
					map.scrollWheelZoom.enable();
				}
			});
		}

		
		function submitOnClickAttrEvent(coords, buffer) {
			var mapping = {
				'geometry-type': 'string'
			};
			var mustMatchQueries = [{
				'match': {
					'geometry-type': 'point'
				}
			}];
			if (buffer == true) {
				var xTolerance = parseFloat($("#xTolerance").val());
				var yTolerance = parseFloat($("#yTolerance").val());
				var coordTolerance = [xTolerance, yTolerance];
				mapping['lng'] = 'double';
				mapping['lat'] = 'double';
				mustMatchQueries.push({
					'range': {
						'lng': {
							'gte': coords[0] - coordTolerance[0],
							'lte': coords[0] + coordTolerance[0]
						}
					}
				});
				mustMatchQueries.push({
					'range': {
						'lat': {
							'gte': coords[1] - coordTolerance[1],
							'lte': coords[1] + coordTolerance[1]
						}
					}
				});
			}

			for (var i = 0; i < attrFields; i++) {
				var optionInput = $('#attrField{0}'.format(i)).val();
				var json = JSON.parse(optionInput);
				var matchItem = {
					"match": json
				};
				mustMatchQueries.push(matchItem);
				for (var key in json) {
					if (typeof(json[key]) == 'string') {
						mapping[key] = 'string';
					} else if (typeof(json[key]) == 'number') {
						if (Number.isInteger(json[key])) {
							mapping[key] = 'integer';

						} else {
							mapping[key] = 'double';
						}
					} else if (typeof json[key] == 'boolean') {
						mapping[key] = 'boolean'
					} else {
						mustMatchQueries.pop();
					}
				}
			}
			if (mustMatchQueries.length > 0 || buffer == true) {
				var pzEvent = {
					'type': 'eventtypes',
					'action': 'post'
				};
				var pzData = {
					'name': 'fulcrum-map-event',
					'mapping': mapping
				};
				pzEvent['data'] = pzData;
				console.log("Posting eventtype");
				console.log(pzEvent);
				onClickAttrEventPost(pzEvent, mustMatchQueries);
			}

		}

		function onClickAttrEventPost(pzrequest, mustMatchQueries) {
			var requestStr = JSON.stringify(pzrequest);
			var csrftoken = getCookie('csrftoken');
			console.log(requestStr);
			$.ajax({
				url: '/pz_fulcrum_pzworkflow',
				type: "post",
				data: requestStr,
				contentType: false,
				processData: false,
				dataType: "json",
				success: function(result) {
					console.log('sucess');
					submitOnClickAttr(result, mustMatchQueries);
				},
				error: function(result) {
					console.log(result);
				},
				beforeSend: function(xhr, settings) {
					if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
						xhr.setRequestHeader("X-CSRFToken", csrftoken);
					}
				}
			});
		}

		function submitOnClickAttr(result, mustMatchQueries) {
			if ('id' in result) {
				var pzData = {
					'title': 'fulcrum-map-event',
					'condition': {
						'eventtype_id': result['id'],
						'query': {
							'query': {
								'bool': {
									'must': mustMatchQueries
								}
							}
						},
						'job': {
							'task': 'None'
						}
					}
				};
				var pzEvent = {
					"type": "trigger",
					"data": pzData,
					"action": "post"
				};
			}
			onClickTriggerPost(pzEvent);
		}

		function onClickTriggerPost(pzrequest) {
			var requestStr = JSON.stringify(pzrequest);
			var csrftoken = getCookie('csrftoken');
			console.log(requestStr);
			$.ajax({
				url: '/pz_fulcrum_pzworkflow',
				type: "POST",
				data: requestStr,
				contentType: false,
				processData: false,
				dataType: "json",
				success: function(result) {
					console.log("Success");
					storePzTrigger(result['id'], result);
				},
				error: function(result) {
					console.log(result);
				},
				beforeSend: function(xhr, settings) {
					if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
						xhr.setRequestHeader("X-CSRFToken", csrftoken);
					}
				}
			});
		}

		// Symbolizes new points in red, old points in grey //
		function Markers(feature, key) {


			if (feature.properties.time + (colortime * 60) > Math.round(Date.now() / 1000.0) && colortime > 0) {
				return {
					radius: 5,
					fillColor: "#e60000",
					color: "#000000",
					weight: 1,
					opacity: 1,
					fillOpacity: 1
				}
			} else {
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
		if (typeof(Storage) != "undefined") {
			if (sessionStorage.timeout) {
				var timeout = parseInt(sessionStorage.timeout);
			} else {
				sessionStorage.timeout = "0";
				timeout = 0;
			}
		} else {
			var timeout = 0;
		}
		document.getElementById("timeout").value = timeout;
		var getTimeout = $(function() {

			var TimeDialogBox = $("#timeoutForm").dialog({
				autoOpen: false,
				closeOnEscape: false,
				open: function(event, ui) {
					$(".ui-dialog-titlebar-close", ui.dialog | ui).hide();
					closeDialogs("#timeoutForm");
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
						if (isNaN(inNum) || inNum < 0 || inNum == "") {
							timeout = 0;
							document.getElementById("timeout").value = timeout;
							sessionStorage.timeout = timeout;
						} else {
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

			$('#timeoutForm').keypress(function(e) {
				if (e.charCode == 13 || e.keyCode == 13) {
					var inNum = parseInt($("#timeout").val());
					if (isNaN(inNum) || inNum < 0 || inNum == "") {
						timeout = 0;
						document.getElementById("timeout").value = timeout;
						sessionStorage.timeout = timeout;
					} else {
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
		if (typeof(Storage) != "undefined") {
			if (sessionStorage.colortime) {
				var colortime = parseInt(sessionStorage.colortime);
			} else {
				sessionStorage.colortime = "0";
				colortime = 0;
			}
		} else {
			var colortime = 0;
		}
		document.getElementById("colortime").value = colortime;
		var getColortime = $(function() {

			var colorDialogBox = $("#colortimeForm").dialog({
				autoOpen: false,
				closeOnEscape: false,
				open: function(event, ui) {
					$(".ui-dialog-titlebar-close", ui.dialog | ui).hide();
					closeDialogs("#colortimeForm");
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
						if (isNaN(inNum) || inNum < 0 || inNum == '') {
							colortime = 0;
							document.getElementById("colortime").value = colortime;
							sessionStorage.colortime = colortime;
						} else {
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

			$('#colortimeForm').keypress(function(e) {
				if (e.charCode == 13 || e.keyCode == 13) {
					var inNum = parseInt($("#colortime").val());
					if (isNaN(inNum) || inNum < 0 || inNum == "") {
						colortime = 0;
						document.getElementById("colortime").value = colortime;
						sessionStorage.colortime = colortime;
					} else {
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
		if (typeof(Storage) != "undefined") {
			if (sessionStorage.refresh) {
				refresh = parseInt(sessionStorage.refresh);
			} else {
				sessionStorage.refresh = "60";
				refresh = 60;
			}
		} else {
			refresh = 60;
		}
		document.getElementById("refresh").value = refresh;
		var getRefresh = $(function() {

			var refreshDialogBox = $("#refreshForm").dialog({
				autoOpen: false,
				closeOnEscape: false,
				open: function(event, ui) {
					$(".ui-dialog-titlebar-close", ui.dialog | ui).hide();
					closeDialogs("#refreshForm");
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
						if (isNaN(inNum) || inNum <= 0 || inNum == "") {
							refresh = 60;
							document.getElementById("refresh").value = refresh;
							sessionStorage.refresh = refresh;
						} else {
							refresh = inNum;
							sessionStorage.refresh = inNum;

						}
						for (var key in activeLayers) {
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

			$('#refreshForm').keypress(function(e) {
				if (e.charCode == 13 || e.keyCode == 13) {
					var inNum = parseInt($("#refresh").val());
					if (isNaN(inNum) || inNum < 0 || inNum == "") {
						refresh = 60;
						document.getElementById("refresh").value = refresh;
						sessionStorage.refresh = refresh;
					} else {
						refresh = inNum;
						sessionStorage.refresh = inNum;
					}
					for (var key in activeLayers) {
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
		var uploadForm = (function() {
			map.dragging.enable();
			map.doubleClickZoom.enable();
			if ($('#uploadFormButton').val() != '' && $('#uploadFormButton').val() != null) {
				var formData = new FormData($('#fileUpload')[0]);
				$.ajax({
					url: '/pz_fulcrum_upload', //Server script to process data
					type: 'POST',
					xhr: function() { // Custom XMLHttpRequest
						var myXhr = $.ajaxSettings.xhr();
						if (myXhr.upload) { // Check if upload property exists
							myXhr.upload.addEventListener('progress', progressHandlingFunction, false); // For handling the progress of the upload
							myXhr.upload.addEventListener('progress', progressFinishedFunction, false); // If progress is finished, close file upload dialog
						}
						return myXhr;
					},
					// Ajax events //
					beforeSend: console.log("Sending"),
					// Adds layer to the map //
					success: function(result) {
						document.getElementById('waiting').style.visibility = 'hidden';
						for (var key in result) {
							// If layer already exists, remove first, then add new version //
							if (key in layers) {
								map.removeLayer(layers[key]);
								layerControl.removeLayer(key);
								delete layers[key];
								if (key in activeLayers) {
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
			}
			else {
				console.log("No file selected");
			}
		});

		// For progress bar ..
		function progressHandlingFunction(e) {
			if (e.lengthComputable) {
				$('progress').attr({
					value: e.loaded,
					max: e.total
				});
			}
		}

		function progressFinishedFunction(e) {
			if (e.lengthComputable) {
				if (e.loaded == e.total) {
					$("#formContainer").dialog("close");
					$('progress').attr({
						value: 0.0,
						max: 1.0
					});
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
				closeDialogs("#formContainer");
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
		$('#formContainer').keypress(function(e) {
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
		var deleteID;
		var deleteEventName;

		var triggerId;
		var triggerTitle;
		var triggerType;
		var triggerTask;

		var eventId;
		var eventType;
		var eventDate;

		var alertId;
		var alertTriggerId;
		var alertEventId;


		var pzDialogBox = $("#pzContainer").dialog({
			autoOpen: false,
			closeOnEscape: false,
			open: function(event, ui) {
				$(".ui-dialog-titlebar-close", ui.dialog | ui).hide();
				closeDialogs("#pzContainer");
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
				"Manager": function() {
					$(this).dialog("close");
					$('#Manager').dialog("open");
				}
			},
		});

		$('#pzContainer').keypress(function(e) {
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
			open: function() {
				var contentStr = "";
				var i = 0;
				for (var key in pzEvents) {
					contentStr += '<input type="radio" id="' + i + '" name="choice" value="' + key + '" style="float: left; margin-left: 30%;"/><label for="' + i + '" style="float: left;">Event: ' + key + '</label><br/>';
					i++;
				}
				for (var key in pzTriggers) {
					contentStr += '<input type="radio" id="' + i + '" name="choice" value="' + key + '" style="float: left; margin-left: 30%;"/><label for="' + i + '" style="float: left;">Trigger: ' + key + '</label><br/>';
					i++;
				}
				$(this).html(contentStr);
			},
			buttons: {
				"Delete": function() {
					deleteManager();
					$(this).dialog("close");
				},
				"Cancel": function() {
					$(this).dialog("close");
					map.dragging.enable();
					map.doubleClickZoom.enable();
				}
			}
		});

		function deleteManager() {
			var choice = $('input[name="choice"]:checked').val();
			if (choice in pzEvents) {
				deleteEvent(choice);
			}
			if (choice in pzTriggers) {
				deleteTrigger(choice);
			}
		}

		function deleteEvent(choice) {
			pzEvents[choice] = null;
			delete pzEvents[choice];
			var pz_delete = {'delete': {'events':{}}};
			pz_delete['delete']['events'][choice] = null;
			postPzModel(pz_delete);
			map.dragging.enable();
			map.doubleClickZoom.enable();
		}

		function deleteTrigger(choice) {
			pzTriggers[choice] = null;
			delete pzTriggers[choice];
			var pz_delete = {'delete': {'triggers':{}}};
			pz_delete['delete']['triggers'][choice] = null;
			postPzModel(pz_delete);
			map.dragging.enable();
			map.doubleClickZoom.enable();
		}

		function pzHandler(type, action) {
			if (action == 'get_all') {
				map.dragging.enable();
				map.doubleClickZoom.enable();
				var request = {
					"type": type,
					"data": {},
					"action": action
				};
				pzSender(request);
			} else if (action == 'get') {
				$("#getContainer").dialog("open");
			} else if (action == 'delete') {
				$("#deleteContainer").dialog("open");
			} else {
				if (type == 'eventtypes') {
					$("#postEventtype").dialog("open");
				} else if (type == 'trigger') {
					$("#postTrigger").dialog("open");
				} else if (type == 'event') {
					$("#postEvent").dialog("open");
				} else if (type == 'alert') {
					$("#alertContainer").dialog("open");
				}
			}
		}

		function pzSender(pzrequest) {
			var requestStr = JSON.stringify(pzrequest);
			var csrftoken = getCookie('csrftoken');
			console.log(requestStr);
			$.ajax({
				url: '/pz_fulcrum_pzworkflow',
				type: "POST",
				data: requestStr,
				contentType: false,
				processData: false,
				dataType: "json",
				success: function(result) {
					console.log("Success");
					pzResponse(result, pzrequest);
				},
				error: function(result) {
					pzError(result);
				},
				beforeSend: function(xhr, settings) {
					if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
						xhr.setRequestHeader("X-CSRFToken", csrftoken);
					}
				}
			});
		};

		function pzResponse(result, pzrequest) {
			if (pzAction == 'delete') {
				if (result == null) {
					console.log("Delete was successful");
				} else {
					console.log("Delete failed")
					console.log(result);
				}
			} else if (pzAction == 'get') {
				console.log(result);
				if (pzType == 'event') {
					storePzEvent(result['id'], result);
				}
				if (pzType == 'trigger') {
					storePzTrigger(result['id'], result);
				}
			} else if (pzAction == 'get_all') {
				getDialog(result)
			} else if (pzAction == 'post') {
				if (result == null) {
					console.log("Not created");
				} else {
					if (pzType == 'trigger') {
						storePzTrigger(result['id'], result);
						console.log(pzTriggers);
					} else if (pzType == 'event') {
						storePzEvent(result['id'], pzrequest['data']);
					} else {
						console.log(result);
					}
				}
			}
		}

		function getDialog(result) {
			$('<div></div>').dialog({
				autoOpen: true,
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
				open: function() {
					map.dragging.disable();
					map.doubleClickZoom.disable();
					map.scrollWheelZoom.disable();
					var contentStr = "";
					$.each(result, function(index, value) {
						contentStr += '<pre style="text-align: left;">' + JSON.stringify(value, undefined, 2) + '</pre><br/>';
					});
					$(this).html(contentStr);
				},
				buttons: {
					Close: function() {
						$(this).dialog("close");
						map.dragging.enable();
						map.doubleClickZoom.enable();
						map.scrollWheelZoom.enable();
					}
				}
			});
		}

		function pzError(result) {
			console.log("Request failed");
			console.log(result);
		}

		var getDialogBox = $("#getContainer").dialog({
			autoOpen: false,
			closeOnEscape: false,
			open: function(event, ui) {
				$(".ui-dialog-titlebar-close", ui.dialog | ui).hide();
			},
			height: 200,
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
					var pzGet = {
						"type": pzType,
						"action": pzAction
					};
					pzGet["data"] = {
						"id": getID
					};
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
		$('#getContainer').keypress(function(e) {
			if (e.charCode == 13 || e.keyCode == 13) {
				getID = $("#getID").val();
				var pzGet = {
					"type": pzType,
					"action": pzAction
				};
				pzGet["data"] = {
					"id": getID
				};
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
			height: 200,
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
					var pzDelete = {
						"type": pzType,
						"action": pzAction
					};
					pzDelete["data"] = {
						"id": deleteID
					};
					pzSender(pzDelete);
					$(this).dialog("close");
					map.dragging.enable();
					map.doubleClickZoom.enable();
					if (pzType == "event") {
						if (deleteID in pzEvents) {
							delete pzEvents[deleteID];
							var pz_delete = {'delete': {'events': {}}};
							pz_delete['delete']['events'][deleteID] = null;
							postPzModel(pz_delete);
						}
					}
					if (pzType == "trigger") {
						if (deleteID in pzTriggers) {
							delete pzTriggers[deleteID];
							var pz_delete = {'delete': {'triggers':{}}};
							pz_delete['delete']['triggers'][deleteID] = null;
							postPzModel(pz_delete);
						}
					}
				},
				"Cancel": function() {
					$(this).dialog("close");
					map.dragging.enable();
					map.doubleClickZoom.enable();
				}
			},
		});
		$('#deleteContainer').keypress(function(e) {
			if (e.charCode == 13 || e.keyCode == 13) {
				deleteID = $("#deleteID").val();
				var pzDelete = {
					"type": pzType,
					"action": pzAction
				};
				pzDelete["data"] = {
					"id": deleteID
				};
				pzSender(pzDelete);
				$(this).dialog("close");
				map.dragging.enable();
				map.doubleClickZoom.enable();
				if (pzType == "event") {
					if (deleteID in pzEvents) {
						delete pzEvents[deleteID];
						var pz_delete = {'delete': {'events':{}}};
						pz_delete['delete']['events'][deleteID] = null;
						postPzModel(pz_delete);
					}
				}
				if (pzType == "trigger") {
					if (deleteID in pzTriggers) {
						delete pzTriggers[deleteID];
						var pz_delete = {'delete': {'triggers':{}}};
						pz_delete['delete']['triggers'][deleteID] = null;
						postPzModel(pz_delete);
					}
				}
				e.preventDefault();
			}
		});

		var triggerFields = 0;
		var triggerMaxFields = 10;
		var postTriggerDialog = $('#postTrigger').dialog({
			autoOpen: false,
			width: 400,
			maxHeight: 620,
			height: 'auto',
			appendTo: '#map',
			modal: false,
			position: {
				my: "left top",
				at: "right bottom",
				of: placeholder
			},
			open: function() {
				map.scrollWheelZoom.disable();
				var contentStr = '<fieldset id="triggerFieldset">';
				contentStr += '<label for="triggerTitle">Title</label><br/><input type="text" id="triggerTitle" class="text ui-widget-content ui-corner-all"/><br/>';
				contentStr += '<label for="triggerType">EventType ID</label><br/><input type="text" id="triggerType" class="text ui-widget-content ui-corner-all"/><br/>';
				contentStr += '<label for="triggerTask">Task</label><br/><input type="text" id="triggerTask" class="text ui-widget-content ui-corner-all"/>'
				contentStr += '<p>Querys</p></fieldset>';
				$(this).html(contentStr);
			},
			buttons: {
				"Submit": function() {
					submitTrigger();
					$(this).dialog("close");
				},
				"Add Query": function() {
					if (triggerFields < triggerMaxFields) {
						$("#triggerFieldset").append('<fieldset><select id="triggerClause' + triggerFields + '">' +
							'<option value = "must">must</option>' +
							'<option value = "filter">filter</option>' +
							'<option value = "must_not">must_not</option>' +
							'<option value = "should">should</option>' +
							'</select>' +
							'<select id="triggerTerm' + triggerFields + '">' +
							'<option value = "match">match</option>' +
							'<option value = "term">term</option>' +
							'</select><br/>' +
							'<label for="queryKey' + triggerFields + '">Key</label><br/><input type="text" id="queryKey' + triggerFields + '" class="text ui-widget-content ui-corner-all"><br/>' +
							'<label for="queryValue' + triggerFields + '">Value</label><br/><input type="text" id="queryValue' + triggerFields + '" class="text ui-widget-content ui-corner-all">' +
							'</fieldset>');
						triggerFields++;
					}
				},
				"Cancel": function() {
					$(this).dialog("close");
					map.dragging.enable();
					map.doubleClickZoom.enable();
					map.scrollWheelZoom.enable();
					triggerFields = 0;
				}
			}
		});

		$('#postTrigger').keypress(function(e) {
			if (e.charCode == 13 || e.keyCode == 13) {
				submitTrigger();
				$(this).dialog("close");
				e.preventDefault();
			}
		});

		function submitTrigger() {
			triggerTitle = $("#triggerTitle").val();
			triggerType = $("#triggerType").val();
			triggerTask = $("#triggerTask").val();
			var pzBool = {};
			var must = [];
			var filter = [];
			var must_not = [];
			var should = [];
			for (var i = 0; i < triggerFields; i++) {
				var clause = $("#triggerClause{0}".format(i)).val();
				var term = $("#triggerTerm{0}".format(i)).val();
				var key = $("#queryKey{0}".format(i)).val();
				var value = $("#queryValue{0}".format(i)).val();
				if (clause == 'must') {
					var termJson = {};
					termJson[key] = value;
					var clauseJson = {};
					clauseJson[term] = termJson;
					must.push(clauseJson);
				} else if (clause == 'filter') {
					var termJson = {};
					termJson[key] = value;
					var clauseJson = {};
					clauseJson[term] = termJson;
					filter.push(clauseJson);
				} else if (clause == 'must_not') {
					var termJson = {};
					termJson[key] = value;
					var clauseJson = {};
					clauseJson[term] = termJson;
					must_not.push(clauseJson);
				} else {
					var termJson = {};
					termJson[key] = value;
					var clauseJson = {};
					clauseJson[term] = termJson;
					should.push(clauseJson);
				}
			}
			if (must.length > 0) {
				pzBool['must'] = must;
			}
			if (filter.length > 0) {
				pzBool['filter'] = filter;
			}
			if (must_not.length > 0) {
				pzBool['must_not'] = must_not;
			}
			if (should.length > 0) {
				pzBool['should'] = should;
			}

			var pzData = {
				'title': triggerTitle,
				'condition': {
					'eventtype_id': triggerType,
					'query': {
						'query': {
							'bool': pzBool
						}
					},
					'job': {
						'task': triggerTask
					}
				}
			};
			var pzEvent = {
				"type": pzType,
				"data": pzData,
				"action": pzAction
			};
			console.log(pzEvent);
			console.log(pzData);
			pzSender(pzEvent);
			map.dragging.enable();
			map.doubleClickZoom.enable();
			map.scrollWheelZoom.enable();
			triggerFields = 0;
		}

		var eventFields = 0;
		var eventMaxFields = 10;
		var postEventDialog = $('#postEvent').dialog({
			autoOpen: false,
			width: 400,
			maxHeight: 620,
			height: 'auto',
			appendTo: '#map',
			modal: false,
			position: {
				my: "left top",
				at: "right bottom",
				of: placeholder
			},
			open: function() {
				map.scrollWheelZoom.disable();
				var contentStr = '<fieldset id="eventFieldset">';
				contentStr += '<label for="eventType">EventType ID  </label><br/><input type="text" id="eventType" class="text ui-widget-content ui-corner-all"/><br/><br/>';
				contentStr += '<label for="eventDate">Date  </label><br/><input type="text" id="eventDate" class="text ui-widget-content ui-corner-all"/><br/>';
				contentStr += '<p>Event Data</p></fieldset>';
				$(this).html(contentStr);
			},
			buttons: {
				"Submit": function() {
					submitEvent();
					$(this).dialog("close");
				},
				"Add Data Field": function() {
					if (eventFields < eventMaxFields) {
						$("#eventFieldset").append('<fieldset><label for="eventKey' + eventFields + '">Key</label><br/><input type="text" id="eventKey' + eventFields + '" class="text ui-widget-content ui-corner-all"><br/>' +
							'<label for="eventValue' + eventFields + '">Value</label><br/><input type="text" id="eventValue' + eventFields + '" class="text ui-widget-content ui-corner-all">' +
							'</fieldset>');
						eventFields++;
					}
				},
				"Cancel": function() {
					$(this).dialog("close");
					map.dragging.enable();
					map.doubleClickZoom.enable();
					map.scrollWheelZoom.enable();
					eventFields = 0;
				}
			}
		});

		$('#postEvent').keypress(function(e) {
			if (e.charCode == 13 || e.keyCode == 13) {
				submitEvent();
				$(this).dialog("close");
				e.preventDefault();
			}
		});

		function submitEvent() {
			eventType = $("#eventType").val();
			eventDate = $("#eventDate").val();
			var pzData = {
				'eventtype_id': eventType,
				'date': eventDate
			};
			var subData = {};
			for (var i = 0; i < eventFields; i++) {
				var key = $("#eventKey{0}".format(i)).val();
				var value = $("#eventValue{0}".format(i)).val();
				subData[key] = value;
			}
			pzData['data'] = subData;
			var pzEvent = {
				"type": pzType,
				"data": pzData,
				"action": pzAction
			};
			console.log(pzEvent);
			console.log(pzData);
			pzSender(pzEvent);
			map.dragging.enable();
			map.doubleClickZoom.enable();
			map.scrollWheelZoom.enable();
			eventFields = 0;
		}

		var eventtypeFields = 0;
		var eventtypeMaxFields = 10;
		var postEventtypeDialog = $('#postEventtype').dialog({
			autoOpen: false,
			width: 500,
			maxHeight: 620,
			height: 'auto',
			appendTo: '#map',
			modal: false,
			position: {
				my: "left top",
				at: "right bottom",
				of: placeholder
			},
			open: function() {
				map.scrollWheelZoom.disable();
				var contentStr = '<fieldset id="eventtypesFieldset">';
				contentStr += '<label for="eventtypesName">Name</label><br/><input type="text" id="eventtypesName" class="text ui-widget-content ui-corner-all"/><br/>';
				contentStr += '<p>Mapping</p>';
				$(this).html(contentStr);
			},
			buttons: {
				"Submit": function() {
					postEventtype();
					$(this).dialog("close");
				},
				"Add Mapping Field": function() {
					if (eventtypeFields < eventtypeMaxFields) {
						$("#eventtypesFieldset").append('<fieldset><label for="eventMappingName' + eventtypeFields + '">FieldName  </label>' +
							'<input type="text" id="eventMappingName' + eventtypeFields + '" class="text ui-widget-content ui-corner-all"/>' +
							'<select id="eventMappingType' + eventtypeFields + '">' +
							'<option value = "string">string</option>' +
							'<option value = "boolean">boolean</option>' +
							'<option value = "integer">integer</option>' +
							'<option value = "double">double</option>' +
							'<option value = "date">date</option>' +
							'<option value = "float">float</option>' +
							'<option value = "byte">byte</option>' +
							'<option value = "short">short</option>' +
							'<option value = "long">long</option>' +
							'</select></fieldset>');
						eventtypeFields++;

					}
				},
				"Cancel": function() {
					$(this).dialog("close");
					map.dragging.enable();
					map.doubleClickZoom.enable();
					map.scrollWheelZoom.enable();
					eventtypeFields = 0;
				}
			}
		});

		$('#postEventtype').keypress(function(e) {
			if (e.charCode == 13 || e.keyCode == 13) {
				postEventtype();
				$(this).dialog("close");
				e.preventDefault();
			}
		});

		function postEventtype() {
			eventtypesName = $("#eventtypesName").val();
			var pzData = {};
			var pzEvent = {
				"type": pzType,
				"action": pzAction
			};
			var pzData = {
				'name': eventtypesName
			};
			var pzMapping = {};
			for (var i = 0; i < eventtypeFields; i++) {
				var nameField = "#eventMappingName{0}".format(i);
				var dataTypeField = "#eventMappingType{0}".format(i);
				pzMapping[$(nameField).val()] = $(dataTypeField).val();
			}
			pzData['mapping'] = pzMapping;
			pzEvent['data'] = pzData;
			console.log(pzEvent);
			console.log(pzData);
			pzSender(pzEvent);
			map.dragging.enable();
			map.doubleClickZoom.enable();
			map.scrollWheelZoom.enable();
			eventtypeFields = 0;
		}

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
					var alertData = {
						"id": alertId,
						"trigger_id": alertTriggerId,
						"event_id": alertEventId
					}
					var pzAlert = {
						"type": pzType,
						"data": {},
						"action": pzAction
					};
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
					map.scrollWheelZoom.enable();
				}
			},
		});
		$('#alertContainer').keypress(function(e) {
			if (e.charCode == 13 || e.keyCode == 13) {
				alertTriggerId = $("#alertTriggerId").val();
				alertEventId = $("#alertEventId").val();
				var alertData = {
					"trigger_id": alertTriggerId,
					"event_id": alertEventId
				}
				var pzAlert = {
					"type": pzType,
					"data": {},
					"action": pzAction
				};
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

		setInterval(function(pzrequest) {
			if (Object.keys(pzTriggers).length != 0) {
				console.log("Getting alerts");
				pzrequest = {
					"action": "get_all",
					"data": {},
					"type": "alert"
				};
				pzChecker(pzrequest);
			} else {
				console.log("No triggers in list");
			}
		}, 30000);

		function pzChecker(pzrequest) {
			var csrftoken = getCookie('csrftoken');
			var requestStr = JSON.stringify(pzrequest);
			$.ajax({
				url: '/pz_fulcrum_pzworkflow',
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
			if (result != null && Object.keys(result).length != 0) {
				console.log("Finding triggers in alerts");
				$.each(result, function(index, value) {
					if (value["trigger_id"] in pzTriggers) {
						console.log(value["trigger_id"] + " is a listed Trigger, checking against events");
						if (value["event_id"] in pzEvents) {
							console.log("Event already listed, moving on");
						} else {
							console.log("Event not listed, going to get event");
							addEvent(value["event_id"]);
						}
					}
				});
			} else {
				console.log("No alerts to iterate through");
			}
		}

		function addEvent(id) {
			var csrftoken = getCookie('csrftoken');
			var requestStr = JSON.stringify({
				"type": "event",
				"data": {
					"id": id
				},
				"action": "get"
			});
			$.ajax({
				url: '/pz_fulcrum_pzworkflow',
				type: "POST",
				data: requestStr,
				contentType: "application/json",
				processData: false,
				dataType: "json",
				success: function(result) {
					storePzEvent(id, result);
					addEventSuccess(id, result);
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
		}

		function addEventSuccess(id, result) {
			console.log("Event request successful");
			$('#alertPopup').dialog({
				autoOpen: true,
				//maxWidth: 450,
				maxHeight: 600,
				width: 200,
				modal: false,
				appendTo: '#map',
				position: {
					my: "left bottom",
					at: "right top",
					of: $("#placeholder3")
				},
				title: "PZ-Workflow Alert",
				open: function() {
					$(this).html('<p style="text-align: center;">Event matching</br>a listed trigger</p>')
					setTimeout(function() {
						if ($("#alertPopup").dialog("isOpen") == true) {
							$("#alertPopup").dialog("close");
						}
					}, 7000);
				},
				buttons: {
					View: function() {
						$(this).dialog("close");
						viewPzEvent(result, id);
						
					},
					Ignore: function() {
						$(this).dialog("close");
					}
				}
			}).prev(".ui-dialog-titlebar").css("color", "red");
		}

		function viewPzEvent(result, id) {
			console.log(result);
			console.log(id);
			var coords = [];
			var data = null;
			$('#viewPzEvent').dialog({
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
				title: "Event Details",
				open: function() {
					map.dragging.disable();
					map.doubleClickZoom.disable();
					map.scrollWheelZoom.disable();
					var contentStr = '<pre style="text-align: left;">' + JSON.stringify(result, undefined, 2) + '</pre><br/>';
					$(this).html(contentStr);
				}
				// },
				// buttons: {
				// 	Close: function() {
				// 		$(this).dialog("close");
				// 		map.dragging.enable();
				// 		map.doubleClickZoom.enable();
				// 		map.scrollWheelZoom.enable();
				// 	}
				// }
			});
			var buttons = {
				'Close': function() {
					$(this).dialog("close");
					map.dragging.enable();
					map.doubleClickZoom.enable();
					map.scrollWheelZoom.enable();
				}
			}
			if ('data' in result){
				data = result;
				if ('lng' in data['data']) {
					coords.push(data['data']['lng'])
				}
				if ('lat' in data['data']){
					coords.push(data['data']['lat']);
				}
			}

			if (coords.length == 2 && data != null) {
				
				buttons['Add-to-map'] = function() {
					addEventToMap(data, coords);
					$(this).dialog('close');
					map.dragging.enable();
					map.doubleClickZoom.enable();
					map.scrollWheelZoom.enable();
				}
			}
			$("#viewPzEvent").dialog("option", "buttons", buttons);
		}


		function addEventToMap(data, coords) {
			var activeLayer = false;
			var existing = false;
			for (var feature in eventLayerGeojson['features']) {
				if (eventLayerGeojson['features'][feature]['properties']['id'] == data['id']) {
					console.log("Feature already exists in layer");
					existing = true;
				}
			}
			if (existing != true) {
				if(map.hasLayer(eventLayer)) {
					activeLayer = true;
					layerControl.removeLayer(eventLayer);
					map.removeLayer(eventLayer);
				}
				var json_feature = {
					'type': 'Feature',
					'geometry': {
						'type': 'Point',
						'coordinates': coords
					},
					'properties': data
				}

				eventLayerGeojson['features'].push(json_feature);
				eventLayer = L.geoJson(eventLayerGeojson, {
					onEachFeature: onEachEventFeature,
					pointToLayer: function(feature, latlng) {
						return L.circleMarker(latlng, {
							radius: 4,
							fillColor: "#e60000",
							color: "#000000",
							weight: 1,
							opacity: 1,
							fillOpacity: 1
						});
					}
				});
				layerControl.addOverlay(eventLayer, "PzEvents", "Fulcrum Layers");
				if (activeLayer == true) {
					map.addLayer(eventLayer);
				}
				var features = [json_feature];
				storePzFeature(features);
			}
		}

		function onEachEventFeature(feature, layer) {
			layer.on('click', function(e) {
				var popupStr = '<pre>' + JSON.stringify(e.target.feature.properties, undefined, 2) + '</pre>';

				// Get position for popup //
				var coords = [e.target.feature.geometry.coordinates[1], e.target.feature.geometry.coordinates[0]];

				var button = '<p><button id="removeFeature">Remove feature from layer</button></p>';

				popupProperties = e.target.feature.properties;
				// Create popup and add to map //
				var popup = L.popup({
					maxHeight: 400,
					closeOnClick: false,
					keepInView: true
				}).setLatLng(coords).setContent(popupStr + button).openOn(map);
			});

		}

		

		function removeFeature(popupProperties) {
			console.log(popupProperties);
			var id = popupProperties['id'];
			var deleteix = null;
			var feature = null;
			var features = eventLayerGeojson['features'];
			for (var f in features) {
				console.log(features[f]);
				if (features[f]['properties']['id'] == id){
					console.log("found feature");
					deleteix = f;
					feature = features[f];
					break;
				} 
			}
			if (deleteix != null) {
				var layerActive = false;
				if(map.hasLayer(eventLayer)) {
					layerActive = true;
					map.removeLayer(eventLayer);
				}
				eventLayerGeojson['features'].splice(deleteix, 1);
				eventLayer = L.geoJson(eventLayerGeojson, {
					onEachFeature: onEachEventFeature,
					pointToLayer: function(feature, latlng) {
						return L.circleMarker(latlng, {
							radius: 4,
							fillColor: "#e60000",
							color: "#000000",
							weight: 1,
							opacity: 1,
							fillOpacity: 1
						});
					}
				});

				layerControl.removeFrom(map);
				layerControl = L.control.groupedLayers(baseMaps, overlays).addTo(map);
				if (eventLayerGeojson['features'].length > 0) {
					layerControl.addOverlay(eventLayer, "PzEvents", "Fulcrum Layers");
					if (layerActive == true) {
						map.addLayer(eventLayer);
					}
				}
				if (feature != null) {
					deleteFeature([feature]);
				}
			}
		}

		function deleteFeature(features) {
			if (features != null) {
				var pz_delete = {'delete': {'features': features}};
				postPzModel(pz_delete);
			}
		}

		// Button to set alert subscription //
		if (typeof(Storage) != "undefined") {
			if (sessionStorage.sub) {
				var sub = sessionStorage.sub;
			} else {
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
					closeDialogs("#subscribeForm");
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
						sub = inStr;
						sessionStorage.sub = inStr;
						getSub(sub);
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

			$('#subcribeForm').keypress(function(e) {
				if (e.charCode == 13 || e.keyCode == 13) {
					var inStr = $("#sub").val();
					sub = inStr;
					sessionStorage.sub = inStr;
					getSub(sub);
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
				url: url,
				dataType: "json",
				success: function(result) {
					subUpdate(result, url);
				},
				error: function() {
					alert("Unable to get alert service, re-check URL");
				}
			});
		}

		function subUpdate(result, url) {
			var layerName = result['test'];
			var layerName = 'test';
			subLayers[layerName] = null;
			if (!(layerName in layers)) {
				if (!(layerName in layerStyles)) {
					var color = getRandomColor();
					layerStyles[layerName] = {
						radius: 4,
						fillColor: color,
						color: "#000000",
						weight: 1,
						opacity: 1,
						fillOpacity: 1
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
				url: layerUrls[name],
				dataType: "json",
				success: function(result) {
					addSubSuccess(result, name);
				},
			});
		}

		function addSubSuccess(result, name) {
			//var layer = result['data'];
			var layer = result[name];
			addSubLayer(layer, name);
			activeLayers[name] = null;
			bounds = fetchBounds(layers[name]);
			// If no layers/legend currently: add legend, else: delete old version and add new version //
			if (Object.keys(activeLayers).length == 1) {
				legend.addTo(map);
			} else {
				legend.removeFrom(map);
				legend.addTo(map);
			}
			layerRefresher(name);
		}

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
		}

		function subLayerRefresher(key) {
			layerUpdates[key] = setInterval(function() {
				console.log("Updating");
				$.ajax({
					url: layerUrls[key],
					dataType: "json",
					success: function(result) {
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
		}

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
			if (Object.keys(activeLayers).length != 0) {
				legend.addTo(map);
			};
		}


		function storePzEvent(id, data) {
			if (id != null) {
				pzEvents[id] = id;
				console.log("Storing event data");
				console.log(data);
				var pz_data = {'post': {'events': {}}}
				pz_data['post']['events'][id] = {'event_data': null};
				if (data != null) {
					if ('data' in data) {
						var coords = [];
						if ('lng' in data.data && 'lat' in data.data) {
							coords.push(data.data.lng);
							coords.push(data.data.lat);
						}
						pzEvents[id] = {'event_data': data['data'], 'coordinates': coords};
						pz_data['post']['events'][id] = {'event_data': data['data'], 'coordinates': coords};
					}
				}
				postPzModel(pz_data);
			}
			// if (typeof(Storage) != "undefined") {
			// 	sessionStorage.pzEvents = JSON.stringify(pzEvents);
			// }
		}

		function storePzTrigger(id, data) {
			if (id != null) {
				pzTriggers[id] = id;
				var pz_data = {"post": {"triggers": {}}};
				pz_data["post"]["triggers"][id] = {"trigger_data": null};
				if (data != null) {
					pzTriggers[id] = data;
					pz_data["post"]["triggers"][id] = {"trigger_data": data};
				}
				postPzModel(pz_data);
			}
			// if (typeof(Storage) != "undefined") {
			// 	sessionStorage.pzTriggers = JSON.stringify(pzTriggers);
			// }
		}

		function storePzFeature(features) {
			if (features.length > 0) {
				var pzData = {"post": {"features": features}};
				postPzModel(pzData);
			}
		}
		function postPzModel(pz_data) {
			console.log("Posting");
			console.log(pz_data);
			console.log(JSON.stringify(pz_data));
			var csrftoken = getCookie('csrftoken');
			$.ajax({
				url: '/pz_fulcrum_pzmodels',
				type: "POST",
				data: JSON.stringify(pz_data),
				contentType: "application/json",
				processData: false,
				dataType: "json",
				success: function(result) {
					console.log("success");
				},
				error: function(result) {
					console.log("Error");
					console.log(result);
				},
				beforeSend: function(xhr, settings) {
					if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
						xhr.setRequestHeader("X-CSRFToken", csrftoken);
					}
				}
			});
		}

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

		function closeDialogs(thisDialog) {
			var dialogs = [
				"#timeoutForm",
				"#colortimeForm",
				"#regreshForm",
				"#subscribeForm",
				"#formContainer",
				"#pzContainer",
				"#getContainer",
				"#deleteContainer",
				"#triggerContainer",
				"#eventContainer",
				"#alertContainer",
				"#onClickAttrTrigger",
				"#onClickBufferTrigger",
				"#Manager",
				"#postTrigger",
				"#postEvent",
				"#postEventtype"
			];
			for (var i = 0; i < dialogs.length; i++) {
				if (dialogs[i] != thisDialog && $(dialogs[i]).hasClass("ui-dialog-content")) {
					$(dialogs[i]).dialog("close");
				}
			}
		}

		// Gets randomized color for new layer //
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
			if (colorix < approvedColors.length) {
				console.log(approvedColors[colorix]);
				return approvedColors[colorix++];
			} else {
				colorix = 1;
				console.log(approvedColors[colorix]);
				return approvedColors[0];
			}
		};

		String.prototype.format = function() {
			var formatted = this;
			for (var i = 0; i < arguments.length; i++) {
				var regexp = new RegExp('\\{' + i + '\\}', 'gi');
				formatted = formatted.replace(regexp, arguments[i]);
			}
			return formatted;
		};



	});