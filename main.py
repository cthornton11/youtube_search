
import yaml
import findvideo as vidfinder
import argparse

parser = argparse.ArgumentParser(description='Defining search parameters')
parser.add_argument('keywords', type=str, nargs='+')
parser.add_argument('--time', type=int, default=10) # days 
args = parser.parse_args()


def load_yaml(filepath):
    with open(filepath, 'r') as path:
        try:
            return yaml.safe_load(path)
        except yaml.YAMLError as err:
            print(err)

# get api key from config
config = load_yaml('./config.yaml')

if __name__ == "__main__":
    start_date = vidfinder.get_start_date(args.time)
    vidfinder.search_each_term(args.keywords, config['api'],
                        start_date)