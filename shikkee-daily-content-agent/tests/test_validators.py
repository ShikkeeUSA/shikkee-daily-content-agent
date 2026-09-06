from shikkee_agent.pipeline.validators import validate_copy


def test_flags_banned_terms():
    result = validate_copy("Our prefabricated homes ship fast.")
    assert not result.ok
    assert "prefabricated" in result.banned_terms


def test_flags_em_dash():
    result = validate_copy("Fixed price — not a promotion.")
    assert not result.ok
    assert result.em_dash_count == 1


def test_clean_copy_passes():
    result = validate_copy("Fixed price, not a promotion. Shikkee it.")
    assert result.ok


def test_unverified_tags_surface_but_dont_fail():
    result = validate_copy("Clean copy.", verified_tags={"RoMac Building Supply": None, "NAHB": "@NAHBhome"})
    assert result.ok  # missing a handle is fine, it's just surfaced
    assert result.unverified_tags == ["RoMac Building Supply"]
