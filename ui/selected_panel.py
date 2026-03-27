"""선별소 패널 - 선별 완료된 이미지들을 표시하는 왼쪽 패널"""

import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QGridLayout, QFrame, QSizePolicy, QMessageBox,
    QTreeWidget, QTreeWidgetItem, QSplitter,
)
from PySide6.QtCore import Qt, Signal, QMimeData, QByteArray
from PySide6.QtGui import QPixmap, QDragEnterEvent, QDropEvent

from core.file_manager import list_images, list_subdirectories, move_file, delete_directory_contents

THUMBNAIL_SIZE = 120
GRID_COLUMNS = 3


class SelectedThumbnailWidget(QFrame):
    """선별소 내 단일 이미지 썸네일 위젯"""

    clicked = Signal(str)

    def __init__(self, image_path: str, parent=None):
        super().__init__(parent)
        self.image_path = image_path
        self._selected = False
        self.setFixedSize(THUMBNAIL_SIZE + 20, THUMBNAIL_SIZE + 30)
        self.setFrameShape(QFrame.Shape.Box)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)

        self._img_label = QLabel()
        self._img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._img_label.setFixedSize(THUMBNAIL_SIZE, THUMBNAIL_SIZE)
        self._load_thumbnail()
        layout.addWidget(self._img_label)

        filename = os.path.basename(self.image_path)
        name_label = QLabel(filename)
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_label.setWordWrap(True)
        name_label.setFixedHeight(20)
        name_label.setStyleSheet("font-size: 9px;")
        layout.addWidget(name_label)

    def _load_thumbnail(self):
        try:
            from PIL import Image
            from PIL.ImageQt import ImageQt
            img = Image.open(self.image_path)
            img.thumbnail((THUMBNAIL_SIZE, THUMBNAIL_SIZE), Image.Resampling.LANCZOS)
            qt_img = ImageQt(img.convert("RGBA"))
            pixmap = QPixmap.fromImage(qt_img)
            self._img_label.setPixmap(pixmap)
        except Exception:
            self._img_label.setText("?")
            self._img_label.setStyleSheet("background: #ccc; color: #666;")

    def set_selected(self, selected: bool):
        self._selected = selected
        if selected:
            self.setStyleSheet("QFrame { border: 2px solid #d4380d; background: #fff2e8; }")
        else:
            self.setStyleSheet("")

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.image_path)
        super().mousePressEvent(event)


class SelectedFolderTree(QTreeWidget):
    """선별소 폴더 트리"""

    folder_selected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHeaderLabel("폴더")
        self.setMinimumWidth(150)
        self.itemClicked.connect(self._on_item_clicked)

    def load_project(self, project_path: str):
        self.clear()
        if not project_path or not os.path.isdir(project_path):
            return
        root_item = QTreeWidgetItem(self, [os.path.basename(project_path)])
        root_item.setData(0, Qt.ItemDataRole.UserRole, project_path)
        self._add_children(root_item, project_path)
        root_item.setExpanded(True)
        self.setCurrentItem(root_item)

    def _add_children(self, parent_item, directory):
        for subdir in list_subdirectories(directory):
            child = QTreeWidgetItem(parent_item, [os.path.basename(subdir)])
            child.setData(0, Qt.ItemDataRole.UserRole, subdir)
            self._add_children(child, subdir)

    def _on_item_clicked(self, item, column):
        path = item.data(0, Qt.ItemDataRole.UserRole)
        if path:
            self.folder_selected.emit(path)


