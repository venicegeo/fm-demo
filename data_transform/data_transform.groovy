#! /usr/bin/env groovy


// import the http builder jars
@Grab(group = "org.codehaus.groovy.modules.http-builder", module = "http-builder", version = "0.7")
import groovyx.net.http.HTTPBuilder
import static groovyx.net.http.Method.GET


email = ""
password = ""

// global variables
def form
records = []
def userAuthKey

// script start
getUserAuthKey()
getFormData()
getRecords(1)
assembleData()
// script end


// script functions
def assembleData() {
	def data = []

	records.each() {
		def record = (it.form_values.collect { 
			recordKey, recordValue -> 
			def key = form.elements.find { recordKey == it.key }.data_name
	
			
			return [(key): recordValue]	
		}).inject([:]) { result, map -> result + map }

		record += [latitude: it.latitude, longitude: it.longitude]
		data.push(record)
	}

	// download all images for all records
	def imageAccessKeys = ((data.collect { it.photos.collect { it.photo_id } }).inject([]) { result, array -> result + array }).unique().sort()
	imageAccessKeys.eachWithIndex() { value, index ->
		print "Getting metadata for image ${index + 1}/${imageAccessKeys.size()}... "
		def filename = value
		def http = new HTTPBuilder("https://api.fulcrumapp.com/api/v2/photos/${filename}.json")
		http.request(GET) { req ->
			headers."X-ApiToken" = authKey
			response.success = { resp, reader ->
				def url = reader.photo.original
				print "Downloading it... "
				downloadImage(url, "${filename}.jpg")
				print "Done!\n"
                        }
		}
	}
}

def downloadImage(url, filename) {
        def file = new File(filename).newOutputStream()  
	file << new URL(url).openStream()  
	file.close()  
}

def getFormData() {
	print "Getting form data... "

	def http = new HTTPBuilder("https://api.fulcrumapp.com/api/v2/forms.json")
	http.request(GET) { req ->
		headers."X-ApiToken" = authKey
		response.success = { resp, reader ->
			reader.forms.each() {
				if (it.name == "Starbucks") { form = it }
			}
			print "Done!\n"
		}
	}
}

def getRecords(pageNumber) {
	print "Getting records... page ${pageNumber}... "

	def http = new HTTPBuilder("https://api.fulcrumapp.com/api/v2/records.json")
	http.request(GET) { req ->
		headers."X-ApiToken" = authKey

		uri.query = [
			"form_id": form.id, 
			"page": pageNumber
		]

		response.success = { resp, reader ->
			records += reader.records
			print "Done!\n"
			if (pageNumber < reader.total_pages) {
				pageNumber++
				getRecords(pageNumber)
			}
		}
	}
}

def getUserAuthKey() {
	print "Getting user authentication key... "

	def http = new HTTPBuilder("https://api.fulcrumapp.com/api/v2/users.json")
	http.request(GET) { req ->
		headers."Authorization" = "Basic " + "${email}:${password}".getBytes().encodeBase64()
		response.success = { resp, reader -> 
			authKey = reader.user.contexts[0].api_token 
			print "Done!\n"
		}
	}
}
