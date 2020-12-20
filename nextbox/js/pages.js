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
	set_dyndns_callbacks();
}
