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


def test_reference_auto_favorable_months_are_per_mountain():
    options = get_options()
    by_id = {m["id"]: m for m in options["mountains"]}
    assert by_id[1]["favorable_months"] == ["申", "酉", "亥", "子"]
    assert by_id[4]["favorable_months"] == ["巳", "辰", "丑"]
    assert by_id[5]["favorable_months"] == ["巳", "午", "辰", "未", "戌", "丑"]
    assert by_id[18]["favorable_months"] == ["申", "酉", "辰", "戌", "丑"]
    assert by_id[22]["favorable_months"] == ["巳", "午", "戌"]


def test_reference_dagua_table():
    options = get_options()
    by_id = {m["id"]: m for m in options["mountains"]}
    assert by_id[1]["dagua"] == [
        {"name": "风地观", "value": "2;2"},
        {"name": "水地比", "value": "7;7"},
        {"name": "山地剥", "value": "6;6"},
    ]
    assert {"name": "乾为天", "value": "9;1"} in by_id[14]["dagua"]
