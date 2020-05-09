GRIP_DIR=$(abspath $(CURDIR))

TESTS_DIR = ${GRIP_DIR}/test

TESTS_PYTHONPATH = ${GRIP_DIR}:${PYTHONPATH}
TESTS_ENV = PYTHONPATH=${TESTS_PYTHONPATH} GRIP_DIR=${GRIP_DIR}
test_all: check_types_strict test_grip

.PHONY:test_lib
test_lib:
	${TESTS_ENV} ${TESTS_DIR}/test_lib.py


.PHONY:test_grip
test_grip:
	(cd ${TESTS_DIR} && ${TESTS_ENV} python3 -m test.test_grip)

PYTHON_SRCS =
PYTHON_SRCS += ${GRIP_DIR}/lib/*/*py
PYTHON_SRCS += ${GRIP_DIR}/lib/*.py
PYTHON_SRCS += ${GRIP_DIR}/cmds/*.py
PYTHON_SRCS += ${GRIP_DIR}/grip
PYTHON_SRCS += ${GRIP_DIR}/test/test_lib/*py
PYTHON_SRCS += ${GRIP_DIR}/test/test_grip.py

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

