package us.geospatial.filter


import geoscript.geom.Point
import groovy.json.JsonSlurper


class BoundaryFilterService {

	def grailsApplication
	
	def serviceMethod(params, request) {
		def usBoundaries = grailsApplication.config.usBoundaries

		// get the submitted json
		def text = request.reader.text ?: params.find { true }.key
		def json = new JsonSlurper().parseText(text)

		// iterate through the json applying the boundary filter
		def failed = []
		def passed = []
		json.each() {
			// support both geojson and regular json
			def coordinates = it.geometry?.coordinates ?: [it.longitude, it.latitude]
			if (coordinates) {
				def point = new Point(coordinates[0], coordinates[1])
				if (usBoundaries.contains(point)) { failed.push(it) }
				else { passed.push(it) }
			}
		}


		return [failed: failed, passed: passed]
	}
}
