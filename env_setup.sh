if ! [ -d ".env" ]; then
  virtualenv -p python3 .env
fi

# activate environment
source .env/bin/activate

# install external packages
pip install -r env_packages.txt

# uninstall home made packages
pip uninstall -y src

# build the setup wheel
python setup.py bdist_wheel

python -m pip install src --ignore-installed --find-links=dist/
