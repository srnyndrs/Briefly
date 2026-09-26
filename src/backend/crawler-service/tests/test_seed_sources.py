from src.scripts.seed_sources import _build_source


def test_seed_source_uses_model_fields_and_is_verified():
    source = _build_source(
        {
            "url": "https://www.origo.hu/rss",
            "title": "ORIGO",
            "content_type": "application/rss+xml",
        }
    )

    assert source.verified is True
    assert source.submitted_by_user_id is None
    assert source.registrable_domain == "origo.hu"
    assert not hasattr(source, "content_type")
