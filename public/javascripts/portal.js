var Portal = new Object();

Portal.nodePath = function(node) {
	if (node.depth == 0) {
		return node.label;
	} else {
		return Portal.nodePath(node.parent) + '/' + node.label;
	}
}

Portal.getTreeNodeByLabel = function(node, label) {
	for (i=0; i<node.children.length; i++) {
		if (node.children[i].label == label)
			return node.children[i];
	}
	return null;
}

Portal.getTreeNodeById = function(node, id) {
	for (i=0; i<node.children.length; i++) {
		if (node.children[i].id == id)
			return node.children[i];
	}
	return null;
}

Portal.expandTreeNode = function(node) {
	node.expand();
	if (node.parent != null) {
		Portal.expandTreeNode(node.parent);
	}
}

Portal.expandTreeNodeByLabel = function(node, label) {
	if (node.label == label) {
		Portal.expandTreeNode(node);
	}
	for (var i=0; i<node.children.length; i++) {
		Portal.expandTreeNodeByLabel(node.children[i], label);
	}
}

Portal.tinyMCEinit = function() {
	tinyMCE.init({
		mode: "textareas",
		theme: "advanced",
		plugins: "table,save,advlink,emotions,iespell,preview,print,contextmenu,media,paste",
		theme_advanced_buttons1_add_before: "save,|",
		theme_advanced_buttons1_add: "forecolor,backcolor,hr,removeformat,visualaid",
		theme_advanced_buttons2_add_before: "cut,copy,paste,|",
		theme_advanced_buttons2_add: "|,print,preview",
		theme_advanced_buttons3_add_before: "media,tablecontrols",
		theme_advanced_buttons3_add: "|,pastetext,pasteword,selectall",
		theme_advanced_disable: "styleselect",
		theme_advanced_toolbar_location: "top",
		theme_advanced_toolbar_align: "left",
		theme_advanced_path_location: "bottom",
		extended_valid_elements: "a[name|href|target|title|onclick|id|class|rel],img[class|src|border=0|alt|title|hspace|vspace|width|height|align|onmouseover|onmouseout|name],hr[class|width|size|noshade],font[size|color|style],span[class|align|style],div[id|class],iframe[src|width|height|name|align]",
		relative_urls: false,
		remove_script_host: false,
		auto_cleanup_word: true,
		content_css: "/stylesheets/editor.css"
	});
	tinyMCE.baseURL = "/javascripts/tiny_mce";
}

Portal.loadTinyMCE = function(id) {
	tinyMCE.execCommand('mceAddControl', false, id);
}

Portal.unloadTinyMCE = function(id) {
	tinyMCE.execCommand('mceRemoveControl', false, id);
}

Portal.slideDown = function(id, ctrl) {
	$('#' + ctrl).hide();
	$('#' + id).slideDown();
	return false;
}
