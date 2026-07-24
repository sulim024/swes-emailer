"""Filter behaviour against the real config/filters.yaml."""

from datetime import date, timedelta

from src import config
from src.filters import passes
from src.models import Job


def _job(title, locations=None, **kw):
    return Job(
        company=kw.pop("company", "Acme"),
        title=title,
        url=kw.pop("url", f"https://example.com/{abs(hash(title)) % 10000}"),
        locations=locations or [],
        **kw,
    )


F = config.filters()


def test_software_intern_us_kept():
    j = _job("Software Engineer Intern", ["New York, NY"])
    assert passes(j, F)
    assert j.category == "software"
    assert j.season == "summer" or j.season is None  # season may be undetected from title


def test_ml_intern_classified_as_data_ml():
    j = _job("Machine Learning Intern", ["Santa Clara, CA"])
    assert passes(j, F)
    assert j.category == "data_ml"


def test_firmware_intern_kept():
    j = _job("Firmware Engineering Intern", ["Boston, MA"])
    assert passes(j, F)
    assert j.category == "firmware"


def test_fulltime_senior_role_rejected():
    j = _job("Senior Software Engineer", ["San Francisco, CA"])
    assert not passes(j, F)


def test_new_grad_role_kept():
    j = _job("Software Engineer, New Grad", ["Seattle, WA"])
    # config sets allow_new_grad: true, so new-grad roles are kept
    assert passes(j, F)
    assert j.category == "software"


def test_non_us_location_rejected():
    j = _job("Software Engineer Intern", ["London, UK"])
    assert not passes(j, F)


def test_canada_rejected():
    j = _job("Embedded Software Intern", ["Toronto, Canada"])
    assert not passes(j, F)


def test_unknown_location_kept():
    j = _job("Software Engineer Intern")
    assert passes(j, F)  # keep_when_location_unknown: true


def test_multi_location_with_us_option_kept():
    j = _job("Software Engineer Intern", ["London, UK", "New York, NY"])
    assert passes(j, F)


def test_non_category_intern_rejected():
    j = _job("Marketing Intern", ["New York, NY"])
    assert not passes(j, F)


def test_out_of_window_year_rejected():
    j = _job("Software Engineer Intern, Summer 2025", ["Austin, TX"])
    assert not passes(j, F)


def test_coop_kept():
    j = _job("Software Engineer Co-op", ["Boston, MA"])
    assert passes(j, F)


def test_remote_kept():
    j = _job("Firmware Engineer Intern", ["Remote"])
    assert passes(j, F)


def test_non_software_intern_rejected():
    # non-software titles should no longer match any category
    j = _job("Mechanical Engineer Intern", ["New York, NY"])
    assert not passes(j, F)


def test_remote_kept_2():
    j = _job("Backend Engineer Intern", ["Remote"])
    assert passes(j, F)


def test_old_posting_rejected_when_freshness_limit_set():
    cfg = dict(F)
    cfg["role"] = dict(F["role"])
    cfg["role"]["max_posted_age_days"] = 7
    old_date = (date.today() - timedelta(days=8)).isoformat()
    j = _job("Software Engineer Intern", ["New York, NY"], posted_date=old_date)
    assert not passes(j, cfg)


def test_recent_posting_kept_when_freshness_limit_set():
    cfg = dict(F)
    cfg["role"] = dict(F["role"])
    cfg["role"]["max_posted_age_days"] = 7
    recent_date = (date.today() - timedelta(days=3)).isoformat()
    j = _job("Software Engineer Intern", ["New York, NY"], posted_date=recent_date)
    assert passes(j, cfg)
