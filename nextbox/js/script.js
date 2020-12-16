

var API_VERSION = 1;

var progress_interval = null;
var requested_host = null;

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

function add_ddclient_edit(data) {

	let domain = (data.domain === null) ? "" : data.domain;
  let email = (data.email === null) ? "" : data.email;
	let details = `
	    <h2>Configuration</h2>
	    <form>
				<h1>Edit Dynamic DNS Client Configuration (ddclient.conf)</h1> 
				<textarea class="ddclient-edit" name="conf">${data.conf.join("\n")}</textarea><br />
				<h1>External Domain</h1>
				<input type=text class="ddclient-domain" name="domain" value="${domain}" /><br /><br />
				<h1>Let's Crypt E-Mail Address</h1>
				<input type=text class="ddclient-email" name="email" value="${email}" /><br /><br />
				<button class="ddclient-edit-save">Save Configuration</button>
				<button class="ddclient-edit-reset">Reset Configuration</button><br /><br />
				<button class="ddclient-edit-test-ddclient">Test DDClient Configuration</button>
				<button class="ddclient-edit-test-domain">Test Domain</button><br /><br />
				<button class="ddclient-enable-https">Enable HTTPS & Let's Crypt</button>
				<button class="ddclient-disable-https">Disable HTTPS</button>
			</form>
		`;

	add_content({details: details});

	if (data.domain === null || data.email === null) {
		$("button.ddclient-enable-https").prop("disabled", true);		
		$("button.ddclient-disable-https").prop("disabled", true);		
	} else {
		if (data.https_port === null) {
			$("button.ddclient-enable-https").prop("enabled", true);		
			$("button.ddclient-disable-https").prop("disabled", true);		
		} else {
			$("button.ddclient-enable-https").prop("disabled", true);		
			$("button.ddclient-disable-https").prop("enabled", true);		
		}
	}


	$("button.ddclient-edit-save").click(function(ev) {
		set_loading($(ev.target).parents(".app-content-details")[0]);
		
		let domain = $("input.ddclient-domain").val().trim();
		let conf = $("textarea.ddclient-edit").val().trim();
		let email = $("input.ddclient-email").val().trim();
		let data = Object();
		if (domain.length > 0)
			data.domain = domain;
		if (conf.length > 0)
			data.conf = conf;
		if (email.length > 0)
			data.email = email;
		
		request("/ddclient/config", "POST", function(resp) { 
			clear_loading();
		}, data);

		return false;
	});


	$("button.ddclient-edit-test-ddclient").click(function(ev) {
		set_loading($(ev.target).parents(".app-content-details")[0]);
		request("/ddclient/test/ddclient", "GET", function(resp) { 
			clear_loading();
		});

		return false;
	});
	
	$("button.ddclient-edit-test-domain").click(function(ev) {
		set_loading($(ev.target).parents(".app-content-details")[0]);
		request("/ddclient/test/domain", "GET", function(resp) { 
			clear_loading();
		});
		return false;
	});
	
	$("button.ddclient-edit-reset").click(function(ev) {
		render_dyndns();
		return false;
	});

	$("button.ddclient-enable-https").click(function(ev) {
		set_loading($(ev.target).parents(".app-content-details")[0]);
		notify("Enabling HTTPs, reloading once finished", 60000);
		request("/ddclient/enable", "GET", function(resp) { 
			//clear_loading();
		});
		
		$(document).ajaxComplete(function() {
			notify("Request completed, reloading in 5secs...");
			window.setTimeout(function() {
				//document.location.href = `https://${requested_host}`;
				location.reload(true);
			}, 5000);
			//location.reload(true);
		});

		return false;
	});
	
	$("button.ddclient-disable-https").click(function(ev) {
		set_loading($(ev.target).parents(".app-content-details")[0]);
		notify("Disabling HTTPs, reloading once finished", 60000);
		request("/ddclient/disable", "GET", function(resp) { 
			//clear_loading();
		});

		notify("Request completed, reloading in 5secs...");
		$(document).ajaxComplete(function() {
			window.setTimeout(function() {
				document.location.href = `http://${requested_host}`;
			}, 5000);
			//location.reload(true);
		});

		return false;
	});


}

