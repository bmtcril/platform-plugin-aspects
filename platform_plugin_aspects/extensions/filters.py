"""
Open edX Filters needed for Aspects integration.
"""

import pkg_resources
from crum import get_current_user
from django.conf import settings
from django.template import Context, Template
from openedx_filters import PipelineStep
from web_fragments.fragment import Fragment

from platform_plugin_aspects.utils import _, generate_superset_context, get_model

TEMPLATE_ABSOLUTE_PATH = "/instructor_dashboard/"
BLOCK_CATEGORY = "aspects"

ASPECTS_SECURITY_FILTERS_FORMAT = [
    "org = '{course.org}'",
    "course_name = '{course.display_name}'",
    "course_run = '{course.id.run}'",
]


class AddSupersetTab(PipelineStep):
    """
    Add superset tab to instructor dashboard.
    """

    def run_filter(
        self, context, template_name
    ):  # pylint: disable=arguments-differ, unused-argument
        """Execute filter that modifies the instructor dashboard context.
        Args:
            context (dict): the context for the instructor dashboard.
            _ (str): instructor dashboard template name.
        """
        course = context["course"]
        dashboards = settings.ASPECTS_INSTRUCTOR_DASHBOARDS
        extra_filters_format = settings.SUPERSET_EXTRA_FILTERS_FORMAT

        filters = ASPECTS_SECURITY_FILTERS_FORMAT + extra_filters_format

        user = get_current_user()

        user_language = (
            get_model("user_preference").get_value(user, "pref-lang") or "en_US"
        )
        formatted_language = user_language.replace("-", "_")
        if formatted_language not in settings.SUPERSET_DASHBOARD_LOCALES:
            formatted_language = "en_US"

        context = generate_superset_context(
            context,
            user,
            dashboards=dashboards,
            filters=filters,
            language=formatted_language,
        )

        template = Template(self.resource_string("static/html/superset.html"))
        html = template.render(Context(context))
        frag = Fragment(html)
        frag.add_css(self.resource_string("static/css/superset.css"))
        frag.add_javascript(self.resource_string("static/js/embed_dashboard.js"))
        section_data = {
            "fragment": frag,
            "section_key": BLOCK_CATEGORY,
            "section_display_name": _("Analytics"),
            "course_id": str(course.id),
            "superset_url": str(context.get("superset_url")),
            "template_path_prefix": TEMPLATE_ABSOLUTE_PATH,
        }
        context["sections"].append(section_data)
        return {
            "context": context,
        }

    def resource_string(self, path):
        """Handy helper for getting resources from our kit."""
        data = pkg_resources.resource_string("platform_plugin_aspects", path)
        return data.decode("utf8")
