function set_dyndns_callbacks() {

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


function set_system_callbacks() {

}
