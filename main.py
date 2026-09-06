"""
极限竞速地平线6 - 自动抽奖工具
主程序入口

功能说明：
- 基于OpenCV模板匹配的图像识别
- 支持自定义相似度阈值、扫描间隔、识别区域
- 完整的常规抽奖 + 最后一次专属收尾流程
- F1启动 / F2停止 热键控制
- 轻量化Tkinter图形界面

使用方法：
1. 安装依赖: pip install -r requirements.txt
2. 运行程序: python main.py
3. 或打包为EXE: pyinstaller --onefile --windowed main.py
"""

import sys
import os

# 将当前目录添加到系统路径（确保模块导入正确）
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def check_dependencies():
    """检查必要的依赖是否已安装"""
    required = {
        'opencv-python': 'cv2',
        'numpy': 'numpy',
        'PyAutoGUI': 'pyautogui',
        'Pillow': 'PIL',
        'pynput': 'pynput'
    }
    
    missing = []
    for package, module in required.items():
        try:
            __import__(module)
        except ImportError:
            missing.append(package)
    
    return missing


def main():
    """程序主入口"""
    print("=" * 60)
    print("  极限竞速地平线6 - 自动抽奖工具")
    print("  Horizon Raffle Bot v1.0")
    print("=" * 60)
    
    # 检查依赖
    missing_deps = check_dependencies()
    if missing_deps:
        print("\n[错误] 缺少以下依赖包:")
        for dep in missing_deps:
            print(f"  - {dep}")
        print("\n请运行以下命令安装:")
        print(f"  pip install {' '.join(missing_deps)}")
        print("\n或使用 requirements.txt:")
        print("  pip install -r requirements.txt")
        input("\n按回车键退出...")
        return
    
    # 启动GUI界面
    try:
        from gui import launch_gui
        launch_gui()
    except Exception as e:
        print(f"\n[严重错误] 程序启动失败: {e}")
        import traceback
        traceback.print_exc()
        input("\n按回车键退出...")


if __name__ == '__main__':
    main()
