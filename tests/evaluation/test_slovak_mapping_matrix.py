"""Systematic synthetic regression matrix for the 2024 NCZI source adapter.

Tests exercise implementation behavior, not independently adjudicated clinical
equivalence. Known source information losses are marked expectedFailure and
must NEVER be counted as semantic-preservation successes in the manuscript.
"""
import unittest
import pandas as pd
from scripts.normalization import sk_registry as sk


class SlovakMappingMatrix(unittest.TestCase):
    def row(self, **source):
        normalized, _ = sk.normalize_sk_registry_dataframe(pd.DataFrame([source]))
        self.assertEqual(sk.OUTPUT_COLUMNS, list(normalized.columns))
        return normalized.iloc[0]

    def test_inventory_71_source_keys_to_81_contract_fields(self):
        self.assertEqual(71, len(sk.COLUMN_MAPPING))
        self.assertEqual(81, len(sk.OUTPUT_COLUMNS))
        self.assertEqual(81, len(set(sk.OUTPUT_COLUMNS)))

    def test_every_declared_source_codebook_entry(self):
        # 13 codebooks, 48 enumerated source-value branches.
        mappings = (
            ("PACPOHLAVIE", "sex", sk.SEX_MAP),
            ("TRANSPORT_SPE", "arrival_mode_id", sk.ARRIVAL_MODE_MAP),
            ("JIS_ARO", "hospitalized_in", sk.HOSPITALIZED_IN_MAP),
            ("TRANSPORT_TYP", "inhospital_stroke", sk.INHOSPITAL_MAP),
            ("OA_FAJCENIE", "risk_smoker_last_10_years", sk.SMOKER_MAP),
            ("KKD_TYP_SPEC", "stroke_type", sk.STROKE_TYPE_MAP),
            ("UKON_SPOSOB", "discharge_destination", sk.DISCHARGE_DESTINATION_MAP),
            ("UKON_PREKLAD_VYBER", "discharge_facility_department", sk.DISCHARGE_FACILITY_DEPARTMENT_MAP),
            ("UKON_FIB_PREDSIEN", "atrial_fibrillation_or_flutter", sk.ATRIAL_FIBRILLATION_MAP),
            ("DYSFAGIA_VYS", "swallowing_screening_done", sk.SWALLOWING_DONE_MAP),
            ("DYSFAGIA", "swallowing_screening_timing", sk.SWALLOWING_TIMING_MAP),
            ("DYSFAGIA_SPEC", "swallowing_screening_type", sk.SWALLOWING_TYPE_MAP),
            ("TICI", "mtici_score", sk.MTICI_MAP),
        )
        self.assertEqual(48, sum(len(mapping) for _, _, mapping in mappings))
        for source, target, mapping in mappings:
            for code, expected in mapping.items():
                with self.subTest(source=source, code=code):
                    actual = self.row(**{source: code})[target]
                    if expected is None:
                        self.assertTrue(pd.isna(actual))
                    else:
                        self.assertEqual(expected, actual)

    def test_every_direct_boolean_source_code(self):
        # 24 direct source Boolean fields x 4 states = 96 branch assertions.
        derived = {"risk_tia", "risk_previous_ischemic_stroke",
                   "risk_previous_stroke", "risk_smoker", "thrombectomy"}
        fields = [(source, target) for source, target in sk.COLUMN_MAPPING.items()
                  if target in sk.BOOLEAN_COLUMNS and target not in derived]
        self.assertEqual(24, len(fields))
        for source, target in fields:
            for code, expected in (("1", True), ("2", False), ("3", False)):
                with self.subTest(source=source, code=code):
                    self.assertEqual(expected, self.row(**{source: code})[target])
            with self.subTest(source=source, code="missing"):
                self.assertTrue(pd.isna(self.row(**{source: None})[target]))
        # This documents current parsing, not NCZI clinical meaning of "3".

    def test_ivt_and_mt_local_external_planned_none(self):
        for code, performed, reason in (("1", True, None), ("2", False, "1"),
                                        ("3", False, None)):
            with self.subTest(NL_TROMBOLYZA=code):
                r = self.row(NL_TROMBOLYZA=code, KKD_TYP_SPEC="5")
                self.assertEqual(performed, r["thrombolysis"])
                self.assertEqual(reason, r["no_thrombolysis_reason"])
        for code, performed, reason in (("1", True, None), ("2", False, "1"),
                                        ("3", False, "8"), ("9", False, None)):
            with self.subTest(ENDO_VYKON=code):
                r = self.row(ENDO_VYKON=code, KKD_TYP_SPEC="5")
                self.assertEqual(performed, r["thrombectomy"])
                self.assertEqual(reason, r["no_thrombectomy_reason"])

    def test_prior_anticoagulants_all_supported_source_spellings(self):
        fields = ("before_onset_warfarin", "before_onset_doak",
                  "before_onset_other_anticoagulant", "before_onset_any_anticoagulant")
        for code, expected in (
            ("01", (True, False, False, True)),
            ("1", (True, False, False, True)),
            ("06", (False, True, False, True)),
            ("6", (False, True, False, True)),
            ("98", (False, False, True, True)),
            (None, (None, None, None, False)),
        ):
            with self.subTest(OA_ANTIKOAGULANCIA=code):
                actual = self.row(OA_ANTIKOAGULANCIA=code)
                for field, value in zip(fields, expected):
                    self.assertEqual(value, actual[field])

    def test_all_eight_discharge_medications_and_aggregate(self):
        source_fields = ("UKON_ASA", "UKON_CLOPIDOGREL", "UKON_WARFARIN",
                         "UKON_HEPARIN", "UKON_DOAK", "UKON_STATIN",
                         "UKON_NOOTROPIKA", "UKON_ANTIDEPRESIVA")
        for source in source_fields:
            with self.subTest(field=source):
                self.assertEqual(True, self.row(**{source: "1"})[sk.COLUMN_MAPPING[source]])
        r = self.row(UKON_ASA="1", UKON_DOAK="1")
        self.assertEqual(True, r["discharge_any_antiplatelet"])
        self.assertEqual(True, r["discharge_any_anticoagulant"])

    def test_ischemic_etiology_5_categories_contextual_suppression(self):
        targets = ("stroke_etiology_cardioembolism", "stroke_etiology_la_atherosclerosis",
                   "stroke_etiology_lacunar", "stroke_etiology_cryptogenic_stroke",
                   "stroke_etiology_other")
        for code, target in enumerate(targets, start=1):
            with self.subTest(ETIO_ISCH_CMP=code):
                self.assertEqual(True, self.row(KKD_TYP_SPEC="5", ETIO_ISCH_CMP=str(code))[target])
                self.assertTrue(pd.isna(self.row(KKD_TYP_SPEC="4", ETIO_ISCH_CMP=str(code))[target]))

    def test_all_bleeding_source_categories(self):
        for code in ("1", "2", "3", "4", "5", "6", "8"):
            with self.subTest(ETIO_HEM_CMP=code):
                r = self.row(ETIO_HEM_CMP=code)
                self.assertEqual(code == "2", r["bleeding_reason_aneurysm"])
                self.assertEqual(code in {"3", "5"}, r["bleeding_reason_malformation"])
                self.assertEqual(code in {"1", "4", "6", "8"}, r["bleeding_reason_other"])

    def test_single_modality_imaging_options(self):
        for source_type, angio, perfusion, expected in (
            ("1", "2", "2", "1"), ("1", "1", "2", "2"),
            ("1", "2", "1", "3"), ("3", "2", "2", "4"),
            ("3", "1", "2", "5"), ("3", "2", "1", "6"),
        ):
            with self.subTest(type=source_type, angio=angio, perfusion=perfusion):
                r = self.row(CT_MR_VYSETRENIE=source_type, CT_ANGIO=angio,
                             CT_PERFUZNE=perfusion)
                self.assertEqual(expected, r["imaging_type"])
                self.assertEqual("1", r["imaging_done"])

    def test_treatment_reason_precedence_and_temporal_metrics(self):
        r = self.row(NL_TROMBOLYZA="3", DNTL_MIMO_CAS="1", DNTL_DEFICIT="1",
                     ENDO_VYKON="9", NMT_MIMO_CAS="1", DMT_DEFICIT="1",
                     DMT_PREMORBIDITA="1")
        self.assertEqual("3", r["no_thrombolysis_reason"])
        self.assertEqual("5", r["no_thrombectomy_reason"])
        r = self.row(DATUM_LEKAR="05/21/2026 12:10",
                     NL_DATUM_TROMBOLYZA="05/21/2026 12:40",
                     NL_TROMBOLYZA="1", DATUM_ENDO_V="05/21/2026 13:10",
                     UKON_MRANKIN_2="exitus",
                     **{"UKON_MRANKIN_po 3 mesiacoch": "mRS 4"})
        self.assertEqual(30, r["door_to_needle"])
        self.assertEqual(60, r["door_to_groin"])
        self.assertEqual(6, r["discharge_mrs"])
        self.assertEqual(4, r["three_m_mrs"])
        remote = self.row(NL_TROMBOLYZA="2", DATUM_LEKAR="05/21/2026 13:10",
                          NL_DATUM_TROMBOLYZA="05/21/2026 12:40")
        self.assertTrue(pd.isna(remote["door_to_needle"]))
        self.assertEqual("2026-05-21 12:40:00", remote["bolus_timestamp"])

    def test_unmapped_categorical_codes_are_not_invented(self):
        for source, target in (("PACPOHLAVIE", "sex"),
                               ("TICI", "mtici_score"),
                               ("KKD_TYP_SPEC", "stroke_type")):
            with self.subTest(source=source):
                self.assertTrue(pd.isna(self.row(**{source: "BAD_CODE"})[target]))

    @unittest.expectedFailure
    def test_known_gap_ct_cta_and_perfusion_precedence(self):
        self.assertEqual("3", self.row(CT_MR_VYSETRENIE="1",
                                      CT_ANGIO="1", CT_PERFUZNE="1")["imaging_type"])

    @unittest.expectedFailure
    def test_known_gap_mr_mra_and_perfusion_precedence(self):
        self.assertEqual("6", self.row(CT_MR_VYSETRENIE="3",
                                      CT_ANGIO="1", CT_PERFUZNE="1")["imaging_type"])

    @unittest.expectedFailure
    def test_known_gap_external_imaging_not_preserved(self):
        self.assertEqual("3", self.row(CT_MR_VYSETRENIE="2")["imaging_done"])

    @unittest.expectedFailure
    def test_known_gap_explicit_no_imaging_not_preserved(self):
        self.assertEqual("2", self.row(CT_MR_VYSETRENIE="5")["imaging_done"])

    @unittest.expectedFailure
    def test_known_gap_unknown_aggregate_forced_false(self):
        self.assertIsNone(self.row(OA_ASPIRIN=None,
                                   OA_CLOPIDOGREL=None)["before_onset_any_antiplatelet"])

    @unittest.expectedFailure
    def test_known_gap_missing_onset_time_fabricates_midnight(self):
        self.assertIsNone(self.row(PACDATVYK="05/21/2026",
                                   PACCASVYK=None)["onset_timestamp"])

    @unittest.expectedFailure
    def test_known_gap_distinct_prior_tia_and_ischemic_stroke(self):
        tia = self.row(OA_TIA="1", OA_ISCHEMICKA_CMP="2")
        stroke = self.row(OA_TIA="2", OA_ISCHEMICKA_CMP="1")
        self.assertNotEqual(tia["risk_previous_ischemic_stroke"],
                            stroke["risk_previous_ischemic_stroke"])


if __name__ == "__main__":
    unittest.main()
