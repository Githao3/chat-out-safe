import argparse
import ctypes
import os
import random
import sys
import time

import numpy as np
import pyautogui
import win32con
import win32gui
from PIL import Image, ImageGrab


def set_dpi_awareness():
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass


def find_qq_window():
    hwnd = win32gui.FindWindow(None, "QQ")
    if not hwnd:
        print("[错误] 未找到QQ窗口，请先打开QQ并进入目标聊天窗口。")
        sys.exit(1)
    return hwnd


def get_window_rect(hwnd):
    rect = win32gui.GetWindowRect(hwnd)
    left, top, right, bottom = rect
    return left, top, right, bottom


def bring_window_to_front(hwnd):
    try:
        shell = ctypes.windll.user32
        shell.SetForegroundWindow(hwnd)
    except Exception:
        pass
    time.sleep(0.3)


def calc_chat_region(window_rect, offset_left=260, offset_top=110, offset_bottom=80):
    left, top, right, bottom = window_rect
    chat_left = left + offset_left
    chat_top = top + offset_top
    chat_right = right
    chat_bottom = bottom - offset_bottom
    return (chat_left, chat_top, chat_right, chat_bottom)


def capture_region(region):
    img = ImageGrab.grab(bbox=region)
    return img


def human_like_pause(min_sec=0.3, max_sec=1.5):
    time.sleep(random.uniform(min_sec, max_sec))


def scroll_down_in_region(region, scroll_amount=50):
    cx = (region[0] + region[2]) // 2
    cy = (region[1] + region[3]) // 2

    click_x = cx + random.randint(-50, 50)
    click_y = cy + random.randint(-80, 80)
    pyautogui.moveTo(click_x, click_y, duration=random.uniform(0.2, 0.5))
    human_like_pause(0.3, 0.8)
    pyautogui.click()
    human_like_pause(0.2, 0.5)

    scroll_count = random.randint(6, 10)
    for i in range(scroll_count):
        if random.random() < 0.15 and i > 1:
            pyautogui.scroll(random.randint(10, 30))
            human_like_pause(0.4, 0.8)

        actual_scroll = scroll_amount + random.randint(-15, 15)
        pyautogui.scroll(-actual_scroll)

        if random.random() < 0.2 and i < scroll_count - 1:
            human_like_pause(0.5, 1.0)
        elif i < scroll_count - 1:
            human_like_pause(0.15, 0.4)

    human_like_pause(0.5, 1.0)


def images_are_similar(img1, img2, threshold=0.98):
    if img1.size != img2.size:
        return False
    arr1 = np.array(img1.convert("RGB"), dtype=np.float32)
    arr2 = np.array(img2.convert("RGB"), dtype=np.float32)
    diff = np.abs(arr1 - arr2)
    similar_pixels = np.sum(diff < 10) / diff.size
    return similar_pixels >= threshold


def scroll_to_top(region, scroll_amount=50, max_attempts=50):
    print("[信息] 正在滚动到聊天顶部（最早的消息）...")
    prev_img = capture_region(region)
    no_change_count = 0
    cx = (region[0] + region[2]) // 2
    cy = (region[1] + region[3]) // 2
    for i in range(max_attempts):
        click_x = cx + random.randint(-50, 50)
        click_y = cy + random.randint(-80, 80)
        pyautogui.moveTo(click_x, click_y, duration=random.uniform(0.2, 0.5))
        human_like_pause(0.3, 0.8)

        scroll_count = random.randint(6, 10)
        for j in range(scroll_count):
            if random.random() < 0.15 and j > 1:
                pyautogui.scroll(-random.randint(10, 30))
                human_like_pause(0.4, 0.8)

            actual_scroll = scroll_amount + random.randint(-15, 15)
            pyautogui.scroll(actual_scroll)

            if random.random() < 0.2 and j < scroll_count - 1:
                human_like_pause(0.5, 1.0)
            elif j < scroll_count - 1:
                human_like_pause(0.15, 0.4)

        human_like_pause(0.6, 1.5)
        curr_img = capture_region(region)
        if images_are_similar(prev_img, curr_img, threshold=0.98):
            no_change_count += 1
            if no_change_count >= 2:
                print(f"[信息] 已到达聊天顶部（共向上滚动 {i + 1} 次）")
                return
        else:
            no_change_count = 0
        prev_img = curr_img
    print(f"[警告] 已达到最大上滚次数 {max_attempts}，可能未到顶部。继续截取...")


