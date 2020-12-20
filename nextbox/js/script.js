

var API_VERSION = 1;

var progress_interval = null;
var requested_host = null;








$(function() {

	requested_host = document.location.host;

	$("#nav_overview").click(render_overview);
	$("#nav_storage").click(render_storage);
	$("#nav_backup").click(render_backup);
	$("#nav_dyndns").click(render_dyndns);
	$("#nav_log").click(render_log);
	$("#nav_system").click(render_system);

	render_overview();

});


