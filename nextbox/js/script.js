
var token = null;
var token_created = null;
var token_max_age = 55 * 5 * 1e3;
var progress_interval = null;
var requested_host = null;



function request_raw(raw_url, method, on_done) {
	let req = function() {
		$.ajax({
			url: raw_url,
			type: method, 
			ContentType: "application/json"
		})
		.done(on_done)
		.fail(function(resp, code) {
			console.error([raw_url, resp, code]);
		});
	};
	
	// refresh token, if needed
	let token_age = Math.abs(token_created - (new Date()));
	if (!token || token_age > token_max_age)
		request_token(req);
	else
		req();
}

function request(url, method, on_done) {
	return request_raw(requested_host + ":18585" + url + "?token=" + token, method, on_done);
}


function request_token(on_done) {
	$.ajax({
		url: "token", 
		type: "GET"
	}).done(function(resp) {
		token = resp.token;
		token_created = new Date();
		
		if (on_done)
			on_done();

	}).fail(function(resp, code) {
		token = null;
		token_created = null;
		console.error(["failed init token", resp, code]);
	});
}

// request comm-token (asap, thus here)
request_token();


function set_content(details, items) {
	$("#app-content-wrapper").html(details);

	// click event for menu-toggle
	$(".app-content-list-item-menu > div.icon-more").click(function(ev) {
		ev.target.parentElement.children[1].classList.toggle("open");
	});

	// click event for umount
	$("button.icon-close").click(function(ev) {
		let name = $(ev.target).parents(".app-content-list-item").first()
			.children(".app-content-list-item-line-two")
			.text().split("/")[2];

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
		let name = $(ev.target).parent().first().children("input[type=text]").val();
		let dev = $(ev.target).parents(".app-content-list-item").first()
			.children(".app-content-list-item-details")
			.text().split("/")[2];

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

}

function render_list(headline, data) {

	let pre = `<div class="app-content-list">`;
	if (headline)
		pre += `<h2>${headline}</h2>`;
	let post = `</div>`;

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
					ret.menu = new Array( new Object({icon: "close", name: "umount"}) );
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


function render_overview() {
	request("/overview", "GET", function(resp) {
		let backup = render_list("Backup / Restore Overview", assemble_backup_overview(resp.backup));
		let storage = render_list("Mounted Storage(s)", assemble_storage(resp.storage, true));
		set_content(backup + storage);
	});
}


function render_storage() {

	request("/storage", "GET", function(resp) {
		let mounted = render_list("Mounted Storages",	assemble_storage(resp.data, true));
		let available = render_list("Available Storages",	assemble_storage(resp.data, false));
		set_content(mounted + available);
	});
}


function render_backup() {
		request("/backup", "GET", function(resp) {
		let backup = render_list("Backup / Restore Overview", assemble_backup_overview(resp.data));
		let available = render_list("Available Backups", assemble_backup_available(resp.data.found));
		set_content(backup + available);
	});
}

function render_dyndns() {


}


$(function() {

	requested_host = document.location.origin;

	$("#nav_overview").click(render_overview);
	$("#nav_storage").click(render_storage);
	$("#nav_backup").click(render_backup);
	$("#nav_dyndns").click(render_dyndns);

	render_overview();

});


