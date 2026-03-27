"""메인 윈도우 - 1:1 비율의 선별소(왼쪽) / 대기소(오른쪽) 분할 화면"""

import os
import shutil
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QLabel, QSplitter, QMessageBox,
    QComboBox, QToolBar, QStatusBar,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction

from config.settings import Settings
from core.project_manager import ProjectManager
from core.file_manager import move_file, delete_directory_contents
from ui.settings_dialog import SettingsDialog
from ui.project_dialog import ProjectDialog
from ui.staging_panel import StagingPanel
from ui.selected_panel import SelectedPanel


class MainWindow(QMainWindow):
    """이미지 분류기 메인 윈도우"""

    def __init__(self):
        super().__init__()
        self._settings = Settings()
        self._project_manager = ProjectManager(self._settings)
        self._current_project = None
        self.setWindowTitle("이미지 분류기")
        self.setMinimumSize(1200, 700)
        self._build_ui()
        self._load_last_project()

    def _build_ui(self):
        # 메뉴 바
        menubar = self.menuBar()
        options_menu = menubar.addMenu("옵션")
        settings_action = QAction("설정", self)
        settings_action.triggered.connect(self._open_settings)
        options_menu.addAction(settings_action)

        # 툴바
        toolbar = QToolBar("메인 툴바")
        self.addToolBar(toolbar)

        # 가져오기 버튼
        self._import_btn = QPushButton("📥 가져오기")
        self._import_btn.setToolTip("소스 폴더에서 이미지를 대기소로 가져옵니다")
        self._import_btn.clicked.connect(self._import_images)
        toolbar.addWidget(self._import_btn)

        toolbar.addSeparator()

        # 프로젝트 선택 콤보박스
        toolbar.addWidget(QLabel("  프로젝트: "))
        self._project_combo = QComboBox()
        self._project_combo.setMinimumWidth(200)
        self._project_combo.currentTextChanged.connect(self._on_project_changed)
        toolbar.addWidget(self._project_combo)

        refresh_btn = QPushButton("🔄 새로고침")
        refresh_btn.clicked.connect(self._refresh_project_list)
        toolbar.addWidget(refresh_btn)

        toolbar.addSeparator()

        # 작업완료 버튼
        self._complete_btn = QPushButton("✅ 작업완료")
        self._complete_btn.setToolTip("현재 폴더의 작업을 완료합니다")
        self._complete_btn.setStyleSheet(
            "QPushButton { background: #52c41a; color: white; font-weight: bold; padding: 4px 12px; }"
        )
        self._complete_btn.clicked.connect(self._complete_work)
        toolbar.addWidget(self._complete_btn)

        # 중앙 위젯 - 1:1 분할
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(4, 4, 4, 4)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # 선별소 패널 (왼쪽)
        self._selected_panel = SelectedPanel(self._settings)
        splitter.addWidget(self._selected_panel)

        # 대기소 패널 (오른쪽)
        self._staging_panel = StagingPanel(self._settings)
        self._staging_panel.image_moved_to_selected.connect(self._on_image_moved_to_selected)
        splitter.addWidget(self._staging_panel)

        # 1:1 비율 설정
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([600, 600])

        layout.addWidget(splitter)

        # 상태 바
        self.statusBar().showMessage("준비")

    def _load_last_project(self):
        """시작 시 프로젝트 목록 로드"""
        self._refresh_project_list()

    def _refresh_project_list(self):
        """프로젝트 콤보박스를 최신 목록으로 갱신"""
        projects = self._project_manager.list_projects()
        current = self._project_combo.currentText()
        self._project_combo.blockSignals(True)
        self._project_combo.clear()
        self._project_combo.addItems(projects)
        # 이전 선택 복원
        if current in projects:
            self._project_combo.setCurrentText(current)
        elif projects:
            self._project_combo.setCurrentIndex(0)
        self._project_combo.blockSignals(False)

        if projects:
            self._on_project_changed(self._project_combo.currentText())

    def _on_project_changed(self, project_name: str):
        """프로젝트 선택 변경 시 패널 갱신"""
        if not project_name:
            return
        self._current_project = project_name
        self._staging_panel.load_project(project_name)
        self._selected_panel.load_project(project_name)
        self.statusBar().showMessage(f"프로젝트 '{project_name}' 로드됨")

    def _open_settings(self):
        """설정 다이얼로그 열기"""
        dialog = SettingsDialog(self._settings, self)
        dialog.exec()

    def _import_images(self):
        """소스 폴더에서 이미지를 대기소로 가져오기"""
        # 소스 경로 확인
        source_path = self._settings.source_path
        if not source_path or not os.path.isdir(source_path):
            QMessageBox.warning(
                self, "경고",
                "유효한 소스 폴더 경로가 설정되지 않았습니다.\n옵션 > 설정에서 소스 폴더를 지정해주세요."
            )
            return

        if not os.listdir(source_path):
            QMessageBox.information(self, "알림", "소스 폴더가 비어있습니다.")
            return

        # 프로젝트 이름 입력 다이얼로그
        dialog = ProjectDialog(self)
        if dialog.exec() != ProjectDialog.DialogCode.Accepted:
            return

        project_name = dialog.get_project_name()
        try:
            staging_path = self._project_manager.create_project(project_name, source_path)
            self._refresh_project_list()
            self._project_combo.setCurrentText(project_name)
            QMessageBox.information(
                self, "완료",
                f"프로젝트 '{project_name}'이 생성되었습니다.\n"
                f"이미지가 대기소로 이동되었습니다."
            )
            self.statusBar().showMessage(f"프로젝트 '{project_name}' 가져오기 완료")
        except FileExistsError as e:
            QMessageBox.warning(self, "오류", str(e))
        except Exception as e:
            QMessageBox.critical(self, "오류", f"가져오기 중 오류가 발생했습니다:\n{e}")

    def _on_image_moved_to_selected(self, image_path: str, staging_folder: str):
        """대기소 패널에서 이미지 이동 요청 시 처리"""
        self._selected_panel.accept_image(image_path, staging_folder)
        self._staging_panel.refresh()
        self.statusBar().showMessage(f"이미지 이동: {os.path.basename(image_path)}")

    def _complete_work(self):
        """
        작업완료:
        1. 선별소의 현재 폴더 파일들을 출력 폴더로 이동
        2. 대기소의 현재 폴더 잔여 파일만 삭제
        """
        if not self._current_project:
            QMessageBox.warning(self, "경고", "활성화된 프로젝트가 없습니다.")
            return

        staging_folder = self._staging_panel.get_current_folder()
        selected_folder = self._selected_panel.get_current_folder()

        if not staging_folder or not selected_folder:
            QMessageBox.warning(self, "경고", "작업할 폴더가 없습니다.")
            return

        # 출력 경로 확인
        output_path = self._settings.output_path
        if not output_path:
            QMessageBox.warning(
                self, "경고",
                "출력 폴더 경로가 설정되지 않았습니다.\n옵션 > 설정에서 출력 폴더를 지정해주세요."
            )
            return

        # 확인 메시지
        reply = QMessageBox.question(
            self, "작업완료 확인",
            f"현재 폴더의 작업을 완료합니다.\n\n"
            f"• 선별소의 파일: 출력 폴더로 이동\n"
            f"• 대기소의 잔여 파일: 삭제\n\n"
            f"계속하시겠습니까?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            # 선별소 현재 폴더의 파일들을 출력 폴더로 이동
            selected_project = os.path.join(self._settings.selected_dir, self._current_project)
            self._move_selected_to_output(selected_folder, selected_project, output_path)

            # 대기소 현재 폴더의 잔여 파일 삭제 (폴더는 유지)
            delete_directory_contents(staging_folder)

            # 화면 갱신
            self._staging_panel.refresh()
            self._selected_panel.refresh()

            QMessageBox.information(self, "완료", "작업이 완료되었습니다.")
            self.statusBar().showMessage("작업완료")
        except Exception as e:
            QMessageBox.critical(self, "오류", f"작업완료 중 오류가 발생했습니다:\n{e}")

    def _move_selected_to_output(self, selected_folder: str, selected_project: str, output_path: str):
        """선별소 폴더의 파일들을 출력 경로로 이동 (상대 경로 구조 유지)"""
        if not os.path.isdir(selected_folder):
            return

        try:
            rel_folder = os.path.relpath(selected_folder, selected_project)
        except ValueError:
            rel_folder = ""

        output_folder = os.path.join(output_path, rel_folder) if rel_folder != "." else output_path

        for item in os.listdir(selected_folder):
            item_path = os.path.join(selected_folder, item)
            if os.path.isfile(item_path):
                dst = os.path.join(output_folder, item)
                move_file(item_path, dst)
