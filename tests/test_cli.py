import json

from PPT_Generator.cli import main


def test_cli_exits_on_missing_field(tmp_path, monkeypatch):
    input_path = tmp_path / "in.json"
    input_path.write_text(json.dumps({"topic": "T"}))
    output_path = tmp_path / "out.pptx"

    with monkeypatch.context() as m:
        m.setattr("sys.argv", ["ppt_generator", str(input_path), str(output_path)])
        try:
            main()
        except SystemExit as e:
            assert e.code == 1
