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
