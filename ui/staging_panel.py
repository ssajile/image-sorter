"""대기소 패널 - 분류 대기 중인 이미지들을 표시하는 오른쪽 패널"""

import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QGridLayout, QFrame, QSizePolicy, QMessageBox,
    QTreeWidget, QTreeWidgetItem, QSplitter,
)
from PySide6.QtCore import Qt, Signal, QSize, QMimeData, QByteArray
from PySide6.QtGui import QPixmap, QDrag, QColor

from core.file_manager import list_images, list_subdirectories, is_image

THUMBNAIL_SIZE = 120
GRID_COLUMNS = 3


class ThumbnailWidget(QFrame):
    """단일 이미지 썸네일 위젯 (드래그 지원)"""

    clicked = Signal(str)  # 파일 경로 전달

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

        # 썸네일 이미지
        self._img_label = QLabel()
        self._img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._img_label.setFixedSize(THUMBNAIL_SIZE, THUMBNAIL_SIZE)
        self._load_thumbnail()
        layout.addWidget(self._img_label)

        # 파일명 표시
        filename = os.path.basename(self.image_path)
        name_label = QLabel(filename)
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_label.setWordWrap(True)
        name_label.setFixedHeight(20)
        name_label.setStyleSheet("font-size: 9px;")
        layout.addWidget(name_label)

    def _load_thumbnail(self):
        """Pillow로 썸네일 로드"""
        try:
            from PIL import Image
            from PIL.ImageQt import ImageQt
            img = Image.open(self.image_path)
            img.thumbnail((THUMBNAIL_SIZE, THUMBNAIL_SIZE), Image.Resampling.LANCZOS)
            qt_img = ImageQt(img.convert("RGBA"))
            pixmap = QPixmap.fromImage(qt_img)
            self._img_label.setPixmap(pixmap)
        except Exception:
            # 로드 실패 시 회색 박스
            self._img_label.setText("?")
            self._img_label.setStyleSheet("background: #ccc; color: #666;")

    def set_selected(self, selected: bool):
        self._selected = selected
        if selected:
            self.setStyleSheet("QFrame { border: 2px solid #0078d4; background: #e8f4ff; }")
        else:
            self.setStyleSheet("")

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start_pos = event.position().toPoint()
            self.clicked.emit(self.image_path)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            return
        drag = QDrag(self)
        mime = QMimeData()
        # 파일 경로를 바이트로 인코딩하여 전달
        mime.setData("application/x-image-path", QByteArray(self.image_path.encode("utf-8")))
        drag.setMimeData(mime)

        # 드래그 시 썸네일 미리보기
        pixmap = self._img_label.pixmap()
        if pixmap and not pixmap.isNull():
            scaled = pixmap.scaled(60, 60, Qt.AspectRatioMode.KeepAspectRatio)
            drag.setPixmap(scaled)

        drag.exec(Qt.DropAction.MoveAction)


class FolderTreeWidget(QTreeWidget):
    """폴더 트리 탐색 위젯"""

    folder_selected = Signal(str)  # 선택된 폴더 경로 전달

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHeaderLabel("폴더")
        self.setMinimumWidth(150)
        self.itemClicked.connect(self._on_item_clicked)

    def load_project(self, project_path: str):
        """프로젝트 폴더를 트리에 로드"""
        self.clear()
        if not project_path or not os.path.isdir(project_path):
            return
        root_item = QTreeWidgetItem(self, [os.path.basename(project_path)])
        root_item.setData(0, Qt.ItemDataRole.UserRole, project_path)
        self._add_children(root_item, project_path)
        root_item.setExpanded(True)
        self.setCurrentItem(root_item)

    def _add_children(self, parent_item: QTreeWidgetItem, directory: str):
        for subdir in list_subdirectories(directory):
            child = QTreeWidgetItem(parent_item, [os.path.basename(subdir)])
            child.setData(0, Qt.ItemDataRole.UserRole, subdir)
            self._add_children(child, subdir)

    def _on_item_clicked(self, item: QTreeWidgetItem, column: int):
        path = item.data(0, Qt.ItemDataRole.UserRole)
        if path:
            self.folder_selected.emit(path)


