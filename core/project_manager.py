"""프로젝트 생성 및 관리 모듈"""

import os
from core.file_manager import move_directory_contents


class ProjectManager:
    """프로젝트 단위로 이미지 작업을 관리하는 클래스"""

    def __init__(self, settings):
        self._settings = settings

    def create_project(self, project_name: str, source_path: str) -> str:
        """
        새 프로젝트를 생성하고 소스 폴더 내용을 대기소로 이동.

        Args:
            project_name: 프로젝트 이름 (폴더명으로 사용)
            source_path: 소스 폴더 경로

        Returns:
            생성된 대기소 프로젝트 경로
        """
        # 프로젝트명으로 대기소/선별소 폴더 생성
        staging_project = os.path.join(self._settings.staging_dir, project_name)
        selected_project = os.path.join(self._settings.selected_dir, project_name)

        if os.path.exists(staging_project):
            raise FileExistsError(f"프로젝트 '{project_name}'이 이미 존재합니다.")

        os.makedirs(staging_project, exist_ok=True)
        os.makedirs(selected_project, exist_ok=True)

        # 소스 폴더 내용 전체를 대기소 프로젝트 폴더로 이동 (잘라내기)
        move_directory_contents(source_path, staging_project)

        return staging_project

    def get_project_staging_path(self, project_name: str) -> str:
        return os.path.join(self._settings.staging_dir, project_name)

    def get_project_selected_path(self, project_name: str) -> str:
        return os.path.join(self._settings.selected_dir, project_name)

    def list_projects(self) -> list[str]:
        """대기소에 존재하는 프로젝트 목록 반환"""
        staging_dir = self._settings.staging_dir
        if not os.path.isdir(staging_dir):
            return []
        return sorted(
            item for item in os.listdir(staging_dir)
            if os.path.isdir(os.path.join(staging_dir, item))
        )
