import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from ckan.logic import get_action
import logging

from ckanext.c3charts.model.featured_charts import setup as setup_featured_charts_model
import ckanext.c3charts.helpers as helpers
import ckanext.c3charts.logic as logic

logger = logging.getLogger(__name__)
not_empty = plugins.toolkit.get_validator('not_empty')
ignore_missing = plugins.toolkit.get_validator('ignore_missing')
ignore_empty = plugins.toolkit.get_validator('ignore_empty')


class ChartsPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer, inherit=True)
    plugins.implements(plugins.IResourceView, inherit=True)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IActions)

    # IConfigurer

    def update_config(self, config):
        toolkit.add_template_directory(config, 'templates')
        toolkit.add_public_directory(config, 'public')
        toolkit.add_resource('assets', 'c3charts')

        setup_featured_charts_model()

    def info(self):
        schema = {
            'chart_type': [not_empty],
            'key_fields': [not_empty],
            'featured': [ignore_missing],
            'x_fields': [ignore_missing],
            'color_scheme': [not_empty],
            'header': [ignore_missing],
            'measure_unit_x': [ignore_missing],
            'measure_unit_y': [ignore_missing],
            'text_chart_number_action': [not_empty],
            'legend': [not_empty],
            'rotated': [ignore_missing],
            'data_labels': [ignore_missing],
            'x_grid': [ignore_missing],
            'y_grid': [ignore_missing],
            'remap_key': [ignore_missing],
            'aggregate': [ignore_missing]
        }

        return {'name': toolkit._('Chart builder'),
                'icon': 'bar-chart-o',
                'filterable': True,
                'iframed': False,
                'schema': schema}

    def can_view(self, data_dict):
        return data_dict['resource'].get('datastore_active', False)

    def setup_template_variables(self, context, data_dict):
        resource = data_dict['resource']
        resource_view = data_dict['resource_view']

        fields = _get_fields_without_id(resource)
        remap_keys = list(fields)
        remap_keys.insert(0, {'value': ''})
        logger.debug(remap_keys)

        return {'resource': resource,
                'resource_view': resource_view,
                'fields': fields,
                'remap_keys': remap_keys,
                'chart_types': [{'value': 'Bar Chart'},
                                {'value': 'Stacked Bar Chart'},
                                {'value': 'Donut Chart'},
                                {'value': 'Line Chart'},
                                {'value': 'Pie Chart'},
                                {'value': 'Spline Chart'},
                                {'value': 'Table Chart'},
                                {'value': 'Simple Chart'}],
                'color_schemes': [{'value': '#4781BF, #A1BBE5, #E59539, #E8CE8B, #6F5DA8, '
                                            '#CDABDB, #3D9990, #7CCFB4, #4C5FB5, #979ACC, '
                                            '#CC5E69, #EDA19F, #4692B0, #8BD4D6, #E0694F, '
                                            '#F5A482, #549970, #9AD9A4, #9C4174, #CF7C92',
                                   'text': toolkit._('Default')},
                                  {'value': '#B80000, #995522, #556677, #118888, #115588, '
                                            '#4C3D3D, #2B2B2B, #660000, #221100',
                                   'text': toolkit._('Saturated')},
                                  {'value': '#DDBBAA, #79E6F2, #88AA99, #00A864, #228899, '
                                            '#3F797F, #775555, #118855, #008751, #3D4C46',
                                   'text': toolkit._('Light')},
                                  {'value': '#ADC0D8, #79AFF2, #8899AA, #0EAAB2, #00A0A8, '
                                            '#776655, #118888, #885511, #3F5C7F, #225599',
                                   'text': toolkit._('Pastel')},
                                  {'value': '#ADB1D8, #8899AA, #7983F2, #777752, #887711, '
                                            '#0070C0, #0062A8, #3F457F, #115588, #3D464C',
                                   'text': toolkit._('Pastel 2')},
                                  {'value': '#AA9988, #A88600, #779922, #6C7F3F, #887711, '
                                            '#555577, #665500, #665100, #4C493D, #2B2B2V',
                                   'text': toolkit._('Contrast')}],
                'text_chart_number_actions': [{'value': 'substract',
                                               'text': toolkit._('Substract last two entries')},
                                              {'value': 'average',
                                               'text': toolkit._('Average')},
                                              {'value': 'last',
                                               'text': toolkit._('Show last')}],
                'legend_options': [{'text': toolkit._('Hide'), 'value': 'hide'},
                                   {'text': toolkit._('Right'), 'value': 'right'},
                                   {'text': toolkit._('Bottom'), 'value': 'bottom'}]
                }

    def view_template(self, context, data_dict):
        return 'charts_view.html'

    def form_template(self, context, data_dict):
        return 'charts_form.html'

    # ITemplateHelpers
    def get_helpers(self):
        return {
            'c3charts_featured_charts': helpers.c3charts_featured_charts,
            'c3charts_render_featured_chart': helpers.c3charts_render_featured_chart,
            'c3charts_uuid': helpers.c3charts_uuid
        }

    # ITActions
    def get_actions(self):
        orig_resource_view_create = get_action('resource_view_create')
        orig_resource_view_delete = get_action('resource_view_delete')
        orig_resource_view_update = get_action('resource_view_update')
        orig_resource_delete = get_action('resource_delete')
        orig_package_delete = get_action('package_delete')
        return {
            'resource_view_create': override_resource_view_create(orig_resource_view_create),
            'resource_view_delete': override_resource_view_delete(orig_resource_view_delete),
            'resource_view_update': override_resource_view_update(orig_resource_view_update),
            'resource_delete': override_resource_delete(orig_resource_delete),
            'package_delete': override_package_delete(orig_package_delete)

        }


