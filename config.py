import yaml


with open("config.yaml") as config_file:
    config = yaml.safe_load(config_file)
