coverage run tests/test_phonomodel.py
REM env/bin/coverage run -a tests/test_regressors.py
coverage run -a tests/test_sound.py
coverage run -a tests/test_segment.py
coverage run -a tests/test_sequence.py
coverage run -a tests/test_utils.py
coverage html
start htmlcov/index.html
