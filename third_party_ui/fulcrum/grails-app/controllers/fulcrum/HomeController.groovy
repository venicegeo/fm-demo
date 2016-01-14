package fulcrum


class HomeController {

	def index() { render(view: "demo.gsp") }

	def photoUpload() { render(view: "photo_upload.gsp") }
}