function set_list_callbacks() {

	// click event for menu-toggle
	$(".app-content-list-item-menu > div.icon-more").click(function(ev) {
		let el = ev.target.parentElement.children[1];

		if ($(el).hasClass("open") === false) {
			$(el).addClass("open").fadeIn(250).delay(2500).fadeOut(250);
			window.setTimeout(function() {
				$(el).removeClass("open"); 
			}, 2750)
		}
	});

	// click event for umount
	$("button.storage-umount").click(function(ev) {
		let name = $(ev.target).parents(".app-content-list-item").first()
			.children(".app-content-list-item-line-two")
			.text().split(" ").slice(0, 1)[0].split("/")[2];

		set_loading($(ev.target).parents(".app-content-list-item")[0]);

		request(`/storage/umount/${name}`, "GET", function(resp) {
			render_storage();
		});
	});

	/*
	// click mount-name text field
	$("input.menu-mount-text").click(function(ev) {
		$(ev.target).val("");
	});

	// click event for mount
	$("input.menu-mount-submit").click(function(ev) {
		// @todo: check name for validity
		let name = $(ev.target).parent().children("input[type=text]").val().split(" ").slice(0, 1)[0];
		let dev = $(ev.target).parents(".app-content-list-item")
			.children(".app-content-list-item-details")
			.text().split("/")[2];

		set_loading($(ev.target).parents(".app-content-list-item")[0]);
		
		request(`/storage/mount/${dev}/${name}`, "GET", function(resp) {
			render_storage();
		});
		return false;
	});*/

	$("button.storage-backup-mount").click(function(ev) {
		let name = "backup";
		let dev = $(ev.target).parents(".app-content-list-item")
			.children(".app-content-list-item-details")
			.text().split("/")[2];
		
		set_loading($(ev.target).parents(".app-content-list-item")[0]);
		request(`/storage/mount/${dev}/${name}`, "GET", function(resp) {
			render_storage();
		});

	});

	$("button.storage-extra-mount").click(function(ev) {
		let dev = $(ev.target).parents(".app-content-list-item")
			.children(".app-content-list-item-details")
			.text().split("/")[2];

		set_loading($(ev.target).parents(".app-content-list-item")[0]);
		request(`/storage/mount/${dev}`, "GET", function(resp) {
			render_storage();
		});

	});


	// click event for backup, fire backup-start & delay reload for 1000ms
	$("button.start-backup").click(function(ev) {

		set_loading($(ev.target).parents(".app-content-list-item")[0]);

		request("/backup/start", "GET", function(resp) {
			$("button.start-backup").delay(1000, render_backup);
		});
	});

	// click event for restore, fire restore-start & delay for 1000ms
	$("button.start-restore").click(function(ev) {


		set_loading($(ev.target).parents(".app-content-list-item")[0]);

		let name = $(ev.target).parents(".app-content-list-item").first()
			.children(".app-content-list-item-line-one").text();
		request(`/backup/restore/${name}`, "GET", function(resp) {
			$("button.start-restore").delay(1000, render_backup);
		});
	});


	// timeout reload for backup progress-bar
	if ($("progress.backup-progress").length > 0) {


		set_loading($("#app-content-wrapper"));

		if(progress_interval === null) {
			progress_interval = window.setInterval(function() {
				request_direct("overview", "GET", function(resp) {	

					if (resp.data.backup.unable) {
						$("span.backup-progress-step").text(`Unable to ${resp.data.backup.what} "${resp.data.backup.unable}"`);
						$("progress.backup-progress").val(0);
						$("span.backup-progress-percent").text("[fail]");
						window.clearInterval(progress_interval);
						progress_interval = null;
						clear_loading();
						fail_notify(`Operation: ${resp.data.backup.what} failed, check logs...`);
						return;					
					}

					if (resp.data.backup.running) {
						$("progress.backup-progress").val(resp.data.backup.progress);
						let step = (resp.data.backup.step === undefined) ? "init" : resp.data.backup.step;
						$("span.backup-progress-step").text(`${resp.data.backup.what} step: ${step}`);
						let percent = resp.data.backup.progress;
						if (percent == undefined || percent === null)
							percent = "0.0";
						$("span.backup-progress-percent").text(percent + "%");
					} else {
						$("progress.backup-progress").val(100);
						$("span.backup-progress-step").text(`${resp.data.backup.step}`);
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

		set_loading($(ev.target).parents(".app-content-list-item"));

		let name = $(ev.target).parents(".app-content-list-item")
			.children(".app-content-list-item-details").text();
			request(`/service/${name}/start`, "GET", function(rest) {
				render_dyndns();
			});
	});
	$("button.service-stop").click(function(ev) {

		set_loading($(ev.target).parents(".app-content-list-item"));

		let name = $(ev.target).parents(".app-content-list-item")
			.children(".app-content-list-item-details")
			.text();
			request(`/service/${name}/stop`, "GET", function(rest) {
				render_dyndns();
			});

	});
	$("button.service-restart").click(function(ev) {

		set_loading($(ev.target).parents(".app-content-list-item"));

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
		.filter(dev => (!(is_mounted ^ mounted_devs.includes(dev)))) 
		.map(dev => {
			
			let block_dev = dev.split("/").slice(-1)[0].slice(0, 3);
			let desc = data.block_devs[block_dev].name;

			let two = (mounted[dev]) ? mounted[dev] + ` (${data.type[dev]})` : "(not mounted)";

			let ret = Object({
				icon: "HD",
				two: two,
				details: dev
			});

			ret.bg = "rgb(100, 155, 155)";
			if (!is_mounted && mounted_devs.includes(dev))
				ret.bg = "rgb(220, 220, 220)";

			ret.one = desc;
			if (mounted_devs.includes(dev)) {
				ret.one = `Extra (${desc})`;
				if (data.main == dev)
					ret.one = `Main (${desc})`;
				else if (data.backup == dev) 
					ret.one = `Backup (${desc})`; 
			}

			if (data.main != dev) {
				if (mounted_devs.includes(dev)) {
					ret.menu = [
						{icon: "close", name: "Unmount Partition", cls: "storage-umount"}
					];
				} else {
					
					ret.menu = [{icon: "add", name: "Mount as Extra Storage", cls: "storage-extra-mount"}];
					if (data.backup === null) 
						ret.menu.push({icon: "folder", name: "Mount as Backup Storage", cls: "storage-backup-mount"});

					//ret.menu.push({icon: "folder", input_value: "[mount-name]"});
				}
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
	
	let state = resp.data.output[0];
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
		clear_loading();
		set_content({list: render_list("Backup / Restore Overview", assemble_backup_overview(resp.data.backup))});
		add_content({list: render_list("Mounted Storage(s)", assemble_storage(resp.data.storage, true))});
		request("/service/ddclient/is-active", "GET", function(resp) {
			add_content({list: render_list("Service Status", assemble_ddclient_status(resp))});
			set_list_callbacks();
		});
	});
}


function render_storage() {

	request("/storage", "GET", function(resp) {
		clear_loading();
		set_content({list: render_list("Mounted Storages",	assemble_storage(resp.data, true))});
		add_content({list: render_list("Available Storages",	assemble_storage(resp.data, false))});
		set_list_callbacks();
	});
}


function render_backup() {
	request("/backup", "GET", function(resp) {
		clear_loading();
		set_content({list: render_list("Backup / Restore Overview", assemble_backup_overview(resp.data))});
		add_content({list: render_list("Available Backups", assemble_backup_available(resp.data.found))});
		set_list_callbacks();
	});
}

function render_dyndns() {
	request("/service/ddclient/is-active", "GET", function(resp) {
		clear_loading();
		set_content({list: render_list("Service Status", assemble_ddclient_status(resp))});
		set_list_callbacks();
		request("/ddclient/config", "GET", function(resp) {
			add_ddclient_edit(resp.data);
		});
	});
}

function render_log() {
	request("/log", "GET", function(resp) {
		clear_loading();
		set_content({details: assemble_log(resp.data)});
	});
}


function render_settings_section(id, content, headline, hint, warning) {

    let _hint = (hint) ? `<p class="settings-hint">${hint}</div>` : "";
    let _warning = (warning) ? `<p class="warning">${warning}</div>` : "";
    let _headline = (headline) ? `<h2>${headline}</h2>` : "";
    return `<div id="${id}" class="section">
        ${_headline}
        ${_hint}
        <p>${content}</p>
        ${_warning}
    </div>`;
}

function set_system_callbacks() {

}

function render_button(text, cls, icon) {
    if (icon)
       cls += ` icon-${icon}`;

    return `<button class="${cls}">${text}</button>`;
}

function render_text_input(name, cls, val, id, label) {
    let _label = (label) ? `<label>${label}</label>` : "";
    let _id = (id) ? ` id="${id}"` : "";
    return `${_label}<input type=text${_id} class="${cls}" name="${name}" value="${val}" />`;
}

function render_radio_input(headline, label, name, options) {

    let _opts = options.map(
        (opt) => `
            <input type="radio" name="${name}" value="${opt.value}" id="${opt.id}" />
            <label for="${opt.id}">${opt.label}</label>
    `).join("");

    let _label = (label) ? `<em>${label}</em>` : "";
    let _headline = (headline) ? `<h2>${headline}</h2>` : "";

    return `${_headline}${_label}${_opts}`;
}


function render_form() {

}


function render_system() {
    request("/system", "GET", function(resp) {
        clear_loading();

        let _lvls = [{id: "log_lvl_20", label: "Regular Logging", value: 20},
                     {id: "log_lvl_10", label: "Verbose Logging", value: 10}];
        let _expert = [{id: "expert_on", label: "Expert mode active", value: "on"},
                       {id: "expert_off", label: "Expert mode inactive", value: "off"}];

        set_content({raw: render_settings_section("system-config-log-lvl",
            render_radio_input("Logging Level", "log_lvl", _lvls)
        )});
        add_content({raw: render_settings_section("system-config-expert-mode",
            render_radio_input("Expert Mode", "expert_mode", _expert)
        )});

    });
}


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


