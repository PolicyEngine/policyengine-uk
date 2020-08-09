import csv
import os
from tqdm import tqdm
import numpy as np

class FRS:
    ''' 
    Helper class for using Family Resources Survey data.
    '''
    def __init__(self, dataset_path, output_path='datasets/frs'):
        '''
        Inputs:
            - dataset_path: path to the folder containing .tab files.
        '''
        self.dataset_path = dataset_path
        self.output_path = output_path
    
    def _reader(self, filename, limit=None):
        if limit is None:
            limit = -1
        with open(os.path.join(self.dataset_path, filename), 'r') as f:
            fieldnames = next(f).split('\t')
            reader = csv.DictReader(f, fieldnames=fieldnames, delimiter='\t')
            i = 0
            for row in reader:
                if i != limit:
                    yield row
                    i += 1
                else:
                    return row
    
    def generate_csv(self, limit=None):
        if limit is None:
            limit = -1
        fieldnames = ['person_id', '']
        with open(os.path.join(self.output_path, 'frs.csv'), 'w+') as f:

    
    def generate_income_csv(self, output_filename='income.csv'):
        with open(os.path.join(self.output_path, output_filename), 'w+') as f:
            writer = csv.DictWriter(f, fieldnames=['person_id', 'income'])
            writer.writeheader()
            skipped = 0
            i = 0
            for row in tqdm(self._reader('adult.tab'), desc='Generating CSV'):
                try:
                    estimated_yearly_income = float(row['INDINC']) * 52
                    if estimated_yearly_income < 0:
                        raise Exception('Income cannot be negative')
                    if estimated_yearly_income > 400000:
                        raise Exception('Suspicious...')
                    writer.writerow({'person_id': i, 'income': estimated_yearly_income })
                    i += 1
                except:
                    skipped += 1
        print(f'Completed, {skipped} rows skipped.')

if __name__ == '__main__':
    frs = FRS('datasets/frs/18_19')
    frs.generate_income_csv()