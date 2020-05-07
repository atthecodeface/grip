test_all: test_lib test_grip

.PHONY:test_lib
test_lib:
	./test_lib.py


.PHONY:test_grip
test_grip:
	./test_grip.py

.PHONY:check_types
check_types:
	mypy lib/*/*py lib/*.py
