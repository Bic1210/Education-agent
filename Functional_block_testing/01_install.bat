@echo off
chcp 65001 >nul
echo ========================================
echo  AI 知识图谱平台 — 依赖安装脚本
echo  仅首次运行需要执行
echo ========================================
echo.

:: ── 检查 Python ──────────────────────────────────────────────
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 Python，请先安装 Python 3.9+(推荐3.10)
    echo        下载地址：https://www.python.org/downloads/
    pause
    exit /b 1
)
echo [OK] Python 检测通过

:: ── 后端依赖（必须）────────────────────────────────────────────
echo.
echo [1/3] 安装后端核心依赖...
pip install flask flask-cors pymupdf pillow numpy tqdm -i https://pypi.tuna.tsinghua.edu.cn/simple
if errorlevel 1 (
    echo [警告] 部分依赖安装失败，请检查网络后重试
)

:: ── OCR 依赖（可选，处理扫描版PDF时需要）──────────────────────
echo.
echo [2/3] 安装 OCR 依赖（PaddlePaddle + PaddleOCR）...
echo       如果不需要处理扫描版PDF，可跳过此步骤
echo       正在检测 CUDA 是否可用...

:: 优先安装 GPU 版本，失败则回退 CPU 版本
pip install paddlepaddle-gpu -i https://pypi.tuna.tsinghua.edu.cn/simple 2>nul
if errorlevel 1 (
    echo [提示] GPU 版安装失败，改为安装 CPU 版...
    pip install paddlepaddle -i https://pypi.tuna.tsinghua.edu.cn/simple
)pip install paddleocr -i https://pypi.tuna.tsinghua.edu.cn/simple

:: ── 前端依赖 ──────────────────────────────────────────────────
echo.
echo [3/3] 安装前端依赖（Node.js + npm）...
where node >nul 2>&1
if errorlevel 1 (
    echo [跳过] 未检测到 Node.js，如需使用网页界面请先安装 Node.js 18+
    echo        下载地址：https://nodejs.org/
) else (
    echo [OK] Node.js 检测通过，安装前端依赖...
    cd knowledge-platform
    npm install
    cd ..
)

:: ── 创建必要目录 ──────────────────────────────────────────────
echo.
echo 创建工作目录...
if not exist "input_pdfs"    mkdir input_pdfs
if not exist "output_txts"   mkdir output_txts
if not exist "corpus"        mkdir corpus
if not exist "data\uploads"  mkdir data\uploads
if not exist "data\output_txts" mkdir data\output_txts
if not exist "data\corpus"   mkdir data\corpus
if not exist "data\graphs"   mkdir data\graphs

:: ── 完成 ──────────────────────────────────────────────────────
echo.
echo ========================================
echo  安装完成！使用方式：
echo.
echo  方式一：网页界面
echo    终端1: python server.py
echo    终端2: cd knowledge-platform ^&^& npm run dev
echo    访问:  http://localhost:5173
echo.
echo  方式二：离线脚本
echo    1. 把 PDF 放入 input_pdfs/
echo    2. python Functional_block_testing\02_run_ocr_v5.py
echo    3. python Functional_block_testing\03_parse_and_build_corpus_v5.py
echo ========================================
pause
