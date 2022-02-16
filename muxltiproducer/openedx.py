import re
import typing as t

from django.conf import settings


def course_pattern_match(course_id: str) -> t.Optional[t.Tuple[str]]:
    """
    Returns: org, course, run for given course ID. Return None if it does not
    correspond to an Open edX course ID pattern.
    """
    match = re.match(
        r"course-v1:(?P<organization>[^+]+)\+(?P<course>[^+]+)\+(?P<run>[^+]+)",
        course_id,
    )
    return match.groups() if match else None  # type: ignore


def course_access_limit_regex(course_id: str) -> t.Optional[str]:
    """
    Return the regular expression to limit access to the people from the same org/course/run as the course_id.
    Return None if there is no limit. If the course ID does not match the Open
    edX course ID pattern, limit to assets in the same context ID, for safety.
    """
    access_limited_to = getattr(
        settings,
        "MUX_ASSET_INSTRUCTOR_ACCESS_LIMITED_TO",
        None,
    )
    if not access_limited_to:
        return None
    match = course_pattern_match(course_id)
    if not match:
        return course_id
    org: str
    course: str
    run: str
    org, course, run = match  # type: ignore
    if access_limited_to == "ORGANIZATION":
        return rf"^course-v1:{org}"
    if access_limited_to == "COURSE":
        return rf"^course-v1:{org}\+{course}"
    if access_limited_to == "RUN":
        return rf"^course-v1:{org}\+{course}\+{run}"
    raise ValueError(f"Incorrect value for access limit setting: '{access_limited_to}'")
