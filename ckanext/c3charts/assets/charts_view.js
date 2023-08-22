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
        var routeFilters = ckan.views.filters ? ckan.views.filters.get() : {};

        return $.extend({}, defaultFilters, routeFilters);
    }

    return {
        initialize: function () {
            var self = this,
                endpoint = self.options.endpoint || self.sandbox.client.endpoint + "/api",
                resourceView = self.options.resourceView,
                params = setupParams(resourceView),
                elementId = self.el.context ? "#"+self.el.context.id : "#"+self.el[0].id,
                resource = {
                    id: self.options.resourceId,
                    endpoint: endpoint
                };
            ckan.views.c3charts.init(elementId, resource, resourceView, params);
        }
    }
});
