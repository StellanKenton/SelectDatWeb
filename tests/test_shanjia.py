from core.shanjia import calculate_days, get_options, get_year_sha


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
    assert len(first["hours"]) == 1
    assert first["lesson_id"].startswith(first["date"].replace("-", ""))
    assert first["time_ganzhi"] == first["hours"][0]["ganzhi"]


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
    assert meta["修方"]["default_month_relations"] == ["旺", "生", "耗", "泄", "克"]
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


def test_ganzhi_toolbar_filters_calendar_results():
    result = calculate_days(
        {
            "start_date": "2026-01-15",
            "end_date": "2027-02-15",
            "ganzhi_year": "丙午",
            "ganzhi_month": "丁酉",
            "ganzhi_day_filter": "全部",
            "use_type": "建造",
            "mountain_id": 1,
            "level": "全部",
        }
    )
    assert result["calendar_filter"] == {
        "ganzhi_year": "丙午",
        "ganzhi_month": "丁酉",
        "ganzhi_day_filter": "全部",
    }
    assert result["results"]
    assert all(item["year_ganzhi"] == "丙午" for item in result["results"])
    assert all(item["month_ganzhi"] == "丁酉" for item in result["results"])


def test_ganzhi_day_stem_filter():
    result = calculate_days(
        {
            "start_date": "2026-01-15",
            "end_date": "2027-02-15",
            "ganzhi_year": "丙午",
            "ganzhi_month": "丁酉",
            "ganzhi_day_filter": "甲",
            "use_type": "建造",
            "mountain_id": 1,
            "level": "全部",
            "sha_filters": [],
            "yiji_mode": "off",
        }
    )
    assert result["results"]
    assert all(item["day_ganzhi"].startswith("甲") for item in result["results"])


def test_reference_day_ji_filter_tables():
    options = get_options()
    assert options["day_ji_filters"]["协纪版"]["建造"] == ["竖造"]
    assert options["day_ji_filters"]["协纪版"]["修方动土"] == ["修造", "动土"]
    assert options["day_ji_filters"]["协纪版"]["附葬破土"] == ["破土", "修造"]
    assert options["day_ji_filters"]["协纪版"]["拆卸"] == ["拆卸", "动土"]
    assert options["day_ji_filters"]["通书版"]["拆卸"] == ["拆卸"]


def test_calculate_reports_reference_edition_and_filters():
    result = calculate_days(
        {
            "start_date": "2026-09-28",
            "end_date": "2026-09-28",
            "use_type": "建造",
            "mountain_id": 1,
            "edition": "协纪版",
            "level": "全部",
        }
    )
    assert result["edition"] == "协纪版"
    assert result["day_ji_filters"] == ["竖造"]


def test_reference_lesson_count_is_date_plus_hour():
    result = calculate_days(
        {
            "start_date": "2026-09-28",
            "end_date": "2026-09-28",
            "use_type": "建造",
            "mountain_id": 1,
            "edition": "协纪版",
            "level": "全部",
            "hours": [0, 2, 16],
        }
    )
    assert result["count"] == 3
    assert [item["hour"] for item in result["results"]] == [0, 2, 16]


def test_reference_shengwang_and_hao_are_independent_relations():
    shengwang = calculate_days(
        {
            "start_date": "2026-09-01",
            "end_date": "2026-10-08",
            "use_type": "建造",
            "mountain_id": 1,
            "edition": "协纪版",
            "level": "生旺",
            "hours": [0],
            "sha_filters": [],
            "yiji_mode": "off",
        }
    )
    assert shengwang["results"]
    assert all(item["relation"] in {"生", "旺"} for item in shengwang["results"])

    hao = calculate_days(
        {
            "start_date": "2026-09-01",
            "end_date": "2026-10-08",
            "use_type": "建造",
            "mountain_id": 1,
            "edition": "协纪版",
            "level": "耗",
            "hours": [0],
            "sha_filters": [],
            "yiji_mode": "off",
        }
    )
    assert hao["results"]
    assert all(item["relation"] == "耗" for item in hao["results"])


