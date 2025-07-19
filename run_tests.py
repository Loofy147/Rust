import sys
import unittest

# Add the project root to the Python path
sys.path.insert(0, '.')

# Discover and run the tests
suite = unittest.defaultTestLoader.discover('/app/multi_agent_framework/tests')
runner = unittest.TextTestRunner()
runner.run(suite)
