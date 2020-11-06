env/bin/coverage run tests/test_phonomodel.py
env/bin/coverage run -a tests/test_sound.py
env/bin/coverage run -a tests/test_utils.py
env/bin/coverage html
firefox htmlcov/index.html
