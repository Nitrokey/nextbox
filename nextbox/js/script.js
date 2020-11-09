
var progress_interval = null;
var requested_host = null;

function request_raw(raw_url, method, on_done, data) {
	$.ajax({
		url: raw_url,
		type: method, 
		ContentType: "application/json",
		data: data,
	})
		.done(function (resp) {
			if ("msg" in resp && resp.msg && resp.msg.length > 0)
				notify(resp.msg.join("\n"));
			return on_done(resp);

		})
		.fail(function(resp, code) {
			console.error([raw_url, resp, code]);
		});

}

function request(url, method, on_done, data) {
	return request_raw("forward" + url, method, on_done, data);
}


function notify(msg) {
	OC.Notification.showTemporary(msg);
}

function set_loading(el) {
		$(el).html('<div class="overlay icon-loading"></div>' + $(el).html());
		el.classList.toggle("grayout");
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
}

function add_text_edit(txt) {
	add_content({details: `
	    <h2>DDClient Configuration</h2>
	    <form>
				<textarea class="ddclient-edit" name="content">${txt}</textarea><br />
				<button class="ddclient-edit-save">Save</button>
				<button class="ddclient-edit-reset">Reset</button>
				<button class="ddclient-edit-test">Test</button><br />
			</form>
		`});

	$("button.ddclient-edit-save").click(function(ev) {
		$data = {
			content: $("textarea.ddclient-edit").val()
		};
		request("/ddclient/config", "POST", function(resp) { }, $data);
		return false;
	});

	$("button.ddclient-edit-test").click(function(ev) {
		request("/ddclient/test", "GET", function(resp) { });
		return false;
	});
	
	$("button.ddclient-edit-reset").click(function(ev) {
		render_dyndns();
		return false;
	});

}

function set_list_callbacks() {

	// click event for menu-toggle
	$(".app-content-list-item-menu > div.icon-more").click(function(ev) {
		ev.target.parentElement.children[1].classList.toggle("open");
	});

	// click event for umount
	$("button.storage-umount").click(function(ev) {
		let name = $(ev.target).parents(".app-content-list-item").first()
			.children(".app-content-list-item-line-two")
			.text().split("/")[2];

		set_loading($(ev.target).parents(".app-content-list-item")[0]);

		request(`/storage/umount/${name}`, "GET", function(resp) {
			render_storage();
		});
	});

	// click mount-name text field
	$("input.menu-mount-text").click(function(ev) {
		$(ev.target).val("");
	});

	// click event for mount
	$("input.menu-mount-submit").click(function(ev) {
		// @todo: check name for validity
		let name = $(ev.target).parent().children("input[type=text]").val();
		let dev = $(ev.target).parents(".app-content-list-item")
			.children(".app-content-list-item-details")
			.text().split("/")[2];

		set_loading($(ev.target).parents(".app-content-list-item")[0]);
		
		request(`/storage/mount/${dev}/${name}`, "GET", function(resp) {
			render_storage();
		});
		return false;
	});

	// click event for backup, fire backup-start & delay reload for 1000ms
	$("button.start-backup").click(function(ev) {
		request("/backup/start", "GET", function(resp) {
			$("button.start-backup").delay(1000, render_backup);
		});
	});

	// click event for restore, fire restore-start & delay for 1000ms
	$("button.start-restore").click(function(ev) {
		let name = $(ev.target).parents(".app-content-list-item").first()
			.children(".app-content-list-item-line-one").text();
		request(`/backup/restore/${name}`, "GET", function(resp) {
			$("button.start-restore").delay(1000, render_backup);
		});
	});


	// timeout reload for backup progress-bar
	if ($("progress.backup-progress").length > 0) {
		if(progress_interval === null) {
			progress_interval = window.setInterval(function() {
				request("/overview", "GET", function(resp) {
					if (resp.backup.running) {
						$("progress.backup-progress").val(resp.backup.progress);
						let step = (resp.backup.step === undefined) ? "init" : resp.backup.step;
						$("span.backup-progress-step").text(`${resp.backup.what} step: ${step}`);
						let percent = resp.backup.progress;
						if (percent == undefined || percent === null)
							percent = "0.0";
						$("span.backup-progress-percent").text(percent + "%");
					} else {
						$("progress.backup-progress").val(100);
						$("span.backup-progress-step").text(`${resp.backup.state}`);
						$("span.backup-progress-percent").text("100.0%");
						window.clearInterval(progress_interval);
						progress_interval = null;
						$("progress.backup-progress").delay(3000, render_backup);
					}
				});
			}, 1000);
		}
	} else {
		if (progress_interval !== null) {
			window.clearInterval(progress_interval);
			progress_interval = null;
		}
	}

	// service callbacks @todo: lame repeating...
	$("button.service-start").click(function(ev) {
		let name = $(ev.target).parents(".app-content-list-item")
			.children(".app-content-list-item-details").text();
			request(`/service/${name}/start`, "GET", function(rest) {
				render_dyndns();
			});
	});
	$("button.service-stop").click(function(ev) {
		let name = $(ev.target).parents(".app-content-list-item")
			.children(".app-content-list-item-details")
			.text();
			request(`/service/${name}/stop`, "GET", function(rest) {
				render_dyndns();
			});

	});
	$("button.service-restart").click(function(ev) {
		let name = $(ev.target).parents(".app-content-list-item")
			.children(".app-content-list-item-details")
			.text();
			request(`/service/${name}/restart`, "GET", function(rest) {
				render_dyndns();
			});
	});

}

