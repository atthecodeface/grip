test_all: test_lib test_grip

.PHONY:test_lib
test_lib:
	./test_lib.py


.PHONY:test_grip
test_grip:
	./test_grip.py

PYTHON_SRCS =
PYTHON_SRCS += lib/*/*py
PYTHON_SRCS += lib/*.py
PYTHON_SRCS += cmds/*.py
PYTHON_SRCS += grip

.PHONY:check_types
check_types:
	mypy ${PYTHON_SRCS}

.PHONY:check_types_strict
check_types_strict:
	mypy --strict ${PYTHON_SRCS}

.PHONY:check_types_stubgen
check_types_stubgen:
	stubgen lib/*/*py lib/*.py

.PHONY:check_types_with_stubs
check_types_with_stubs:
	MYPYPATH=$(CURDIR)/lib/mypy_stubs mypy lib/workflow/*py

