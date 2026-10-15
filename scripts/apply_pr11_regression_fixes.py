from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    file_path = Path(path)
    text = file_path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"Expected exactly one match in {path}, found {count}")
    file_path.write_text(text.replace(old, new, 1), encoding="utf-8")


# 1) Slovak: do not export ischemic etiology outside ischemic stroke.
sk_path = "scripts/normalization/sk_registry.py"
sk_old = '''    out["stroke_etiology_cardioembolism"] = etiology_source.map(lambda value: True if value == "1" else (False if value else None))
    out["stroke_etiology_la_atherosclerosis"] = etiology_source.map(lambda value: True if value == "2" else (False if value else None))
    out["stroke_etiology_lacunar"] = etiology_source.map(lambda value: True if value == "3" else (False if value else None))
    out["stroke_etiology_cryptogenic_stroke"] = etiology_source.map(lambda value: True if value == "4" else (False if value else None))
    out["stroke_etiology_other"] = etiology_source.map(lambda value: True if value == "5" else (False if value else None))
    if "risk_atrial_fibrillation" in out:
'''
sk_new = '''    out["stroke_etiology_cardioembolism"] = etiology_source.map(lambda value: True if value == "1" else (False if value else None))
    out["stroke_etiology_la_atherosclerosis"] = etiology_source.map(lambda value: True if value == "2" else (False if value else None))
    out["stroke_etiology_lacunar"] = etiology_source.map(lambda value: True if value == "3" else (False if value else None))
    out["stroke_etiology_cryptogenic_stroke"] = etiology_source.map(lambda value: True if value == "4" else (False if value else None))
    out["stroke_etiology_other"] = etiology_source.map(lambda value: True if value == "5" else (False if value else None))

    # ETIO_ISCH_CMP is an ischemic-stroke classification. Some Slovak rows carry
    # a residual value even when the final diagnosis is TIA/non-ischemic. Keep
    # the source unchanged, but do not export that value into the canonical
    # contract where it would be interpreted as ischemic-stroke etiology.
    ischemic_etiology_columns = [
        "stroke_etiology_cardioembolism",
        "stroke_etiology_la_atherosclerosis",
        "stroke_etiology_lacunar",
        "stroke_etiology_cryptogenic_stroke",
        "stroke_etiology_other",
    ]
    non_ischemic_mask = out["stroke_type"].ne("1")
    out.loc[non_ischemic_mask, ischemic_etiology_columns] = None

    if "risk_atrial_fibrillation" in out:
'''
replace_once(sk_path, sk_old, sk_new)


# 2) Transformation: only create an IVT Location reference when a Location exists.
model_path = "scripts/data_modeling.py"
helper_anchor = '''def document_sections_for_procedure(
    procedure,
    *,
    include_not_done: bool = False,
) -> tuple[DischargeSection, ...]:
'''
helper_insert = '''def _add_thrombolysis_location(context: StrokeCaseContext, location_value: str | None) -> str | None:
    """Create and register the IVT Location only when the source provides it."""

    if location_value is None:
        return None

    location_ref = get_uuid()
    location = build_location(IvtApplicationDepartment.by_id(location_value))
    context.add_resource(location, full_url=location_ref)
    return location_ref


def document_sections_for_procedure(
    procedure,
    *,
    include_not_done: bool = False,
) -> tuple[DischargeSection, ...]:
'''
replace_once(model_path, helper_anchor, helper_insert)

ischemic_old = '''                thrombolysis_location_value = safe_get(raw, "ivt_application_department", required=False) # Check if thrombolysis location is present in raw data, not required
                thrombolysis_location_ref = get_uuid()

                if thrombolysis_location_value is not None:
                    logger.info("Thrombolysis location: %s", thrombolysis_location_value)
                    thrombolysis_location = build_location(IvtApplicationDepartment.by_id(thrombolysis_location_value)) # Build Location resource for thrombolysis location
                    #entries.append(BundleEntry(fullUrl=thrombolysis_location_ref, resource=thrombolysis_location, request=BundleEntryRequest(method="POST", url="Location")))
                    context.add_resource(thrombolysis_location,full_url=thrombolysis_location_ref,)
'''
ischemic_new = '''                thrombolysis_location_value = safe_get(raw, "ivt_application_department", required=False) # Check if thrombolysis location is present in raw data, not required
                thrombolysis_location_ref = _add_thrombolysis_location(context, thrombolysis_location_value)
                if thrombolysis_location_ref is not None:
                    logger.info("Thrombolysis location: %s", thrombolysis_location_value)
'''
replace_once(model_path, ischemic_old, ischemic_new)

mimic_old = '''                if thrombolysis_location_value is not None:
                    thrombolysis_location_ref = get_uuid()
                    thrombolysis_location = build_location(IvtApplicationDepartment.by_id(thrombolysis_location_value)) # Build Location resource for thrombolysis location
                    entries.append(BundleEntry(fullUrl=thrombolysis_location_ref, resource=thrombolysis_location, request=BundleEntryRequest(method="POST", url="Location")))
'''
mimic_new = '''                thrombolysis_location_ref = _add_thrombolysis_location(context, thrombolysis_location_value)
'''
replace_once(model_path, mimic_old, mimic_new)

print("Applied Slovak etiology and thrombolysis location fixes.")
