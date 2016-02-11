#! /usr/bin/env groovy


// import the http builder jars
@Grab(group = "org.codehaus.groovy.modules.http-builder", module = "http-builder", version = "0.7")
import groovyx.net.http.HTTPBuilder
import static groovyx.net.http.Method.*
import static groovyx.net.http.ContentType.*

email = ""
password = ""

// global variables
data = [] // raw data from Fulcrum
def form
records = [] // transformed data, i.e. "assembled"
def userAuthKey

// script start
getUserAuthKey()
getFormData()
getRecords(1)
assembleData()
filterData("phoneNumber")
filterData("geospatial")
// script end



// script functions
def assembleData() {
	data.each() {
		def record = (it.form_values.collect { 
			recordKey, recordValue -> 
			def key = form.elements.find { recordKey == it.key }.data_name
	
				
			return [(key): recordValue]	
		}).inject([:]) { result, map -> result + map }

		record += [latitude: it.latitude, longitude: it.longitude]
		records.push(record)

		//downloadRecordImages(record)
		//downloadRecordVideos(record)
	}
}

def downloadFile(url, filename) {
        def file = new File(filename).newOutputStream()  
	file << new URL(url).openStream()  
	file.close()  
}

def downloadRecordImages(record) {
	record.photos.eachWithIndex() { value, index ->
		def photoId = value.photo_id
		print "Getting metadata for image ${index + 1}... "
		def http = new HTTPBuilder("https://api.fulcrumapp.com/api/v2/photos/${photoId}.json")
		http.request(GET) { req ->
			headers."X-ApiToken" = authKey
			response.success = { resp, reader ->
				def url = reader.photo.original
				print "Downloading it... "
				//downloadFile(url, "${photoId}.jpg")
				print "Done!\n"
			}
		}
	}
}

def downloadRecordVideos(record) {
	record.videos.eachWithIndex() { value, index ->
		println record
		def videoId = value.video_id
		print "Getting metadata for video ${index + 1}... "
		def http = new HTTPBuilder("https://api.fulcrumapp.com/api/v2/photos/${videoId}.json")
		http.request(GET) { req ->
			headers."X-ApiToken" = authKey
			response.success = { resp, reader ->
				def url = reader.video.original
				print "Downloading it... "
				//downloadFile(url, "${photoId}.mp4")
				print "Done!\n"
			}
		}
	}
}

def filterData(filter) {
	if (filter == "geospatial") {
		def http = new HTTPBuilder("http://pzsvc-us-geospatial-filter.cf.piazzageo.io/filter")
		print "Filtering data geospatially... "
		http.request(POST) { req ->
			send JSON, records
			response.success = { resp, reader ->
				records = reader.passed.features
			}
		}
	}
	else if (filter == "phoneNumber") {
		def http = new HTTPBuilder("http://pzsvc-us-phone-number-filter.cf.piazzageo.io/filter")
		print "Filtering data for US phone numbers... "
		http.request(POST) { req ->
			send JSON, records
			response.success = { resp, reader ->
				records = reader.passed
			}       
		}       
	}
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
			data += reader.records
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
