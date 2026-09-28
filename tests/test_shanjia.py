from core.shanjia import calculate_days, get_options


def test_reference_mountain_table():
    options = get_options()
    mountains = options["mountains"]
    assert len(mountains) == 24
    assert mountains[0]["name"] == "壬"
    assert mountains[0]["element"] == "水"
    assert mountains[1]["name"] == "子"
    assert mountains[9]["name"] == "辰"
    assert mountains[23]["name"] == "亥"


def test_reference_jian_and_fenjin():
    m = get_options()["mountains"][0]
    assert [item["value"] for item in m["jian"]] == ["亥巳", "正针", "子午"]
    assert m["fenjin"] == ["乙亥", "丁亥", "己亥", "辛亥", "癸亥"]


def test_calculate_days_returns_calendar_data():
    result = calculate_days(
        {
            "start_date": "2026-09-28",
            "end_date": "2026-10-08",
            "use_type": "建造",
            "mountain_id": 1,
            "life_years": ["1988"],
            "level": "全部",
            "hours": [0, 12],
        }
    )
    assert result["mountain"]["name"] == "壬"
    assert result["life_ganzhi"]
    assert result["results"]
    first = result["results"][0]
    assert len(first["day_ganzhi"]) == 2
    assert "month_ganzhi" in first
    assert len(first["hours"]) == 2


def test_manual_favorable_month_filter():
    result = calculate_days(
        {
            "start_date": "2026-01-01",
            "end_date": "2026-12-31",
            "use_type": "建造",
            "mountain_id": 8,
            "favorable_months": ["寅"],
            "level": "全部",
        }
    )
    assert result["results"]
    assert all(item["month_zhi"] == "寅" for item in result["results"])
