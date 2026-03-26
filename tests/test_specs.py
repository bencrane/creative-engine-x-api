from pathlib import Path

import pytest

from src.specs.loader import SpecLoader
from src.specs.models import FormatSpec


SPECS_DIR = Path(__file__).parent.parent / "src" / "specs"


class TestSpecLoader:
    def test_load_all_returns_dict(self):
        specs = SpecLoader.load_all(SPECS_DIR)
        assert isinstance(specs, dict)
        assert len(specs) > 0

    def test_all_specs_are_format_spec(self):
        specs = SpecLoader.load_all(SPECS_DIR)
        for key, spec in specs.items():
            assert isinstance(spec, FormatSpec)
            assert isinstance(key, tuple)
            assert len(key) == 2

    def test_loads_12_unique_keys(self):
        """13 YAML files but two generic specs merge into one key."""
        specs = SpecLoader.load_all(SPECS_DIR)
        assert len(specs) == 12

    def test_structured_text_generic_merges_two_specs(self):
        """Two generic specs (image_brief, video_script) merge into one key."""
        specs = SpecLoader.load_all(SPECS_DIR)
        st_generic = specs.get(("structured_text", "generic"))
        assert st_generic is not None

    def test_expected_keys_present(self):
        specs = SpecLoader.load_all(SPECS_DIR)
        # Using actual surface values from spec YAML files
        expected = [
            ("audio", "voice_channel"),
            ("document_slides", "linkedin"),
            ("html_page", "web"),
            ("pdf", "generic"),
            ("physical_mail", "direct_mail"),
            ("structured_text", "generic"),
            ("structured_text", "google_rsa"),
            ("structured_text", "linkedin"),
            ("structured_text", "meta"),
            ("video", "generic"),
            ("video", "meta_ads"),
            ("video", "tiktok_ads"),
        ]
        for key in expected:
            assert key in specs, f"Missing spec: {key}"

    def test_each_spec_has_required_fields(self):
        specs = SpecLoader.load_all(SPECS_DIR)
        for key, spec in specs.items():
            assert spec.spec_id, f"{key} missing spec_id"
            assert spec.artifact_type, f"{key} missing artifact_type"
            assert spec.surface, f"{key} missing surface"
            assert spec.version, f"{key} missing version"

    def test_delivery_mode_is_sync_or_async(self):
        specs = SpecLoader.load_all(SPECS_DIR)
        for key, spec in specs.items():
            if spec.delivery:
                assert spec.delivery.mode in ("sync", "async"), (
                    f"{key} has invalid delivery mode: {spec.delivery.mode}"
                )

    def test_video_specs_are_async(self):
        specs = SpecLoader.load_all(SPECS_DIR)
        for key, spec in specs.items():
            if spec.artifact_type == "video" and spec.delivery:
                assert spec.delivery.mode == "async", f"{key} should be async"

    def test_audio_spec_is_async(self):
        specs = SpecLoader.load_all(SPECS_DIR)
        audio = specs.get(("audio", "voice_channel"))
        assert audio is not None
        assert audio.delivery.mode == "async"

    def test_structured_text_specs_are_sync(self):
        specs = SpecLoader.load_all(SPECS_DIR)
        for key, spec in specs.items():
            if spec.artifact_type == "structured_text" and spec.delivery:
                assert spec.delivery.mode == "sync", f"{key} should be sync"
