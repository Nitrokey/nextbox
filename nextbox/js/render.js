
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


