GRIP_DIR=$(abspath $(CURDIR))

TESTS_DIR = ${GRIP_DIR}/test

TESTS_LOG_DIR = ${GRIP_DIR}/test/logs

TESTS_PYTHONPATH = ${GRIP_DIR}:${PYTHONPATH}
TESTS_ENV = PYTHONPATH=${TESTS_PYTHONPATH} GRIP_DIR=${GRIP_DIR} TESTS_LOG_DIR=${TESTS_LOG_DIR}
all: check_types test_all

.PHONY:test_lib
test_lib:
	${TESTS_ENV} ${TESTS_DIR}/test_lib.py


.PHONY:test_all
test_all:
	mkdir -p ${TESTS_LOG_DIR}
	(cd ${TESTS_DIR} && ${TESTS_ENV} python3 -m test.test_all -v)

PYTHON_SRCS =
PYTHON_SRCS += ${GRIP_DIR}/lib/*/*py
PYTHON_SRCS += ${GRIP_DIR}/lib/*.py
PYTHON_SRCS += ${GRIP_DIR}/cmds/*.py
PYTHON_SRCS += ${GRIP_DIR}/grip
PYTHON_SRCS += ${GRIP_DIR}/test/test_lib/*py
PYTHON_SRCS += ${GRIP_DIR}/test/test_all.py
PYTHON_SRCS += ${GRIP_DIR}/test/test_grip.py
PYTHON_SRCS += ${GRIP_DIR}/test/test_git.py
PYTHON_SRCS += ${GRIP_DIR}/test/test_state_file.py

.PHONY:check_types_loose
check_types_loose:
	mypy ${PYTHON_SRCS}

.PHONY:check_types
check_types:
	mypy --strict ${PYTHON_SRCS}