def _get_fields_without_id(resource):
    fields = _get_fields(resource)
    return [{'value': v['id']} for v in fields if v['id'] != '_id']


def _get_fields(resource):
    data = {
        'resource_id': resource['id'],
        'limit': 0
    }
    result = plugins.toolkit.get_action('datastore_search')({}, data)
    return result['fields']


def override_resource_view_create(orig_resource_view_create):

    def _resource_view_create(context, data_dict):
        result = orig_resource_view_create(context, data_dict)
        if not context.get('preview'):
            if data_dict.get('featured'):
                package_id = result['package_id']
                resource_id = result['resource_id']
                view_id = result["id"]
                logic.save_featured_chart(package_id, resource_id, view_id)
        return result

    return _resource_view_create


def override_resource_view_delete(orig_resource_view_delete):

    def _resource_view_delete(context, data_dict):
        result = orig_resource_view_delete(context, data_dict)
        logic.remove_from_featured_charts(data_dict['id'])
        return result

    return _resource_view_delete


def override_resource_view_update(orig_resource_view_update):

    def _resource_view_update(context, data_dict):
        result = orig_resource_view_update(context, data_dict)
        if not context.get('preview'):
            package_id = result['package_id']
            resource_id = result['resource_id']
            view_id = result["id"]
            if data_dict.get('featured'):
                logic.save_featured_chart(package_id, resource_id, view_id)
            else:
                logic.remove_from_featured_charts(view_id)
        return result

    return _resource_view_update


def override_resource_delete(orig_resource_delete):

    def _resource_delete(context, data_dict):
        result = orig_resource_delete(context, data_dict)
        resource_id = data_dict.get('id')
        if resource_id:
            logic.remove_all_featured_charts_for_resource(resource_id)
        return result
    return _resource_delete


def override_package_delete(orig_package_delete):

    def _package_delete(context, data_dict):
        result = orig_package_delete(context, data_dict)
        package_id = data_dict.get('id')
        if package_id:
            logic.remove_all_featured_charts_for_package(package_id)
        return result

    return _package_delete
