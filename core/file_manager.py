"""파일 이동/삭제/관리 로직"""

import os
import shutil

# 지원하는 이미지 확장자
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".tiff", ".tif"}


def is_image(path: str) -> bool:
    """파일이 이미지인지 확인"""
    _, ext = os.path.splitext(path)
    return ext.lower() in IMAGE_EXTENSIONS


def move_file(src: str, dst: str):
    """파일을 src에서 dst로 이동 (잘라내기)"""
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.move(src, dst)


def move_directory_contents(src_dir: str, dst_dir: str):
    """src_dir 안의 모든 파일과 폴더를 dst_dir로 이동 (잘라내기)"""
    if not os.path.isdir(src_dir):
        raise NotADirectoryError(f"소스 경로가 디렉토리가 아닙니다: {src_dir}")
    os.makedirs(dst_dir, exist_ok=True)
    for item in os.listdir(src_dir):
        src_item = os.path.join(src_dir, item)
        dst_item = os.path.join(dst_dir, item)
        shutil.move(src_item, dst_item)


def delete_directory_contents(directory: str):
    """디렉토리 안의 모든 내용을 삭제 (디렉토리 자체는 유지)"""
    if not os.path.isdir(directory):
        return
    for item in os.listdir(directory):
        item_path = os.path.join(directory, item)
        if os.path.isfile(item_path) or os.path.islink(item_path):
            os.unlink(item_path)
        elif os.path.isdir(item_path):
            shutil.rmtree(item_path)


def list_images(directory: str) -> list[str]:
    """디렉토리에서 이미지 파일 목록 반환 (재귀 탐색 없이 현재 폴더만)"""
    if not os.path.isdir(directory):
        return []
    result = []
    for item in sorted(os.listdir(directory)):
        item_path = os.path.join(directory, item)
        if os.path.isfile(item_path) and is_image(item_path):
            result.append(item_path)
    return result


def list_subdirectories(directory: str) -> list[str]:
    """디렉토리 안의 하위 폴더 목록 반환"""
    if not os.path.isdir(directory):
        return []
    result = []
    for item in sorted(os.listdir(directory)):
        item_path = os.path.join(directory, item)
        if os.path.isdir(item_path):
            result.append(item_path)
    return result