function render_list(headline, data) {

	let pre = ""; /*`<div class="app-content-list">`;*/
	if (headline)
		pre += `<h2>${headline}</h2>`;
	let post = ""; /*`</div>`;*/

	let inner = data.map(function(item) {
		out = `<a href="#" class="app-content-list-item">`;
		let icon = item.icon ? item.icon : "?";
		let bg_col = (item.bg && item.bg !== null) ? item.bg : "rgb(225, 225, 225)";
		out += `<div class="app-content-list-item-icon" style="background-color: ${bg_col};">${icon}</div>`;
		out += `<div class="app-content-list-item-line-one">${item.one}</div>`;
		if (item.two)
			out += `<div class="app-content-list-item-line-two">${item.two}</div>`;
		if (item.details)
			out += `<span class="app-content-list-item-details">${item.details}</span>`;
		/** add options menu here **/
		if(item.menu) {
				out += `<div class="app-content-list-item-menu"><div class="icon-more"></div><div class="popovermenu"><ul>`;
				
				out += item.menu.map(function(menu_item) {
					let tag_class = (menu_item.cls) ? `${menu_item.cls} ` : "";
					tag_class += `icon-${menu_item.icon} `;
					if (menu_item.input_value) {
						tag_class += "icon";
						return `<li><span class="menuitem"><span class="${tag_class}"></span><form><input type="text" value="${menu_item.input_value}" class="menu-mount-text"><input type="submit" value=" " class="primary icon-checkmark-white menu-mount-submit"></form></span></li>`;
					} else {
						return `<li><button class="${tag_class}"><span>${menu_item.name}</span></button></li>`;
					}
				}).join("");

				out += `</ul></div></div>`;
		}
		out += "</a>";
		return out;
	}).join("");
	return pre + inner + post;
}

function assemble_storage(data, is_mounted) {

	let mounted = data.mounted;
	let mounted_devs = Object.keys(data.mounted);
	return data.available
		.filter(dev => !is_mounted || (is_mounted && mounted_devs.includes(dev))) 
		.map(dev => {
			
			let ret = Object({
				icon: "HD",
				two: mounted[dev] || "(not mounted)",
				details: dev
			});

			ret.bg = "rgb(100, 155, 155)";
			if (!is_mounted && mounted_devs.includes(dev))
				ret.bg = "rgb(220, 220, 220)";

			ret.one = "Extra Storage";
			if (data.main == dev)
				ret.one = "Main Storage";
			else if (data.backup == dev) 
				ret.one = "Backup Storage"; 

			if (data.main != dev) {
				if (mounted_devs.includes(dev)) 
					ret.menu = new Array( new Object({icon: "close", name: "umount", cls: "storage-umount"}) );
				else
					ret.menu = new Array( new Object({icon: "folder", input_value: "[mount-name]"}) );
			}

			return ret;
		});
}