class StagingPanel(QWidget):
    """대기소 패널 - 오른쪽에 표시되는 분류 대기 이미지 패널"""

    # 이미지가 선별소로 이동될 때 발생하는 시그널 (이미지 경로, 현재 폴더 경로)
    image_moved_to_selected = Signal(str, str)

    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self._settings = settings
        self._current_project = None    # 현재 프로젝트 이름
        self._current_folder = None     # 현재 보고 있는 폴더 경로
        self._selected_images = set()   # 선택된 이미지 경로들
        self._thumbnails = {}           # 경로 → ThumbnailWidget 매핑
        self._build_ui()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(4, 4, 4, 4)

        # 헤더
        header = QLabel("🗂 대기소")
        header.setStyleSheet("font-size: 16px; font-weight: bold; padding: 4px;")
        main_layout.addWidget(header)

        # 프로젝트 선택 라벨
        self._project_label = QLabel("프로젝트: (없음)")
        self._project_label.setStyleSheet("color: #555; padding: 2px 4px;")
        main_layout.addWidget(self._project_label)

        # 분리자: 트리(왼쪽) + 이미지 그리드(오른쪽)
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # 폴더 트리
        self._folder_tree = FolderTreeWidget()
        self._folder_tree.folder_selected.connect(self._on_folder_selected)
        splitter.addWidget(self._folder_tree)

        # 이미지 그리드 영역
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)

        # 현재 폴더 경로 표시
        self._path_label = QLabel("")
        self._path_label.setStyleSheet("color: #777; font-size: 10px; padding: 2px;")
        right_layout.addWidget(self._path_label)

        # 이미지 그리드 스크롤 영역
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setAcceptDrops(False)
        self._grid_container = QWidget()
        self._grid_layout = QGridLayout(self._grid_container)
        self._grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        scroll.setWidget(self._grid_container)
        right_layout.addWidget(scroll)

        # 버튼 영역
        btn_layout = QHBoxLayout()
        self._select_all_btn = QPushButton("전체 선택")
        self._select_all_btn.clicked.connect(self._select_all)
        self._move_btn = QPushButton("선별소로 이동 →")
        self._move_btn.clicked.connect(self._move_selected)
        self._move_btn.setStyleSheet("background: #0078d4; color: white; font-weight: bold;")
        btn_layout.addWidget(self._select_all_btn)
        btn_layout.addWidget(self._move_btn)
        right_layout.addLayout(btn_layout)

        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)

        main_layout.addWidget(splitter)

    def load_project(self, project_name: str):
        """프로젝트를 로드하고 폴더 트리를 갱신"""
        self._current_project = project_name
        project_path = os.path.join(self._settings.staging_dir, project_name)
        self._project_label.setText(f"프로젝트: {project_name}")
        self._folder_tree.load_project(project_path)
        # 루트 폴더 이미지 표시
        self._current_folder = project_path
        self._refresh_grid()

    def refresh(self):
        """현재 폴더의 이미지 그리드 갱신"""
        self._refresh_grid()
        if self._current_project and self._current_folder:
            project_path = os.path.join(self._settings.staging_dir, self._current_project)
            self._folder_tree.load_project(project_path)

    def get_current_folder(self) -> str | None:
        """현재 보고 있는 폴더 경로 반환"""
        return self._current_folder

    def _on_folder_selected(self, folder_path: str):
        self._current_folder = folder_path
        self._refresh_grid()

    def _refresh_grid(self):
        """이미지 그리드 갱신"""
        # 기존 위젯 제거
        while self._grid_layout.count():
            item = self._grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._thumbnails.clear()
        self._selected_images.clear()

        if not self._current_folder or not os.path.isdir(self._current_folder):
            self._path_label.setText("")
            return

        self._path_label.setText(self._current_folder)
        images = list_images(self._current_folder)

        for idx, img_path in enumerate(images):
            thumb = ThumbnailWidget(img_path)
            thumb.clicked.connect(self._on_thumbnail_clicked)
            row, col = divmod(idx, GRID_COLUMNS)
            self._grid_layout.addWidget(thumb, row, col)
            self._thumbnails[img_path] = thumb

    def _on_thumbnail_clicked(self, image_path: str):
        """썸네일 클릭 시 선택/해제 토글"""
        if image_path in self._selected_images:
            self._selected_images.discard(image_path)
            self._thumbnails[image_path].set_selected(False)
        else:
            self._selected_images.add(image_path)
            self._thumbnails[image_path].set_selected(True)

    def _select_all(self):
        """현재 폴더의 모든 이미지 선택"""
        for path, thumb in self._thumbnails.items():
            self._selected_images.add(path)
            thumb.set_selected(True)

    def _move_selected(self):
        """선택된 이미지들을 선별소로 이동"""
        if not self._selected_images:
            QMessageBox.information(self, "알림", "이동할 이미지를 선택해주세요.")
            return
        for img_path in list(self._selected_images):
            self.image_moved_to_selected.emit(img_path, self._current_folder)
        self._refresh_grid()