def test_reference_exact_month_relation_defaults():
    meta = get_options()["use_meta"]
    assert meta["修方兼竖造"]["default_month_relations"] == ["旺", "生"]
    assert meta["附葬"]["default_month_relations"] == ["旺", "生"]
    assert meta["进神"]["default_month_relations"] == ["旺", "生", "耗"]
    assert meta["修方"]["default_month_relations"] == ["旺", "生", "耗", "泄", "克"]


def test_reference_20260928_ren_mountain_hour_sansha_sample():
    result = calculate_days(
        {
            "start_date": "2026-09-28",
            "end_date": "2026-09-28",
            "use_type": "建造",
            "edition": "协纪版",
            "mountain_id": 1,
            "level": "全部",
            "hours": [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22],
            "sha_filters": [
                "月冲山", "日冲山", "时冲山", "月三杀", "日三杀", "时三杀",
                "月正阴府", "日正阴府", "时正阴府", "日正八煞", "时正八煞",
                "日星曜煞", "时星曜煞", "天星煞", "地曜煞", "日山方煞",
            ],
        }
    )
    assert result["count"] == 9
    assert [item["hour"] for item in result["results"]] == [0, 2, 6, 8, 10, 14, 16, 18, 22]
    assert any("年三煞在北方" in reason for reason in result["results"][0]["bad"])



def test_reference_default_sha_filters_are_exposed():
    options = get_options()
    assert options["default_sha_filters"]["建造"] == [
        "月冲山", "日冲山", "时冲山", "月三杀", "日三杀", "时三杀",
        "月正阴府", "日正阴府", "时正阴府", "五黄重叠", "二五交加",
        "日星曜煞", "时星曜煞", "天星煞", "地曜煞", "日流太岁",
        "日消灭煞", "日山方煞", "时山方煞", "月傍阴府", "时傍阴府",
    ]
    assert options["default_sha_filters"]["安门"] == ["日冲山", "时冲山", "日三杀", "时三杀"]
    assert options["default_sha_filters"]["拆卸"] == ["月冲山", "日冲山", "时冲山"]
    assert options["default_sha_filters"]["其它"] == []


def test_calculate_reports_reference_default_sha_filters():
    result = calculate_days(
        {
            "start_date": "2026-09-28",
            "end_date": "2026-09-28",
            "use_type": "建造",
            "mountain_id": 1,
            "level": "全部",
            "hours": [0],
        }
    )
    assert result["sha_filters"][-3:] == ["时山方煞", "月傍阴府", "时傍阴府"]


def test_year_sha_uses_reference_rows_and_marks_current_mountain():
    data = get_year_sha(2026, 1)
    current, next_year = data["cards"][:2]
    assert current["ganzhi"] == "丙午"
    assert current["reference_rows_verified"] is True
    assert current["san_sha_hits"] is True
    assert any(row["name"] == "伏兵（坐煞）" and row["applies"] for row in current["rows"])
    assert next_year["ganzhi"] == "丁未"
    assert next_year["san_sha_hits"] is False
    later = get_year_sha(2036, 1)["cards"][0]
    assert later["reference_rows_verified"] is False
    assert [row["name"] for row in later["rows"]] == ["太岁", "岁破（大耗）"]


def test_selected_sha_filters_change_result_set():
    payload = {
        "start_date": "2026-09-01", "end_date": "2026-10-08",
        "use_type": "建造", "mountain_id": 2, "level": "全部",
        "hours": [0], "yiji_mode": "off",
    }
    unrestricted = calculate_days({**payload, "sha_filters": []})
    filtered = calculate_days({**payload, "sha_filters": ["日冲山"]})
    assert unrestricted["count"] > filtered["count"]
    assert filtered["active_sha_filters"] == ["日冲山"]
    assert all(item["day_ganzhi"][1] != "午" for item in filtered["results"])


def test_year_and_ganzhi_input_do_not_count_same_life_twice():
    result = calculate_days({
        "start_date": "2026-09-28", "end_date": "2026-09-28",
        "use_type": "建造", "mountain_id": 1, "level": "全部",
        "hours": [0], "life_years": ["1996", "丙子"],
    })
    assert result["life_ganzhi"] == ["丙子"]


