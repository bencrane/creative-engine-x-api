from pathlib import Path

import yaml

from src.specs.models import FormatSpec


class SpecLoader:
    @staticmethod
    def load_all(specs_dir: Path | None = None) -> dict[tuple[str, str], FormatSpec]:
        if specs_dir is None:
            specs_dir = Path(__file__).parent

        specs: dict[tuple[str, str], FormatSpec] = {}
        for yaml_file in sorted(specs_dir.glob("*.yaml")):
            raw = yaml.safe_load(yaml_file.read_text())
            spec = FormatSpec(**raw)
            key = (spec.artifact_type, spec.surface)

            if key in specs:
                # Merge: two generic specs map to same key — merge subtypes
                existing = specs[key]
                if spec.subtypes and existing.subtypes:
                    existing.subtypes.update(spec.subtypes)
                elif spec.subtypes:
                    existing.subtypes = spec.subtypes
            else:
                specs[key] = spec

        return specs
