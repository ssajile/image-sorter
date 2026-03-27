"""프로젝트 이름 입력 다이얼로그"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit,
    QDialogButtonBox, QMessageBox,
)
from PySide6.QtCore import Qt


class ProjectDialog(QDialog):
    """새 프로젝트 이름을 입력받는 다이얼로그"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("프로젝트 이름 입력")
        self.setMinimumWidth(350)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        label = QLabel("새 프로젝트의 이름을 입력하세요:")
        layout.addWidget(label)

        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("예: 프로젝트_2024")
        layout.addWidget(self._name_edit)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _validate_and_accept(self):
        name = self._name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "입력 오류", "프로젝트 이름을 입력해주세요.")
            return
        # 파일 시스템에서 허용되지 않는 문자 검사
        invalid_chars = r'\/:*?"<>|'
        for ch in invalid_chars:
            if ch in name:
                QMessageBox.warning(
                    self, "입력 오류",
                    f"프로젝트 이름에 사용할 수 없는 문자가 포함되어 있습니다: {invalid_chars}"
                )
                return
        self.accept()

    def get_project_name(self) -> str:
        """입력된 프로젝트 이름 반환"""
        return self._name_edit.text().strip()