def test_reference_20260928_almanac_metadata():
    result = calculate_days(
        {
            "start_date": "2026-09-28",
            "end_date": "2026-09-28",
            "use_type": "建造",
            "edition": "协纪版",
            "mountain_id": 1,
            "level": "全部",
            "hours": [16],
        }
    )
    assert result["count"] == 1
    item = result["results"][0]
    assert item["zhi_xing"] == "成"
    assert item["xiu"] == "危"
    assert item["xiu_luck"] == "凶"
    assert item["jieqi"] == "秋分"
    assert [x["name"] for x in item["jieqi_times"]] == ["白露", "秋分", "寒露"]
    assert all(x["time"] for x in item["jieqi_times"])


def test_reference_yiji_mode_options_match_site():
    options = get_options()
    assert options["yiji_modes"] == [
        {"value": "all", "label": "显示协纪版"},
        {"value": "all1", "label": "显示潮汕版"},
        {"value": "all2", "label": "上协纪下潮汕一起显示"},
        {"value": "off", "label": "不显示"},
    ]
    assert options["day_ji_filters"]["潮汕版"]["拆卸"] == ["拆卸"]
    assert options["day_ji_filters"]["协纪+潮汕"]["拆卸"] == ["拆卸", "动土"]
    assert options["day_ji_filters"]["不显示"]["建造"] == []


def test_calculate_accepts_original_yiji_mode_values():
    chaoshan = calculate_days(
        {
            "start_date": "2026-09-28",
            "end_date": "2026-09-28",
            "use_type": "拆卸",
            "mountain_id": 1,
            "yiji_mode": "all1",
            "level": "全部",
            "hours": [0],
        }
    )
    assert chaoshan["yiji_mode"] == "all1"
    assert chaoshan["edition"] == "潮汕版"
    assert chaoshan["yiji_label"] == "显示潮汕版"
    assert chaoshan["day_ji_filters"] == ["拆卸"]

    off = calculate_days(
        {
            "start_date": "2026-09-28",
            "end_date": "2026-09-28",
            "use_type": "建造",
            "mountain_id": 1,
            "yiji_mode": "off",
            "level": "全部",
            "hours": [0],
        }
    )
    assert off["edition"] == "不显示"
    assert off["day_ji_filters"] == []


def test_official_xingyao_filters_water_mountain_day_and_hour():
    day_hit = calculate_days(
        {
            "start_date": "2026-09-12",
            "end_date": "2026-09-12",
            "use_type": "建造",
            "mountain_id": 1,
            "level": "全部",
            "hours": [0, 2, 6, 8, 10, 14, 16, 18, 22],
            "sha_filters": ["日星曜煞", "时星曜煞"],
            "yiji_mode": "off",
        }
    )
    assert day_hit["count"] == 0

    time_hit = calculate_days(
        {
            "start_date": "2026-09-16",
            "end_date": "2026-09-16",
            "use_type": "建造",
            "mountain_id": 1,
            "level": "全部",
            "hours": [14, 16],
            "sha_filters": ["日星曜煞", "时星曜煞"],
            "yiji_mode": "off",
        }
    )
    assert [(item["hour"], item["time_ganzhi"]) for item in time_hit["results"]] == [(16, "庚申")]

    time_hit_2 = calculate_days(
        {
            "start_date": "2026-10-04",
            "end_date": "2026-10-04",
            "use_type": "建造",
            "mountain_id": 1,
            "level": "全部",
            "hours": [2, 6],
            "sha_filters": ["日星曜煞", "时星曜煞"],
            "yiji_mode": "off",
        }
    )
    assert [(item["hour"], item["time_ganzhi"]) for item in time_hit_2["results"]] == [(6, "辛卯")]


def test_official_shanfang_filters_kangua_day():
    result = calculate_days(
        {
            "start_date": "2026-10-08",
            "end_date": "2026-10-08",
            "use_type": "建造",
            "mountain_id": 1,
            "level": "全部",
            "hours": [0, 2, 6],
        }
    )
    assert result["count"] == 0


def test_sha_filters_follow_use_type_default_table():
    # “其它”在原站默认不勾选山家神煞；壬山寅时不应被默认时三杀误删。
    result = calculate_days(
        {
            "start_date": "2026-09-28",
            "end_date": "2026-09-28",
            "use_type": "其它",
            "mountain_id": 1,
            "level": "全部",
            "hours": [4],
        }
    )
    assert result["count"] == 1
    assert result["results"][0]["hour"] == 4
