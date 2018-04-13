from tethys_sdk.base import TethysAppBase, url_map_maker


class BldasExplorer(TethysAppBase):
    """
    Tethys app class for BLDAS Explorer.
    """

    name = 'BLDAS Explorer Beta'
    index = 'bldas_explorer:home'
    icon = 'bldas_explorer/images/logo.png'
    package = 'bldas_explorer'
    root_url = 'bldas-explorer'
    color = '#2980b9'
    description = 'View SALDAS data for Bangladesh'
    tags = ''
    enable_feedback = False
    feedback_emails = []

    def url_maps(self):
        """
        Add controllers
        """
        UrlMap = url_map_maker(self.root_url)

        url_maps = (
            UrlMap(
                name='home',
                url='bldas-explorer',
                controller='bldas_explorer.controllers.home'
            ),
            UrlMap(
                name='get-plot',
                url='bldas-explorer/get-plot',
                controller='bldas_explorer.controllers.get_plot'
            ),
            UrlMap(
                name='get-point-stats',
                url='bldas-explorer/api/getPointStats',
                controller='bldas_explorer.api.get_point_ts'
            ),
            UrlMap(
                name='get-feature-stats',
                url='bldas-explorer/api/getFeatureStats',
                controller='bldas_explorer.api.geo_json_stats'
            ),
            UrlMap(
                name='get-poly-stats',
                url='bldas-explorer/api/getPolygonStats',
                controller='bldas_explorer.api.get_poly_ts'
            ),
            UrlMap(
                name='get-poly-stats-post',
                url='bldas-explorer/api/getPolygonStatsPost',
                controller='bldas_explorer.api.get_poly_ts_post'
            ),
        )

        return url_maps