class SelectedPanel(QWidget):
    """선별소 패널 - 왼쪽에 표시되는 선별 완료 이미지 패널"""

    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self._settings = settings
        self._current_project = None
        self._current_folder = None
        self._selected_images = set()
        self._thumbnails = {}
        self.setAcceptDrops(True)
        self._build_ui()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(4, 4, 4, 4)

        header = QLabel("✅ 선별소")
        header.setStyleSheet("font-size: 16px; font-weight: bold; padding: 4px;")
        main_layout.addWidget(header)

        self._project_label = QLabel("프로젝트: (없음)")
        self._project_label.setStyleSheet("color: #555; padding: 2px 4px;")
        main_layout.addWidget(self._project_label)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # 폴더 트리
        self._folder_tree = SelectedFolderTree()
        self._folder_tree.folder_selected.connect(self._on_folder_selected)
        splitter.addWidget(self._folder_tree)

        # 이미지 그리드 영역
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)

        self._path_label = QLabel("")
        self._path_label.setStyleSheet("color: #777; font-size: 10px; padding: 2px;")
        right_layout.addWidget(self._path_label)

        # 드롭 영역 안내
        self._drop_hint = QLabel("← 이미지를 여기로 드래그하거나 버튼을 클릭하세요")
        self._drop_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._drop_hint.setStyleSheet(
            "color: #aaa; font-size: 12px; border: 2px dashed #ccc; padding: 8px;"
        )
        right_layout.addWidget(self._drop_hint)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self._grid_container = QWidget()
        self._grid_layout = QGridLayout(self._grid_container)
        self._grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        scroll.setWidget(self._grid_container)
        right_layout.addWidget(scroll)

        # 버튼
        btn_layout = QHBoxLayout()
        self._select_all_btn = QPushButton("전체 선택")
        self._select_all_btn.clicked.connect(self._select_all)
        self._remove_btn = QPushButton("← 대기소로 되돌리기")
        self._remove_btn.clicked.connect(self._remove_selected)
        btn_layout.addWidget(self._select_all_btn)
        btn_layout.addWidget(self._remove_btn)
        right_layout.addLayout(btn_layout)

        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)

        main_layout.addWidget(splitter)

    def load_project(self, project_name: str):
        self._current_project = project_name
        project_path = os.path.join(self._settings.selected_dir, project_name)
        self._project_label.setText(f"프로젝트: {project_name}")
        self._folder_tree.load_project(project_path)
        self._current_folder = project_path
        self._refresh_grid()

    def refresh(self):
        self._refresh_grid()
        if self._current_project and self._current_folder:
            project_path = os.path.join(self._settings.selected_dir, self._current_project)
            self._folder_tree.load_project(project_path)

    def get_current_folder(self) -> str | None:
        return self._current_folder

    def accept_image(self, image_path: str, staging_folder: str):
        """
        대기소에서 이미지를 받아 선별소로 이동.

        선별소의 폴더 구조는 staging 폴더 기준으로 대응.
        예: staging/project/folder/img.jpg → selected/project/folder/img.jpg
        """
        if not self._current_project:
            return
        staging_project = os.path.join(self._settings.staging_dir, self._current_project)
        selected_project = os.path.join(self._settings.selected_dir, self._current_project)

        # staging_project 기준 상대 경로 계산
        try:
            rel_path = os.path.relpath(image_path, staging_project)
        except ValueError:
            rel_path = os.path.basename(image_path)

        dst_path = os.path.join(selected_project, rel_path)
        move_file(image_path, dst_path)
        self._refresh_grid()
        self._folder_tree.load_project(selected_project)

    def _on_folder_selected(self, folder_path: str):
        self._current_folder = folder_path
        self._refresh_grid()

    def _refresh_grid(self):
        while self._grid_layout.count():
            item = self._grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._thumbnails.clear()
        self._selected_images.clear()

        has_images = False
        if self._current_folder and os.path.isdir(self._current_folder):
            self._path_label.setText(self._current_folder)
            images = list_images(self._current_folder)
            for idx, img_path in enumerate(images):
                thumb = SelectedThumbnailWidget(img_path)
                thumb.clicked.connect(self._on_thumbnail_clicked)
                row, col = divmod(idx, GRID_COLUMNS)
                self._grid_layout.addWidget(thumb, row, col)
                self._thumbnails[img_path] = thumb
                has_images = True
        else:
            self._path_label.setText("")

        self._drop_hint.setVisible(not has_images)

    def _on_thumbnail_clicked(self, image_path: str):
        if image_path in self._selected_images:
            self._selected_images.discard(image_path)
            self._thumbnails[image_path].set_selected(False)
        else:
            self._selected_images.add(image_path)
            self._thumbnails[image_path].set_selected(True)

    def _select_all(self):
        for path, thumb in self._thumbnails.items():
            self._selected_images.add(path)
            thumb.set_selected(True)

    def _remove_selected(self):
        """선택된 이미지를 다시 대기소로 되돌리기"""
        if not self._selected_images or not self._current_project:
            QMessageBox.information(self, "알림", "되돌릴 이미지를 선택해주세요.")
            return
        selected_project = os.path.join(self._settings.selected_dir, self._current_project)
        staging_project = os.path.join(self._settings.staging_dir, self._current_project)
        for img_path in list(self._selected_images):
            try:
                rel_path = os.path.relpath(img_path, selected_project)
            except ValueError:
                rel_path = os.path.basename(img_path)
            dst_path = os.path.join(staging_project, rel_path)
            move_file(img_path, dst_path)
        self._refresh_grid()

    # 드래그&드롭 수신
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasFormat("application/x-image-path"):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        mime = event.mimeData()
        if mime.hasFormat("application/x-image-path"):
            image_path = bytes(mime.data("application/x-image-path")).decode("utf-8")
            staging_folder = os.path.dirname(image_path)
            self.accept_image(image_path, staging_folder)
            event.acceptProposedAction()
