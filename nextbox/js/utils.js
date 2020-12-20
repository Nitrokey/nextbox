function request_raw(raw_url, method, on_done, data) {
	$.ajax({
		url: raw_url,
		type: method,
		ContentType: "application/json",
		data: data,
	}).done(function (resp) {

			if (resp === null) {
				fail_notify("Failed connection to Nextbox-Daemon");
				return;
			}

			if (resp.api != API_VERSION) {
				if ("api" in resp)
					fail_notify(`Not matching APIs, backend: ${resp.api} frontend: ${API_VERSION}`);
				else
					fail_notify("Connection to Nextbox-Daemon failed");
				return;
			}

			if ("msg" in resp && resp.msg && resp.msg.length > 0)
				notify(resp.msg.join("\n"));
			return on_done(resp);
		})
		.fail(function(resp, code) {
			console.error([raw_url, resp, code]);
			fail_notify("Failed connecting to Nextbox-Daemon");
		});

}

function request(url, method, on_done, data) {
	return request_raw("forward" + url, method, on_done, data);
}

function request_direct(url, method, on_done, data) {
	return request_raw(`http://${requested_host}:18585/${url}`, method, on_done, data);
}

function fail_notify(msg) {
	return notify(`<span class="notify-error">${msg}</span>`);
}

function notify(msg, duration=5000) {
	//return OC.Notification.showTemporary(msg);
    let obj = OC.Notification.showHtml(msg + "&nbsp;&nbsp;");
	$(obj).delay(duration).fadeOut(500);
}

function clear_loading() {
		if ($(".overlay").length > 0) {
			$(".overlay").remove();
			$(".grayout").removeClass("grayout");
		}
}

function set_loading(el) {
			$(el).prepend('<div class="overlay icon-loading"></div>');
			$(el).toggleClass("grayout");
}

function set_content(data) {
		$("#app-content-wrapper").html("");
		add_content(data);
}

function add_content(data) {
		if ("list" in data)
			$("#app-content-wrapper").append(`<div class="app-content-list">${data.list}</div>`);
		if ("details" in data)
			$("#app-content-wrapper").append(`<div class="app-content-details">${data.details}</div>`);
		if ("raw" in data)
		    $("#app-content-wrapper").append(data.raw);
}
