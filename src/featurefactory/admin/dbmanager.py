import codecs
import csv

import mysql.connector
import numpy as np
import pandas as pd
# from sklearn import *

import orm


'''
TODO:
-create a feature that works.
-attach classification methods to the feature, and get that part of the pipeline built.
-be able to retrieve features from the database.
-fix up the datatypes for the dataframe
-have a solid configuration for datatypes, so users dont get confused
'''


class DatabaseManager(object):

    def __init__(self, database):
        self.cnx = mysql.connector.connect(user='root', password='', database=database)
        self.cursor = self.cnx.cursor()
        self.database = database

    def change_db(self, database):
        command = 'USE {};'.format(database)
        try:
            self.cursor.execute(command)
        except Exception as e:
            print(e.message)

    def get_column_names(self, table):
        command = 'SHOW COLUMNS FROM {};'.format(table)
        self.cursor.execute(command)
        names = []
        for row in self.cursor:
            names.append(row[0])
        return names

    def insert_dataset(self, table, fn):
        fields = self.get_column_names(table)[1:]    # ignore internal db id
        failed_inserts = 0
        with open(fn, 'rU') as csvfile:
            deencoded = codecs.iterencode(codecs.iterdecode(csvfile, 'ISO-8859-1'), 'ISO-8859-1')
            reader = csv.reader(deencoded)
            first_row = True
            for row in reader:
                if not first_row:
                    try:
                        self.insert_row(table, fields, [x.decode('ISO-8859-1') for x in row])
                    except Exception as e:
                        print(e)
                        failed_inserts += 1
                else:
                    first_row = False

        print("There were " + str(failed_inserts) + " rows that failed to be inserted")

    def insert_row(self, table, fields, values):
        val_str = ",".join(['%s' for elem in values])
        command = 'INSERT INTO ' + table + ' ( ' + ','.join(fields) + ') VALUES (' + val_str + ')'
        self.cursor.execute(command, values)
        self.cnx.commit()

    def retrieve_dataset(self, table, columns=None, num_rows=None, form='numpy'):
        if columns:
            command = 'SELECT {} FROM {}'.format(','.join(columns), table)
        else:
            command = 'SELECT * FROM {}'.format(table)

        if num_rows:
            command += ' LIMIT {}'.format(num_rows)

        self.cursor.execute(command + ';')

        result = np.matrix([list(row) for row in self.cursor])

        if form == 'numpy':
            return result

        elif form == 'pandas':
            result = np.transpose(result)
            if not columns:
                columns = self.get_column_names(table)

            tmp = {}
            for i in range(len(columns)):
                tmp[columns[i]] = result[i, :].flatten().tolist()[0]

            return pd.DataFrame(tmp)

        else:
            raise ValueError('data form not recognized. the two available forms are pandas and numpy')

    def execute(self, command, values=None):
        self.cursor.execute(command, values)
        return [list(row) for row in self.cursor]
