"""설정 관리 모듈 - 소스 경로, 출력 경로 등을 JSON 파일로 저장/불러오기"""

import json
import os

# 프로그램 실행 폴더 기준으로 설정 파일 경로 결정
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SETTINGS_FILE = os.path.join(BASE_DIR, "data", "settings.json")
DATA_DIR = os.path.join(BASE_DIR, "data")
STAGING_DIR = os.path.join(DATA_DIR, "staging")
SELECTED_DIR = os.path.join(DATA_DIR, "selected")

# 기본 설정값
DEFAULT_SETTINGS = {
    "source_path": "",      # 소스 폴더 경로
    "output_path": "",      # 최종 출력 폴더 경로
}


class Settings:
    """설정을 관리하는 클래스"""

    def __init__(self):
        # 필요한 디렉토리 생성
        os.makedirs(DATA_DIR, exist_ok=True)
        os.makedirs(STAGING_DIR, exist_ok=True)
        os.makedirs(SELECTED_DIR, exist_ok=True)
        self._data = dict(DEFAULT_SETTINGS)
        self._load()

    def _load(self):
        """JSON 파일에서 설정을 불러옴"""
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                self._data.update(saved)
            except (json.JSONDecodeError, OSError):
                pass

    def save(self):
        """현재 설정을 JSON 파일에 저장"""
        os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(self._data, f, ensure_ascii=False, indent=2)

    def get(self, key, default=None):
        return self._data.get(key, default)

    def set(self, key, value):
        self._data[key] = value

    @property
    def source_path(self) -> str:
        return self._data.get("source_path", "")

    @source_path.setter
    def source_path(self, value: str):
        self._data["source_path"] = value

    @property
    def output_path(self) -> str:
        return self._data.get("output_path", "")

    @output_path.setter
    def output_path(self, value: str):
        self._data["output_path"] = value

    @property
    def staging_dir(self) -> str:
        return STAGING_DIR

    @property
    def selected_dir(self) -> str:
        return SELECTED_DIR
