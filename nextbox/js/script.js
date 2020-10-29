
// request comm-token (asap, thus here)
var token = null;
$.ajax({
	url: "token", 
	type: "GET"
}).done(function(resp) {
	token = resp.token;
}).fail(function(respone, code) {
	token = null;
});


function storage_overview() {

	  var url = "http://192.168.10.129:18585/storage?token=" + token;
		$.ajax({
    		url: url,
		    type: "GET",
		    contentType: "application/json"
		    //data: JSON.stringify(note)

		}).done(function (response) {
			
				set_content(response.toString()); 
			  //console.log([response]);
			
		}).fail(function (response, code) {
		    // handle failure
			  console.log([response, code]);

		});
}


function set_content(details, items) {

	/*let l = "";
	for (


	$("#inside-app").html(`
    <div class="app-content-detail">${details}</div>
		${details}
		<div class="app-content-list"></div>
	`);*/

	$("#app-content-wrapper").html(`
			<div class="app-content-list">${details}</div>
	`);

}


$(function() {


	//$("#inside-app").text("isodjoidfsj");

	$("#nav_storage").click(storage_overview);


	$.ajax({
		url: "http://192.168.10.129:18585/overview",
		type: "GET",
		contentType: "application/json"
	}).done(function(resp) {

		let details = "<h2>NextBox Overview</h2>"
		details += "<h1>Backup / Restore Status</h1>";
		if(resp["backup"]["running"] === false) 
			details += `<a href="#" class="app-content-list-item">
            <div class="app-content-list-item-icon" style="background-color: rgb(41, 97, 156);">N</div>
            <div class="app-content-list-item-line-one">Backup / Restore</div>
            <div class="app-content-list-item-line-two">not running</div>
            <!--span class="app-content-list-item-details">8 hours ago</span-->
            <!--div class="icon-delete"></div-->
        </a>`;
		else
			details += `<a href="#" class="app-content-list-item">
            <div class="app-content-list-item-icon" style="background-color: rgb(41, 97, 156);">N</div>
            <div class="app-content-list-item-line-one">Backup / Restore</div>
            <div class="app-content-list-item-line-two">running</div>
            <!--span class="app-content-list-item-details">8 hours ago</span-->
            <!--div class="icon-delete"></div-->
        </a>`;

		details += "<h1>Mounted Storage(s)</h1>";

		Object.keys(resp["storage"]["mounted"]).map(x => {
			 let map = resp["storage"]["mounted"];
				
			 let what = "Extra Storage";
			 if (resp["storage"]["main"] == x)
				what = "Main Storage";
			 else if (resp["storage"]["backup"] == x)
				what = "Backup Storage"; 

       details += `
				<a href="#" class="app-content-list-item">
            <div class="app-content-list-item-icon" style="background-color: rgb(41, 97, 156);">HD</div>
            <div class="app-content-list-item-line-one">${what}</div>
            <div class="app-content-list-item-line-two">${map[x]}</div>
            <span class="app-content-list-item-details">${x}</span>
            <!--div class="icon-delete"></div-->
        </a>
			 `;
		})


		set_content(details);
	});


});


