#
# Copyright (C) 2018-present, iQIYI, Inc. All rights reserved.
#
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and
# associated documentation files (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or substantial
# portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT
# LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#



SOURCE_DIR = src

MANIFEST_FILE = etc/manifest.txt

DEX_JAR = dx.jar

SOURCE_FILE = srcfile

CLASS_DIR = class_src

ORIGIN_DEX_JAR = origin.dx.jar

build:
	@find . -name "*.java" > $(SOURCE_FILE)
	@javac -d class_src -cp $(CLASSPATH) \@$(SOURCE_FILE)
	@jar cvfm $(DEX_JAR) $(MANIFEST_FILE) -C $(CLASS_DIR) .
	@cp $(DEX_PATH)/$(DEX_JAR) $(DEX_PATH)/$(ORIGIN_DEX_JAR)
	@cp $(DEX_JAR) $(DEX_PATH)/$(DEX_JAR)