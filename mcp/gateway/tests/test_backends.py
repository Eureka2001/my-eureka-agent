"""backends.py：.env 解析与前缀注入。"""

from __future__ import annotations

import os
from pathlib import Path

from backends import _std, env_for, parse_env_file


def test_parse_env_file(tmp_path: Path) -> None:
    env = tmp_path / ".env"
    env.write_text(
        "# 注释\nA=1\n  B = 空格  \nC='单引号'\nD=\"双引号\"\nE=\n没有等号的行\n",
        encoding="utf-8",
    )
    assert parse_env_file(env) == {
        "A": "1",
        "B": "空格",
        "C": "单引号",
        "D": "双引号",
        "E": "",
    }
    assert parse_env_file(tmp_path / "absent.env") == {}


def test_env_for_filters_by_prefix(monkeypatch, tmp_path: Path) -> None:
    # 宿主机用户级环境可能已设置 HABITICA_*（会触发"不覆盖"分支），先摘掉
    for key in ("HABITICA_USER_ID", "HABITICA_API_TOKEN"):
        monkeypatch.delenv(key, raising=False)
    env = tmp_path / ".env"
    env.write_text(
        "HABITICA_USER_ID=uid\nHABITICA_API_TOKEN=tok\nOTHER=x\n",
        encoding="utf-8",
    )
    spec = _std("habitica", env_prefixes=("HABITICA_",))
    assert env_for(spec, env_file=env) == {
        "HABITICA_USER_ID": "uid",
        "HABITICA_API_TOKEN": "tok",
    }


def test_env_for_does_not_override_existing(monkeypatch, tmp_path: Path) -> None:
    env = tmp_path / ".env"
    env.write_text("HABITICA_USER_ID=from-file\n", encoding="utf-8")
    monkeypatch.setenv("HABITICA_USER_ID", "from-env")
    spec = _std("habitica", env_prefixes=("HABITICA_",))
    assert env_for(spec, env_file=env) == {}
    assert os.environ["HABITICA_USER_ID"] == "from-env"


def test_env_for_no_prefix_means_no_injection() -> None:
    assert env_for(_std("fetch")) == {}
