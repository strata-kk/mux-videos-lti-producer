from django.test import TestCase, override_settings

from muxltiproducer import models


class MuxLtiProducerTests(TestCase):
    def test_filter_by_openedx_context(self) -> None:
        lti_context1 = models.LtiContext.objects.create(
            context_id="course-v1:org1+course1+run1"
        )
        lti_context2 = models.LtiContext.objects.create(
            context_id="course-v1:org1+course1+run2"
        )
        lti_context3 = models.LtiContext.objects.create(
            context_id="course-v1:org1+course2+run1"
        )
        lti_context4 = models.LtiContext.objects.create(
            context_id="course-v1:org2+course1+run1"
        )
        _lti_context5 = models.LtiContext.objects.create(context_id="dummy")
        models.Asset.objects.create(mux_id="1", lti_context=lti_context1)
        models.Asset.objects.create(mux_id="2", lti_context=lti_context2)
        models.Asset.objects.create(mux_id="3", lti_context=lti_context3)
        models.Asset.objects.create(mux_id="4", lti_context=lti_context4)

        course_id = lti_context1.context_id

        with override_settings(MUX_ASSET_INSTRUCTOR_ACCESS_LIMITED_TO=None):
            self.assertEqual(["1", "2", "3", "4"], get_mux_asset_ids(course_id))

        with override_settings(MUX_ASSET_INSTRUCTOR_ACCESS_LIMITED_TO="ORGANIZATION"):
            self.assertEqual(["1", "2", "3"], get_mux_asset_ids(course_id))

        with override_settings(MUX_ASSET_INSTRUCTOR_ACCESS_LIMITED_TO="COURSE"):
            self.assertEqual(["1", "2"], get_mux_asset_ids(course_id))

        with override_settings(MUX_ASSET_INSTRUCTOR_ACCESS_LIMITED_TO="RUN"):
            self.assertEqual(["1"], get_mux_asset_ids(course_id))

    def test_filter_by_openedx_context_no_match(self) -> None:
        lti_context1 = models.LtiContext.objects.create(
            context_id="course-v1:org1+course1+run1"
        )
        lti_context2 = models.LtiContext.objects.create(context_id="dummy")
        models.Asset.objects.create(mux_id="1", lti_context=lti_context1)
        models.Asset.objects.create(mux_id="2", lti_context=lti_context2)

        # By default there is no filter
        self.assertEqual(["1", "2"], get_mux_asset_ids("dummy"))

        with override_settings(MUX_ASSET_INSTRUCTOR_ACCESS_LIMITED_TO="ORGANIZATION"):
            self.assertEqual(["2"], get_mux_asset_ids("dummy"))
        with override_settings(MUX_ASSET_INSTRUCTOR_ACCESS_LIMITED_TO="COURSE"):
            self.assertEqual(["2"], get_mux_asset_ids("dummy"))
        with override_settings(MUX_ASSET_INSTRUCTOR_ACCESS_LIMITED_TO="RUN"):
            self.assertEqual(["2"], get_mux_asset_ids("dummy"))


def get_mux_asset_ids(course_id: str):
    return [
        asset.mux_id
        for asset in models.Asset.objects.filter_visible(course_id)
        .order_by("mux_id")
        .all()
    ]
