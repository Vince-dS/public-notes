import argparse
import gzip
import tarfile
import time
from datetime import datetime
from elasticsearch import Elasticsearch, helpers


def parse_arguments():
    parser = argparse.ArgumentParser(description='Elasticsearch Timestamp Loader')
    parser.add_argument('--host', required=True, help='Elasticsearch host')
    parser.add_argument('--user', required=True, help='Elasticsearch user')
    parser.add_argument('--password', required=True, help='Elasticsearch password')
    parser.add_argument('--input', required=True, help='Input file (tar.gz or gzip)')
    parser.add_argument('--batch-size', type=int, default=1000, help='Batch size for bulk insert')
    parser.add_argument('--current-date', required=True, help='Current date for reference')
    parser.add_argument('--patterns', nargs='*', help='Patterns to filter data')
    return parser.parse_args()


def transform_timestamps(data, reference_date):
    transformed_data = []
    reference_timestamp = datetime.strptime(reference_date, '%Y-%m-%d %H:%M:%S').timestamp()
    for item in data:
        timestamp = item.get('timestamp')  # Assuming 'timestamp' is a key in the item
        if timestamp:
            new_timestamp = reference_timestamp + (timestamp - reference_timestamp)  # Example transformation
            item['timestamp'] = new_timestamp
            transformed_data.append(item)
    return transformed_data


def load_data(es, index_name, data):
    # Bulk insert into Elasticsearch
    for success, info in helpers.parallel_bulk(es, data):
        if not success:
            print(f'Failed to index document {info}')


def process_file(input_file):
    if input_file.endswith('.tar.gz'):
        with tarfile.open(input_file, 'r:gz') as tar:
            return [json.loads(tar.extractfile(member).read()) for member in tar.getmembers()]
    elif input_file.endswith('.gz'):
        with gzip.open(input_file, 'rt') as gz:
            return [json.loads(line) for line in gz]
    else:
        raise ValueError('Unsupported file format: must be tar.gz or gzip')


def main():
    args = parse_arguments()
    es = Elasticsearch([args.host], http_auth=(args.user, args.password))

    raw_data = process_file(args.input)
    transformed_data = transform_timestamps(raw_data, args.current_date)
    load_data(es, 'my_index', transformed_data)  # Replace 'my_index' with your actual index name

if __name__ == '__main__':
    main()