def save_screenshot(img, output_dir, page_number):
    filename = f"page_{page_number:03d}.png"
    filepath = os.path.join(output_dir, filename)
    img.save(filepath)
    print(f"  [截取] {filename}")
    return filepath


def main():
    parser = argparse.ArgumentParser(description="QQ聊天记录自动化截屏工具")
    parser.add_argument("--output-dir", type=str, default="./output_qq", help="截图输出目录（默认: ./output_qq）")
    parser.add_argument("--scroll-amount", type=int, default=200, help="每次滚动量（默认: 200）")
    parser.add_argument("--scroll-delay", type=float, default=1.5, help="滚动后等待时间/秒（默认: 1.5）")
    parser.add_argument("--similarity-threshold", type=float, default=0.98, help="重复检测相似度阈值（默认: 0.98）")
    parser.add_argument("--max-pages", type=int, default=1000, help="最大截取页数（默认: 1000）")
    parser.add_argument("--offset-left", type=int, default=260, help="聊天区域左侧偏移像素（默认: 260）")
    parser.add_argument("--offset-top", type=int, default=110, help="聊天区域顶部偏移像素（默认: 110）")
    parser.add_argument("--offset-bottom", type=int, default=80, help="聊天区域底部偏移像素（默认: 80）")
    parser.add_argument("--scroll-top", action="store_true", help="自动滚动到聊天顶部后再开始截取（默认从当前位置开始）")
    args = parser.parse_args()

    set_dpi_awareness()

    pyautogui.FAILSAFE = True
    pyautogui.PAUSE = 0.1

    print("=" * 50)
    print("  QQ聊天记录自动化截屏工具")
    print("=" * 50)

    hwnd = find_qq_window()
    window_rect = get_window_rect(hwnd)
    print(f"[信息] 找到QQ窗口: 位置({window_rect[0]}, {window_rect[1]}) "
          f"大小({window_rect[2] - window_rect[0]}x{window_rect[3] - window_rect[1]})")

    chat_region = calc_chat_region(window_rect, args.offset_left, args.offset_top, args.offset_bottom)
    chat_w = chat_region[2] - chat_region[0]
    chat_h = chat_region[3] - chat_region[1]
    print(f"[信息] 聊天消息区域: 位置({chat_region[0]}, {chat_region[1]}) 大小({chat_w}x{chat_h})")

    os.makedirs(args.output_dir, exist_ok=True)
    print(f"[信息] 截图将保存到: {os.path.abspath(args.output_dir)}")

    bring_window_to_front(hwnd)

    print("\n[提示] 程序将在 3 秒后开始，请确保QQ窗口已打开并定位到目标聊天...")
    for i in range(3, 0, -1):
        print(f"  {i}...")
        time.sleep(1)

    if args.scroll_top:
        scroll_to_top(chat_region, scroll_amount=args.scroll_amount, max_attempts=80)
        time.sleep(0.5)

    print(f"\n[信息] 开始逐屏截取（从当前位置往下）...")
    print(f"[信息] 最大截取 {args.max_pages} 页，相似度阈值 {args.similarity_threshold}")
    print("-" * 50)

    page_number = 0
    prev_img = None
    no_change_count = 0

    try:
        while page_number < args.max_pages:
            curr_img = capture_region(chat_region)

            if prev_img is not None and images_are_similar(prev_img, curr_img, args.similarity_threshold):
                no_change_count += 1
                if no_change_count >= 2:
                    print(f"\n[信息] 连续 {no_change_count} 次检测到页面未变化，已到达聊天底部。")
                    break
                else:
                    print(f"  [警告] 第 {page_number + 1} 屏检测到相似，再滚动一次确认...")
                    scroll_down_in_region(chat_region, args.scroll_amount)
                    time.sleep(random.uniform(args.scroll_delay * 0.6, args.scroll_delay * 1.8))
                    continue
            else:
                no_change_count = 0

            page_number += 1
            save_screenshot(curr_img, args.output_dir, page_number)
            prev_img = curr_img

            if page_number < args.max_pages:
                scroll_down_in_region(chat_region, args.scroll_amount)
                time.sleep(random.uniform(args.scroll_delay * 0.6, args.scroll_delay * 1.8))

    except KeyboardInterrupt:
        print(f"\n\n[中断] 用户手动中断（Ctrl+C），已截取的图片已保存。")

    print("-" * 50)
    print(f"[完成] 共截取 {page_number} 张截图，保存在: {os.path.abspath(args.output_dir)}")
    print("=" * 50)


if __name__ == "__main__":
    main()
