"""설정 다이얼로그 - 소스 폴더 경로 및 출력 폴더 경로 설정"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFileDialog, QDialogButtonBox, QFormLayout,
)


class SettingsDialog(QDialog):
    """소스 폴더 및 출력 폴더 경로를 설정하는 다이얼로그"""

    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self._settings = settings
        self.setWindowTitle("설정")
        self.setMinimumWidth(500)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        form = QFormLayout()

        # 소스 폴더 경로
        self._source_edit = QLineEdit(self._settings.source_path)
        source_browse = QPushButton("찾아보기")
        source_browse.clicked.connect(self._browse_source)
        source_row = QHBoxLayout()
        source_row.addWidget(self._source_edit)
        source_row.addWidget(source_browse)
        form.addRow("소스 폴더 경로:", source_row)

        # 출력 폴더 경로
        self._output_edit = QLineEdit(self._settings.output_path)
        output_browse = QPushButton("찾아보기")
        output_browse.clicked.connect(self._browse_output)
        output_row = QHBoxLayout()
        output_row.addWidget(self._output_edit)
        output_row.addWidget(output_browse)
        form.addRow("출력 폴더 경로:", output_row)

        layout.addLayout(form)

        # 확인/취소 버튼
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _browse_source(self):
        path = QFileDialog.getExistingDirectory(self, "소스 폴더 선택", self._source_edit.text())
        if path:
            self._source_edit.setText(path)

    def _browse_output(self):
        path = QFileDialog.getExistingDirectory(self, "출력 폴더 선택", self._output_edit.text())
        if path:
            self._output_edit.setText(path)

    def _accept(self):
        self._settings.source_path = self._source_edit.text().strip()
        self._settings.output_path = self._output_edit.text().strip()
        self._settings.save()
        self.accept()
