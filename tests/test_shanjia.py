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



def test_reference_auto_favorable_month_table():
    options = get_options()
    mountains = {item["id"]: item for item in options["mountains"]}
    assert mountains[1]["auto_favorable_months"] == ["申", "酉", "亥", "子"]
    assert mountains[4]["auto_favorable_months"] == ["巳", "辰", "丑"]
    assert mountains[5]["auto_favorable_months"] == ["巳", "午", "辰", "未", "戌", "丑"]
    assert mountains[23]["auto_favorable_months"] == ["申", "酉", "辰", "戌", "丑"]


def test_reference_dagua_and_facing_labels():
    mountains = {item["id"]: item for item in get_options()["mountains"]}
    assert mountains[1]["facing_label"] == "正北偏左【壬向】水"
    assert mountains[3]["facing_label"] == "正北偏右【癸向】水"
    assert mountains[1]["dagua"] == [
        {"label": "风地观", "value": "2;2"},
        {"label": "水地比", "value": "7;7"},
        {"label": "山地剥", "value": "6;6"},
    ]
    assert mountains[14]["dagua"][1] == {"label": "乾为天", "value": "9;1"}


def test_reference_use_type_semantics():
    options = get_options()
    meta = options["use_meta"]
    assert meta["安门"]["mountain_mode"] == "facing"
    assert meta["安门"]["mountain_title"] == "第二步【选择门向】"
    assert meta["旧坟立碑"]["show_repair"] is True
    assert meta["旧坟立碑"]["show_deceased"] is True
    assert meta["旧坟立碑"]["auto_repair"] == "seat_facing"
    assert meta["作灶"]["life_name"] == "馈主年命"
    assert meta["其它"]["show_mountain"] is False
    assert meta["其它"]["show_year_sha"] is False


def test_reference_repair_direction_table():
    options = get_options()
    assert options["repair_positions"]["坎宫"] == ["壬", "子", "癸"]
    assert options["repair_positions"]["巽宫"] == ["辰", "巽", "巳"]
    assert options["repair_positions"]["中宫"] == []


def test_calculate_accepts_reference_extra_inputs():
    result = calculate_days(
        {
            "start_date": "2026-09-28",
            "end_date": "2026-09-30",
            "use_type": "旧坟立碑",
            "mountain_id": 1,
            "life_years": "1988",
            "deceased_years": "1950",
            "repair_positions": ["坎宫", "壬", "离宫", "丙"],
            "dagua": "风地观",
            "dagua_value": "2;2",
            "level": "全部",
        }
    )
    assert result["deceased_ganzhi"]
    assert result["repair_positions"] == ["坎宫", "壬", "离宫", "丙"]
    assert result["dagua"] == "风地观"
    assert result["dagua_value"] == "2;2"



def test_reference_month_relation_mode():
    meta = get_options()["use_meta"]
    assert meta["修方"]["month_mode"] == "relation"
    assert meta["修方"]["default_month_relations"] == ["旺", "生", "耗"]
    assert meta["建造"]["month_mode"] == "mountain"


def test_month_relation_filter_is_applied():
    result = calculate_days(
        {
            "start_date": "2026-01-01",
            "end_date": "2026-03-31",
            "use_type": "修方",
            "mountain_id": 8,
            "month_relations": ["旺"],
            "level": "全部",
        }
    )
    assert result["month_relations"] == ["旺"]
    assert result["results"]
    assert all("为旺" in "；".join(item["good"]) for item in result["results"])



def test_reference_solar_calendar_query_month_and_range():
    month = calculate_days(
        {
            "calendar_query": {"mode": "公历", "year": 2026, "month": 9, "day": "全部", "range": "范围"},
            "use_type": "建造",
            "mountain_id": 1,
            "level": "全部",
        }
    )
    assert month["calendar_query"]["mode"] == "公历"
    assert len(month["results"]) == 30
    assert month["results"][0]["date"].startswith("2026-09-")

    ranged = calculate_days(
        {
            "calendar_query": {"mode": "公历", "year": 2026, "month": 9, "day": "28", "range": "后10"},
            "use_type": "建造",
            "mountain_id": 1,
            "level": "全部",
        }
    )
    assert len(ranged["results"]) == 11
    assert {item["date"] for item in ranged["results"]} == {
        f"2026-09-{day:02d}" for day in range(28, 31)
    } | {
        f"2026-10-{day:02d}" for day in range(1, 9)
    }


def test_reference_ganzhi_calendar_query():
    result = calculate_days(
        {
            "calendar_query": {
                "mode": "干支",
                "year": 2026,
                "year_ganzhi": "丙午",
                "month_ganzhi": "丁酉",
                "day": "全部",
            },
            "use_type": "建造",
            "mountain_id": 1,
            "level": "全部",
        }
    )
    assert result["results"]
    assert all(item["year_ganzhi"] == "丙午" for item in result["results"])
    assert all(item["month_ganzhi"] == "丁酉" for item in result["results"])


def test_reference_lunar_calendar_query():
    result = calculate_days(
        {
            "calendar_query": {
                "mode": "农历",
                "year": 2026,
                "month": "八",
                "day": "全部",
                "range": "范围",
            },
            "use_type": "建造",
            "mountain_id": 1,
            "level": "全部",
        }
    )
    assert len(result["results"]) >= 29
    assert all("八月" in item["lunar"] for item in result["results"])
