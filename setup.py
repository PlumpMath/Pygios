from setuptools import setup, find_packages

setup(
      name = "Pygios",
      version = "0.1",
      description = "A light-weight server monitoring system.",
      author = "Alice Bevan-McGregor",
      author_email = "alice@gothcandy.com",
      url = "http://github.com/GothAlice/Pygios",
      download_url = "http://pypi.python.org/pypi/Pygios",
      license = "MIT",
      packages = find_packages(exclude=['tests']),
      include_package_data = False,
      zip_safe = True,
      install_requires = ['CoScheduler', 'httplib2']
  )