function assemble_backup_overview(data) {

	let o_icon = "-";
	let o_bg = "rgb(220, 220, 220)";

	if (data.what) {
		o_icon = data.what.substr(0, 1).toUpperCase();
		o_bg = "rgb(225, 125, 125)";
	}

	let out = [{
		icon: "B",
		bg: "rgb(220, 220, 220)",
		one: "Backup",
 		two: "last: " + ((data.last_backup) ? (new Date(data.last_backup*1e3)).toLocaleString() : "n/a"),
		menu: [{icon: "upload", name: "start backup", cls: "start-backup"}]
	}, {
		icon: "R",
		bg: "rgb(220, 220, 220)",
		one: "Restore",
		two: "last: " + ((data.last_restore) ? (new Date(data.last_restore*1e3)).toLocaleString() : "n/a")
	}];

	
	let op_info = ("running" in data) ? data : data.operation;

	if (op_info.running) {
		out.push({
			icon: "!",
			bg: "rgb(125, 225, 225)",
			one: `<span class="backup-progress-step">starting operation</span>`,
			two: `<progress value=0 max=100 class="backup-progress"></progress>`,
			details: `<span class="backup-progress-percent"></span>`
		});
	}


	return out;
}

function assemble_backup_available(data) {
	return data.map(item => Object({
			icon: "B",
			bg: "rgb(125, 225, 225)",
			one: item.name,
		  two: new Date(item.created*1e3).toLocaleString(),
			details: item.size + "B",
		  menu: [{icon: "download", name: "restore this backup", cls: "start-restore"}]
	}));
}

function assemble_log(logdata) {
	return logdata.map(line => {
			let toks = line.split(" => ");
			return `<span class="log-date">${toks[0]}:</span> ${toks[1]}`;
		}).join("<br />");
}

function assemble_ddclient_status(resp) {
	
	let state = resp.data[0];
	let _icon = "?";
	let _bg = "rgb(225, 225, 225)";
	let _menu = [];
	if (state == "active") {
			_icon = "+";
			_bg = "rgb(33, 128, 33)";
		  _menu = [
				{icon: "close", name: "stop service", cls: "service-stop"},
				{icon: "history", name: "restart service", cls: "service-restart"}
			];
	} else {
			_icon = "-";
			_bg = "rgb(225, 55, 55)";
		  _menu = [
				{icon: "play", name: "start service", cls: "service-start"},
			];
	}

	return [{
		icon: _icon,
		bg: _bg,
		one: "Dynamic DNS",
		two: state,
		details: "ddclient",
		menu: _menu,
	}];
}

function render_overview() {
	request("/overview", "GET", function(resp) {
		set_content({list: render_list("Backup / Restore Overview", assemble_backup_overview(resp.backup))});
		add_content({list: render_list("Mounted Storage(s)", assemble_storage(resp.storage, true))});
		set_list_callbacks();
	});
}


function render_storage() {

	request("/storage", "GET", function(resp) {
		set_content({list: render_list("Mounted Storages",	assemble_storage(resp.data, true))});
		add_content({list: render_list("Available Storages",	assemble_storage(resp.data, false))});
		set_list_callbacks();
	});
}


function render_backup() {
	request("/backup", "GET", function(resp) {
		set_content({list: render_list("Backup / Restore Overview", assemble_backup_overview(resp.data))});
		add_content({list: render_list("Available Backups", assemble_backup_available(resp.data.found))});
		set_list_callbacks();
	});
}

function render_dyndns() {
	request("/service/ddclient/is-active", "GET", function(resp) {
		set_content({list: render_list("Service Status", assemble_ddclient_status(resp))});
		set_list_callbacks();
		request("/ddclient/config", "GET", function(resp) {
			add_text_edit(resp.data.join("\n"));
		});
	});
}

function render_log() {
	request("/log", "GET", function(resp) {
		set_content({details: assemble_log(resp.data)});
	});
}

function render_http() {
	

}



$(function() {

	requested_host = document.location.host;
	$("#nav_overview").click(render_overview);
	$("#nav_storage").click(render_storage);
	$("#nav_backup").click(render_backup);
	$("#nav_dyndns").click(render_dyndns);
	$("#nav_log").click(render_log);
	$("#nav_http").click(render_http);

	render_overview();

});


