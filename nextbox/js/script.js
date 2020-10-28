





function storage_overview() {

		//var baseUrl = OC.generateUrl('/apps/notestutorial');
	  var url = "http://192.168.10.129:18585/storage";
		$.ajax({
    		url: url,
		    type: "GET",
		    contentType: "application/json"
		    //data: JSON.stringify(note)

		}).done(function (response) {
			

			  console.log([response]);
			
		}).fail(function (response, code) {
		    // handle failure
			  console.log([response, code]);

		});



}


$(function() {


	//alert("iodsfjsf");

	$("#inside-app").text("isodjoidfsj");

	$("#nav_storage").click(storage_overview);


});
