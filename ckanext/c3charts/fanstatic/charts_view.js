ckan.module('c3charts_builder', function ($, _) {
    "use strict";

    function setupParams(defaultParams) {
        var routeParams = window.location.search.queryStringToJSON(),
            params = {
                filters: setupFilters(defaultParams.filters)
            };

        return $.extend({}, defaultParams, routeParams, params);
    }

    function setupFilters(defaultFilters) {
        var routeFilters = {};
        try {
            if (window.parent.ckan.views && window.parent.ckan.views.filters) {
                routeFilters = window.parent.ckan.views.filters.get();
            }
        } catch(e) {}

        return $.extend({}, defaultFilters, routeFilters);
    }

    return {
        initialize: function () {
            var self = this,
                endpoint = self.options.endpoint || self.sandbox.client.endpoint + "/api",
                resourceView = self.options.resourceView,
                params = setupParams(resourceView),
                elementId = "#" + self.el.context.id,
                resource = {
                    id: self.options.resourceId,
                    endpoint: endpoint
                };
            ckan.views.c3charts.init(elementId, resource, resourceView, params);
        }
    }
});
