import importlib.util
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "minecraft" / "voyager.py"
spec = importlib.util.spec_from_file_location("voyager_module", MODULE_PATH)
voyager_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(voyager_module)

Skill = voyager_module.Skill
SkillLibrary = voyager_module.SkillLibrary


def test_json_file_path_storage(tmp_path):
    library_path = tmp_path / "skills.json"
    lib = SkillLibrary(str(library_path))

    lib.add(Skill(name="mine_stone", description="挖石头", code="attack"))

    assert library_path.exists()
    loaded = SkillLibrary(str(library_path))
    assert loaded.get("mine_stone") is not None


def test_find_similar_uses_tags_and_description(tmp_path):
    lib = SkillLibrary(str(tmp_path / "data"))
    lib.add(
        Skill(
            name="gather_wood",
            description="收集木头和木板",
            code="mine oak_log",
            tags=["木头", "log", "resource"],
            successes=8,
            attempts=10,
            success_rate=0.8,
        )
    )

    matched = lib.find_similar("去收集一些木头资源")
    assert matched is not None
    assert matched.name == "gather_wood"
