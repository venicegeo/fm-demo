package us.geospatial.filter


import groovy.json.JsonOutput


class HomeController {
	def boundaryFilterService


	def index() { 
		def map = boundaryFilterService.serviceMethod(params, request)
		def json = new JsonOutput().toJson(map)


		response.contentType = "application/json"
		//response.setHeader("Access-Control-Allow-Origin", "http://mycomputer:9090")
		//response.setHeader("Access-Control-Allow-Headers", "Content-Type")
		//response.setHeader("Access-Control-Allow-Methods", "POST")
		render json
	}
}
