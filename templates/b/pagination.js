{% load i18n %}

new YAHOO.widget.Button('create-object-button');

paginator = new YAHOO.widget.Paginator({
	rowsPerPage:{{ ITEMS_PER_PAGE }},
	totalRecords: {{ total }},

	firstPageLinkLabel: "&laquo; {% trans "first" %}",
	previousPageLinkLabel: "&lsaquo; {% trans "previous" %}",
	nextPageLinkLabel: "{% trans "next" %} &rsaquo;",
	lastPageLinkLabel: "{% trans "last" %} &raquo;"
});

var oConfigs = {
	dynamicData: true,
	paginator: paginator,
	generateRequest: function(oState, oSelf) {
		return "page=" + oState.pagination.page;
	},
	MSG_ERROR: Portal.connectionFailure
};

var oDataTable = new YAHOO.widget.DataTable("object-table", oColumnDefs,
		oDataSource, oConfigs);

return {
	oDS: oDataSource,
	oDT: oDataTable
};
