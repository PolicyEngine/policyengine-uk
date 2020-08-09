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
        fieldnames = [
            'person_id',
            'earnings',
            'jsa',
            'income_support',
            'housing_benefit',
            'child_benefit',
            'child_tax_credit',
            'working_tax_credit_childcare',
            'tax_free_childcare',
            'working_tax_credit'
        ]
        data = {}
        for row in tqdm(self._reader('adult.tab'), desc='Reading adult.tab'):
            identifier = row['sernum'] + 'p' + row['PERSON']
            data[identifier] = {
                'earnings': np.round(float(row['INEARNS']) * 30 / 7, 2)
            }
        benefit_name = {
            '14': 'jsa',
            '19': 'income_support',
            '94': 'housing_benefit',
            '3': 'child_benefit',
            '106': 'child_tax_credit',
            '105': 'working_tax_credit'
        }
        skipped = 0
        for row in tqdm(self._reader('benefits.tab'), desc='Reading benefits.tab'):
            identifier = row['sernum'] + 'p' + row['PERSON']
            if row['BENEFIT'] in benefit_name:
                benefit = benefit_name[row['BENEFIT']]
                amount = row['BENAMT']
                try:
                    data[identifier][benefit] = np.round(float(amount) * 30 / 7, 2)
                except:
                    skipped += 1
        print(f'Completed, skipped {skipped} rows of benefits.tab.')
        for person in tqdm(data.values(), desc='Zeroing missing values'):
            for name in fieldnames:
                if name not in person:
                    person[name] = 0
        with open(os.path.join(self.output_path, 'frs.csv'), 'w+') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for key, value in tqdm(data.items(), desc='Writing data'):
                row = value
                row['person_id'] = key
                writer.writerow(row)

if __name__ == '__main__':
    frs = FRS('datasets/frs/18_19')
    frs.generate_csv()