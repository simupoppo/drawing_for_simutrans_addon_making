TARGET_SCRIPT = drawing_for_simutrans_addon_making.py
DIST_DIR = dist
WORK_DIR = work
PYINSTALLER_OPTS = --onefile --distpath $(DIST_DIR) --workpath $(WORK_DIR)

.PHONY: all build clean help

all: build

build:
	@echo "start building..."
	-@mkdir $(DIST_DIR) 2>nul || exit 0
	-@mkdir $(WORK_DIR) 2>nul || exit 0
	pyinstaller $(PYINSTALLER_OPTS) $(TARGET_SCRIPT)
	@echo "done"

clean:
	@echo "clean up..."
	-@rmdir /s /q $(WORK_DIR) 2>nul || exit 0
	-@rmdir /s /q $(DIST_DIR) 2>nul || exit 0
	-@del /q drawing_for_simutrans_addon_making.spec 2>nul || exit 0
	@echo "done"

help:
	@echo "help:"
	@echo "  make build  - exeを作成します"
	@echo "  make clean  - 生成されたディレクトリとspecファイルを削除します"